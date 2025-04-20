import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import camelot

from ..pipeline.context import PipelineContext
from ..utils.gemini_api import extract_text_from_pdf
from ..utils.project_root import find_project_root

# Initialize Gemini model
# model = init_gemini()


async def extract_tables_from_pdf(pdf_path: Path) -> List[Dict]:
    """
    Extract tables from PDF using Camelot with lattice method.
    Falls back to stream if no tables found.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of tables with their data and parsing reports
    """
    try:
        # Try lattice first (for tables with borders)
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice")

        extracted_tables = []

        for i, table in enumerate(tables):
            # Convert DataFrame to dict
            df = table.df
            headers = df.iloc[0].tolist()
            rows = [dict(zip(headers, row.tolist())) for _, row in df.iloc[1:].iterrows()]

            # Combine table data and parsing report
            table_data = {
                "table_number": i + 1,
                "page": table.page,
                "headers": headers,
                "rows": rows,
                "accuracy": table.accuracy,
                **table.parsing_report,
            }
            extracted_tables.append(table_data)

        return extracted_tables

    except Exception as e:
        raise Exception(f"Failed to extract tables from PDF: {str(e)}") from e


async def save_file_safely(content: Any, file_path: Path, is_json: bool = False) -> None:
    """Safely save content to a file using a temporary file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
        if is_json:
            json.dump(content, temp_file, indent=2, ensure_ascii=False)
        else:
            temp_file.write(content)

    shutil.move(temp_file.name, file_path)


def create_table_summary(tables: List[Dict]) -> Dict[str, Any]:
    """Create summary of extracted tables."""
    return {
        "has_tables": len(tables) > 0,
        "num_tables": len(tables),
        "tables_data": {
            "tables_summary": [
                {
                    "table_number": table["table_number"],
                    "page": table["page"],
                    "accuracy": table["accuracy"],
                    "num_rows": len(table["rows"]),
                    "num_columns": len(table["headers"]),
                }
                for table in tables
            ]
            if tables
            else []
        },
    }


def update_progress_step(progress_data: Dict[str, Any], step_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update progress data with new step information."""
    if "steps" not in progress_data:
        progress_data["steps"] = []

    # Remove existing step if present
    progress_data["steps"] = [step for step in progress_data["steps"] if step.get("step") != "pdf_extraction"]

    # Add new step
    progress_data["steps"].append(step_data)
    return progress_data


def create_extraction_step(text_path: Path, tables_path: Path, tables: List[Dict]) -> Dict[str, Any]:
    """Create extraction step data."""
    return {
        "step": "pdf_extraction",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "data": {
            "extracted_text_path": str(text_path.name),
            "tables_path": str(tables_path.name),
            **create_table_summary(tables),
        },
    }


def create_failure_step(error: Exception) -> Dict[str, Any]:
    """Create failure step data."""
    return {
        "step": "pdf_extraction",
        "timestamp": datetime.utcnow().isoformat(),
        "status": "failed",
        "error": str(error),
    }


async def extract_pdf_contents(pdf_path: Path, extractor_type: str = "marker") -> str:
    """
    Extract both text and tables from a PDF file and update progress.json.

    Args:
        pdf_path: Path to the PDF file
        extractor_type: Type of text extractor to use

    Returns:
        Extracted text in markdown format
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF: {pdf_path}")

    progress_path = pdf_path.parent / "progress.json"
    text_path = pdf_path.parent / "extracted_text.md"
    tables_path = pdf_path.parent / "extracted_tables.json"

    try:
        # Load existing progress
        with open(progress_path, "r", encoding="utf-8") as f:
            progress_data = json.load(f)

        # Extract and save text
        extracted_text = await extract_text_from_pdf(pdf_path, extractor_type)
        await save_file_safely(extracted_text, text_path)

        # Extract and save tables
        tables = await extract_tables_from_pdf(pdf_path)
        await save_file_safely(tables, tables_path, is_json=True)

        # Update and save progress
        step_data = create_extraction_step(text_path, tables_path, tables)
        updated_progress = update_progress_step(progress_data, step_data)
        await save_file_safely(updated_progress, progress_path, is_json=True)

        return updated_progress

    except Exception as e:
        try:
            # Record failure in progress.json
            step_data = create_failure_step(e)
            updated_progress = update_progress_step(progress_data, step_data)
            await save_file_safely(updated_progress, progress_path, is_json=True)
        except (IOError, json.JSONDecodeError):
            pass  # Don't let progress recording failure mask the original error

        raise Exception(f"Failed to extract PDF contents: {str(e)}") from e


async def batch_pdf_extraction(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Process PDFs for all downloaded questions through Gemini API.

    Args:
        outputs: Pipeline outputs containing downloaded questions
        context: Pipeline context for logging

    Returns:
        Dict containing extraction results
    """
    downloaded_questions = outputs.get("downloaded_sansad_session_questions", [])
    project_root = find_project_root()

    context.log_step("extraction_start", total_questions=len(downloaded_questions))

    processed_questions = []
    failed_extractions = []

    for i, question in enumerate(downloaded_questions):
        try:
            # Check if PDF file exists using absolute path
            pdf_path = Path(project_root) / question["questions_file_path_local"]
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # Extract contents
            result = await extract_pdf_contents(pdf_path)
            processed_questions.append(result)

            context.log_step(
                "question_extracted",
                question_number=question["question_number"],
                progress=f"{i + 1}/{len(downloaded_questions)}",
            )

        except Exception as e:
            failed_extractions.append({"question": question, "error": str(e)})
            context.log_step("extraction_failed", question_number=question["question_number"], error=str(e))

    status = "SUCCESS" if not failed_extractions else "PARTIAL"

    context.log_step(
        "extraction_complete",
        status=status,
        total_processed=len(processed_questions),
        total_failed=len(failed_extractions),
    )

    return {"status": status, "extracted_questions": processed_questions, "failed_extractions": failed_extractions}
