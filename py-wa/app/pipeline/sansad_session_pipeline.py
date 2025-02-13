import logging
from pathlib import Path
from typing import Any, Dict

from .pipeline import run_pipeline
from .types import PipelineStep
from ..parliament_questions import fetch_and_categorize_questions_pdfs
from ..parliament_questions.questions_meta_analysis import fetch_meta_analysis_for_questions_pdfs

logger = logging.getLogger(__name__)

async def sansad_session_pipeline(sansad: str, session: str) -> Any:
    """
    Pipeline for processing Sansad session data.
    
    Args:
        sansad: Sansad identifier
        session: Session identifier
        
    Returns:
        Any: Output from the last successful step
    """
    logger.info(f"SANSAD SESSION PROCESSING INITIALIZED: {sansad} {session}")
    
    steps: list[PipelineStep] = [
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
            name="Fetch Meta Analysis for Questions PDFs",
            function=fetch_meta_analysis_for_questions_pdfs,
            key="FETCH_META_ANALYSIS_FOR_QUESTIONS_PDFS",
            input={
                "sansad": sansad,
                "session": session,
                "downloadedSansadSessionQuestions": []
            }
        )
    ]
    
    outputs: Dict[str, Any] = {
        "sansad": sansad,
        "session": session,
        "failedSansadSessionQuestionDownload": [],
        "downloadedSansadSessionQuestions": [],
        "cleanedQnAData": []
    }
    
    # Using Path for better path handling
    sansad_session_directory = Path(__file__).parent.parent.parent / f"sansad-{sansad}" / session
    sansad_progress_dir = sansad_session_directory / "sansad-session-pipeline-logs"
    progress_status_file = sansad_progress_dir / "progress-status.json"
    
    try:
        last_step_output = await run_pipeline(
            steps=steps,
            initial_outputs=outputs,
            progress_dir=sansad_progress_dir,
            progress_file=progress_status_file
        )
        return last_step_output
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise 