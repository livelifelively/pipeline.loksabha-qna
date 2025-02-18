from pathlib import Path
from typing import Any

from ..parliament_questions import fetch_and_categorize_questions_pdfs
from ..parliament_questions.adapt_input_data import adapt_source_questions_list_to_parliament_questions
from ..parliament_questions.question_pipeline import process_questions
from ..parliament_questions.types import ParliamentQuestionsPipelineState
from ..utils.project_root import find_project_root
from .context import PipelineContext
from .pipeline import run_pipeline
from .types import PipelineStep


async def sansad_session_pipeline(sansad: str, session: str) -> Any:
    """
    Pipeline for processing Sansad session data.

    Args:
        sansad: Sansad identifier
        session: Session identifier

    Returns:
        Any: Output from the last successful step
    """
    context = PipelineContext.create(__name__, sansad, session)

    steps = [
        PipelineStep(
            name="Adapt Input Data",
            function=adapt_source_questions_list_to_parliament_questions,
            key="ADAPT_INPUT_DATA",
        ),
        PipelineStep(
            name="Fetch Questions PDFs", function=fetch_and_categorize_questions_pdfs, key="FETCH_QUESTIONS_PDFS"
        ),
        PipelineStep(name="Process Individual Questions", function=process_questions, key="PROCESS_QUESTIONS"),
    ]

    outputs = ParliamentQuestionsPipelineState(
        sansad=sansad,
        session=session,
        failed_sansad_session_question_download=[],
        downloaded_sansad_session_questions=[],
        cleaned_question_answer_data=[],
        failed_analysis=[],
        status="PENDING",
    ).model_dump()

    # Setup pipeline directories
    sansad_session_directory = Path(find_project_root()) / f"sansad-{sansad}" / session
    sansad_progress_dir = sansad_session_directory / "sansad-session-pipeline-logs"
    progress_status_file = sansad_progress_dir / "progress-status.json"

    context.log_pipeline(
        "init",
        config={"sansad": sansad, "session": session, "progress_dir": str(sansad_progress_dir), "steps": len(steps)},
    )

    try:
        last_step_output = await run_pipeline(
            context=context,
            steps=steps,
            outputs=outputs,
            progress_dir=sansad_progress_dir,
            progress_file=progress_status_file,
        )
        context.log_pipeline("complete")
        return last_step_output

    except Exception as e:
        context.log_pipeline("failed", error=str(e))
        raise
