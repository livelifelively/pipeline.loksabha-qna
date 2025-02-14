import json
import logging
from pathlib import Path
from typing import Dict, Any
from itertools import groupby
from operator import itemgetter

from .types import ParliamentQuestion, PipelineOutput
from ..utils.project_root import find_project_root
from ..utils.file_utils import kebab_case_names, filename_generator
from ..utils.pdf import download_pdfs, DownloadConfig
from ..utils.pipeline_context import PipelineContext

logger = logging.getLogger(__name__)


async def fetch_and_categorize_questions_pdfs(outputs: Dict[str, Any], context: PipelineContext) -> Dict[str, Any]:
    """
    Fetch and categorize parliament questions PDFs.
    
    Args:
        outputs: Pipeline outputs containing sansad and session info
        context: Pipeline context for logging
        
    Returns:
        Dict containing download status and processed questions
    """
    sansad = outputs["sansad"]
    session = outputs["session"]
    
    context.log_step("init", 0, "Fetch Questions PDFs", 
        params={"sansad": sansad, "session": session}
    )
    
    # Setup directories
    project_root = find_project_root()
    sansad_session_directory = Path(project_root) / f"sansad-{sansad}" / session
    sansad_session_directory.mkdir(parents=True, exist_ok=True)
    
    qna_file = sansad_session_directory / f"{sansad}_{session}.qna.json"
    
    # Check if file exists
    if not qna_file.exists():
        context.log_step("qna_file_missing", 0, "Fetch Questions PDFs", 
            error=f"QnA file not found: {qna_file}"
        )
        return {
            "failedSansadSessionQuestionDownload": [],
            "downloadedSansadSessionQuestions": [],
            "status": "FAILURE",
            "error": f"QnA file not found: {qna_file}"
        }

    # Load QnA data
    with qna_file.open() as f:
        qna_data = json.load(f)
    
    # Group questions by ministry
    questions = sorted(qna_data["listOfQuestions"], key=itemgetter("ministry"))
    grouped_questions = {k: list(g) for k, g in groupby(questions, key=itemgetter("ministry"))}
    
    context.log_step("processing_start", 0, "Fetch Questions PDFs",
        total_ministries=len(grouped_questions),
        total_questions=len(questions)
    )
    
    failed_downloads = []
    downloaded_questions = []
    
    # Process each ministry's questions
    for ministry, ministry_questions in grouped_questions.items():
        for question in ministry_questions:
            ministry_dir = sansad_session_directory / "ministries" / kebab_case_names(ministry)
            question_dir = ministry_dir / kebab_case_names(str(question["quesNo"]).strip())
            question_dir.mkdir(parents=True, exist_ok=True)
            
            pdf_url = question["questionsFilePath"]
            project_root = find_project_root()
            relative_question_dir = question_dir.relative_to(project_root)
            
            try:
                # Download PDF
                config = DownloadConfig(
                    output_directory=question_dir,
                    filename_generator=filename_generator,
                    timeout_ms=30000,
                    retries=5,
                    retry_delay_ms=2000,
                    overwrite_existing=False
                )
                await download_pdfs([pdf_url], config)
                
                # Create ParliamentQuestion instance
                downloaded_question = ParliamentQuestion(
                    ques_no=question["quesNo"],
                    subjects=question["subjects"],
                    lok_no=question["lokNo"],
                    member=question["member"],
                    ministry=question["ministry"],
                    type=question["type"],
                    date=question["date"],
                    questions_file_path_web=question["questionsFilePath"],
                    questions_file_path_local=str(relative_question_dir / filename_generator(pdf_url, 0)),
                    questions_file_path_hindi_web=question.get("questionsFilePathHindi")
                )
                downloaded_questions.append(downloaded_question)
                
                context.log_step("question_downloaded", 0, "Fetch Questions PDFs",
                    question_id=question["quesNo"],
                    ministry=ministry,
                    progress=f"{len(downloaded_questions)}/{len(questions)}"
                )
                
            except Exception as e:
                failed_downloads.append(pdf_url)
                context.log_step("download_failed", 0, "Fetch Questions PDFs",
                    question_id=question["quesNo"],
                    ministry=ministry,
                    error=str(e)
                )
    
    status = "PARTIAL" if failed_downloads else "SUCCESS"
    context.log_step("complete", 0, "Fetch Questions PDFs",
        status=status,
        total_downloaded=len(downloaded_questions),
        total_failed=len(failed_downloads)
    )
    
    return {
        "failedSansadSessionQuestionDownload": failed_downloads,
        "downloadedSansadSessionQuestions": [q.dict() for q in downloaded_questions],
        "status": status
    }
