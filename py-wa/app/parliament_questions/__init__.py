import json
import logging
from pathlib import Path
from typing import Dict, Any
from itertools import groupby
from operator import itemgetter

from .types import ParliamentQuestion, PipelineOutput
from ..utils.project_root import find_project_root, kebab_case_names, filename_generator
from ..utils.pdf import download_pdfs, DownloadConfig

logger = logging.getLogger(__name__)

async def fetch_and_categorize_questions_pdfs(outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch and categorize parliament question PDFs.
    
    Args:
        outputs: Pipeline outputs containing sansad and session info
        
    Returns:
        Dict containing download status and processed questions
    """
    sansad = outputs["sansad"]
    session = outputs["session"]
    
    # Setup directories
    sansad_session_directory = Path(__file__).parent.parent.parent / f"sansad-{sansad}" / session
    qna_file = sansad_session_directory / f"{sansad}_{session}.qna.json"
    
    # Load QnA data
    with qna_file.open() as f:
        qna_data = json.load(f)
    
    # Group questions by ministry
    questions = sorted(qna_data["listOfQuestions"], key=itemgetter("ministry"))
    grouped_questions = {k: list(g) for k, g in groupby(questions, key=itemgetter("ministry"))}
    
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
                downloaded_questions.append(
                    ParliamentQuestion(
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
                )
            except Exception as e:
                logger.error(f"Error downloading PDF: {e}")
                failed_downloads.append(pdf_url)
    
    return {
        "failedSansadSessionQuestionDownload": failed_downloads,
        "downloadedSansadSessionQuestions": [q.dict() for q in downloaded_questions],
        "status": "PARTIAL" if failed_downloads else "SUCCESS"
    }
