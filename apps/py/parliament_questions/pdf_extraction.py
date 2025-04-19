from pathlib import Path
from typing import Any, Dict

from ..pipeline.context import PipelineContext
from ..utils.gemini_api import extract_text_from_pdf
from ..utils.project_root import find_project_root

# Initialize Gemini model
# model = init_gemini()


async def extract_pdf_contents(pdf_path: Path, extractor_type: str = "marker") -> str:
    """
    Extract contents from a question PDF using Marker.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text in markdown format
    """

    try:
        # Extract text using Marker
        extracted_text = await extract_text_from_pdf(pdf_path, extractor_type)

        # Save extracted text to markdown file
        output_path = pdf_path.parent / "extracted_text.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        return extracted_text

    except Exception as e:
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
