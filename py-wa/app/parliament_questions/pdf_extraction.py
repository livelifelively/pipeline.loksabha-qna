from pathlib import Path
from typing import Any, Dict

from ..pipeline.context import PipelineContext
from ..utils.gemini_api import extract_text_from_pdf, init_gemini

# Initialize Gemini model
model = init_gemini()


async def extract_pdf_contents(question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract contents from a question PDF using Gemini API.

    Args:
        question_data: Dictionary containing question information

    Returns:
        Dictionary with extracted question and answer text
    """
    pdf_path = Path(question_data["questions_file_path_local"])

    try:
        # Extract text using Gemini API
        extracted_text = await extract_text_from_pdf(model, pdf_path)

        return {
            **question_data,
            "question_text": extracted_text["question_text"],
            "answer_text": extracted_text["answer_text"],
        }

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

    context.log_step("extraction_start", total_questions=len(downloaded_questions))

    processed_questions = []
    failed_extractions = []

    for i, question in enumerate(downloaded_questions):
        try:
            # Check if PDF file exists
            pdf_path = Path(question["questions_file_path_local"])
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            # Extract contents
            result = await extract_pdf_contents(question)
            processed_questions.append(result)

            context.log_step(
                "question_extracted",
                question_number=question["question_number"],
                progress=f"{i+1}/{len(downloaded_questions)}",
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
