from typing import Any

from .pipeline import run_pipeline
from .types import PipelineStep
from ..parliament_questions import fetch_and_categorize_questions_pdfs
from ..parliament_questions.questions_meta_analysis import fetch_meta_analysis_for_questions_pdfs
from .context import PipelineContext
from ..utils.project_root import find_project_root
from ..parliament_questions.types import ParliamentQuestionsPipelineState



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
            name="Fetch Questions PDFs",
            function=fetch_and_categorize_questions_pdfs,
            key="FETCH_QUESTIONS_PDFS",
            input={
                "sansad": sansad,
                "session": session,
            }
        ),
        PipelineStep(
            name="Fetch Meta Analysis",
            function=fetch_meta_analysis_for_questions_pdfs,
            key="FETCH_META_ANALYSIS",
            input={
                "sansad": sansad,
                "session": session,
                "downloadedSansadSessionQuestions": []
            }
        )
    ]
    
    outputs = ParliamentQuestionsPipelineState(
        sansad=sansad,
        session=session,
        failed_sansad_session_question_download=[],
        downloaded_sansad_session_questions=[],
        cleaned_qna_data=[],
        status="PENDING"
    ).dict()
    
    # Setup pipeline directories
    sansad_session_directory = find_project_root() / f"sansad-{sansad}" / session
    sansad_progress_dir = sansad_session_directory / "sansad-session-pipeline-logs"
    progress_status_file = sansad_progress_dir / "progress-status.json"
    
    context.log_pipeline("init", 
        config={
            "sansad": sansad,
            "session": session,
            "progress_dir": str(sansad_progress_dir),
            "steps": len(steps)
        }
    )
    
    try:
        last_step_output = await run_pipeline(
            context=context,
            steps=steps,
            initial_outputs=outputs,
            progress_dir=sansad_progress_dir,
            progress_file=progress_status_file
        )
        context.log_pipeline("complete")
        return last_step_output
        
    except Exception as e:
        context.log_pipeline("failed", error=str(e))
        raise 