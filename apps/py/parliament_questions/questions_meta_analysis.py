import logging
from typing import Any, Dict

from ..pipeline.context import PipelineContext
from .types import ParliamentQuestion

logger = logging.getLogger(__name__)


async def analyze_questions_batch_metadata(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Fetch meta analysis for downloaded question PDFs.

    Args:
        outputs: Pipeline outputs containing downloaded questions
        context: Pipeline context for logging

    Returns:
        Dict containing analysis status and results
    """
    downloaded_questions = outputs.get("downloaded_sansad_session_questions", [])

    context.log_step("analysis_start", total_questions=len(downloaded_questions))

    try:
        analyzed_data = []
        failed_analysis = []

        for i, question in enumerate(downloaded_questions):
            try:
                analysis = await analyze_question_metadata(question)
                analyzed_data.append(analysis)

                context.log_step(
                    "question_analyzed",
                    question_id=question["question_number"],
                    progress=f"{i+1}/{len(downloaded_questions)}",
                )

            except Exception as e:
                failed_analysis.append({"question": question, "error": str(e)})
                context.log_step("question_analysis_failed", question_id=question["question_number"], error=str(e))

        status = "SUCCESS" if not failed_analysis else "PARTIAL"

        return {
            "status": status,
            "cleaned_question_answer_data": analyzed_data,
            "failed_analysis": failed_analysis,
        }

    except Exception as e:
        context.log_step("analysis_failed", error=str(e))
        return {"status": "FAILURE", "error": str(e)}

    # TODO: Implement additional meta-analysis features:
    # - Number of pages
    # - Has table detection
    # - Answer length analysis
    # - Structure conformance check


async def analyze_question_metadata(question: ParliamentQuestion) -> Dict[str, Any]:
    """
    Analyze a question PDF for metadata using Marker.

    Args:
        question: Question object containing PDF data

    Returns:
        Dict containing analysis results
    """
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    try:
        # Initialize Marker converter with debug mode to get detailed metadata
        converter = PdfConverter(artifact_dict=create_model_dict(), config={"debug": True})

        # Convert and analyze PDF
        rendered = converter(str(question["questions_file_path_local"]))
        metadata = rendered.metadata

        # Extract relevant metadata
        page_stats = metadata.get("page_stats", [])
        total_pages = len(page_stats)

        # Analyze table presence
        has_tables = any(any(block_type == "Table" for block_type, _ in page["block_counts"]) for page in page_stats)

        # Calculate total text length
        total_text_length = sum(
            count
            for page in page_stats
            for block_type, count in page["block_counts"]
            if block_type in ("Text", "TextInlineMath")
        )

        # Check structure conformance by analyzing block types and order
        structure_valid = True  # Implement detailed structure validation logic here

        return {
            "question_id": question["question_number"],
            "num_pages": total_pages,
            "has_tables": has_tables,
            "answer_length": total_text_length,
            "structure_valid": structure_valid,
            "analysis_status": "SUCCESS",
            "raw_metadata": metadata,  # Store full metadata for future use
        }

    except Exception as e:
        raise ValueError(f"Failed to analyze PDF for question {question['question_number']}: {e}") from e
