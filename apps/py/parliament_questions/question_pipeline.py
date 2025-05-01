from pathlib import Path
from typing import Any, Dict

from ..pipeline.context import PipelineContext
from ..pipeline.pipeline import run_pipeline
from ..pipeline.types import PipelineStep
from ..utils.project_root import get_loksabha_data_root
from .types import QuestionPipelineState


async def analyze_single_question(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Simulates analysis of a question PDF with intentional failures for testing.
    """
    question_number = int(outputs["question_number"])

    context.log_step("analysis_start", question_number=question_number)

    try:
        # Simulate failure for questions that are multiples of 37
        if question_number % 37 == 0:
            raise Exception(f"Simulated failure for question {question_number}")

        context.log_step("analysis_complete", question_number=question_number)

        return {"status": "SUCCESS", "analysis_result": f"Simulated analysis for question {question_number}"}

    except Exception as e:
        context.log_step("analysis_failed", question_number=question_number, error=str(e))
        return {"status": "FAILURE", "error": str(e)}


async def single_question_analysis_pipeline(question: Dict[str, Any], parent_context: PipelineContext) -> Any:
    """
    Pipeline for processing individual question data.

    Args:
        question: Question data to process
        parent_context: Parent pipeline context

    Returns:
        Any: Output from the last successful step
    """
    # Create question-specific context
    context = PipelineContext.create(
        f"question-{question['question_number']}", question["loksabha_number"], question["session_number"]
    )

    steps = [PipelineStep(name="Analyze Single Question", function=analyze_single_question, key="ANALYZE_QUESTION")]

    outputs = QuestionPipelineState(
        sansad=question["loksabha_number"],
        session=question["session_number"],
        question_number=question["question_number"],
        ministry=question["ministry"],
        local_file_path=question["questions_file_path_local"],
        status="PENDING",
    ).model_dump()

    # Setup pipeline directories
    question_dir = get_loksabha_data_root() / Path(question["questions_file_path_local"]).parent
    pipeline_dir = question_dir / "pipeline-logs"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    progress_file = pipeline_dir / "progress-status.json"

    context.log_pipeline(
        "init",
        config={
            "question_number": question["question_number"],
            "ministry": question["ministry"],
            "progress_dir": str(pipeline_dir),
        },
    )

    try:
        last_step_output = await run_pipeline(
            context=context, steps=steps, outputs=outputs, progress_dir=pipeline_dir, progress_file=progress_file
        )
        context.log_pipeline("complete")
        return last_step_output

    except Exception as e:
        context.log_pipeline("failed", error=str(e))
        raise


async def batch_question_analysis(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Process each downloaded question through its own analysis pipeline.
    """
    downloaded_questions = outputs.get("downloaded_sansad_session_questions", [])

    context.log_step("processing_start", total_questions=len(downloaded_questions))

    processed_questions = []
    failed_questions = []

    for i, question in enumerate(downloaded_questions):
        try:
            result = await single_question_analysis_pipeline(question, context)
            processed_questions.append(result)

            context.log_step(
                "question_processed",
                question_number=question["question_number"],
                progress=f"{i + 1}/{len(downloaded_questions)}",
            )

        except Exception as e:
            failed_questions.append({"question": question, "error": str(e)})
            context.log_step("question_failed", question_number=question["question_number"], error=str(e))

    status = "SUCCESS" if not failed_questions else "PARTIAL"
    context.log_step(
        "complete", status=status, total_processed=len(processed_questions), total_failed=len(failed_questions)
    )

    return {"status": status, "processed_questions": processed_questions, "failed_questions": failed_questions}
