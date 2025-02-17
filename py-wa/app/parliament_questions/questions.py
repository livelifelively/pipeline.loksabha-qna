import logging
from itertools import groupby
from operator import itemgetter
from pathlib import Path
from typing import Any, Dict

from ..pipeline.context import PipelineContext
from ..utils.file_utils import filename_generator, kebab_case_names
from ..utils.pdf import DownloadConfig, download_pdfs
from ..utils.project_root import find_project_root
from .types import ParliamentQuestion

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
    parliament_session_questions = outputs["parliament_session_questions"]

    context.log_step("init", params={"sansad": sansad, "session": session})

    # Setup directories
    project_root = find_project_root()
    sansad_session_directory = Path(project_root) / f"sansad-{sansad}" / session
    sansad_session_directory.mkdir(parents=True, exist_ok=True)

    # Group questions by ministry
    questions = sorted(parliament_session_questions, key=itemgetter("ministry"))
    grouped_questions = {k: list(g) for k, g in groupby(questions, key=itemgetter("ministry"))}

    context.log_step("processing_start", total_ministries=len(grouped_questions), total_questions=len(questions))

    failed_downloads = []
    downloaded_questions = []

    # Process each ministry's questions
    for ministry, ministry_questions in grouped_questions.items():
        for question in ministry_questions:
            ministry_dir = sansad_session_directory / "ministries" / kebab_case_names(ministry)
            question_dir = ministry_dir / kebab_case_names(str(question["question_number"]).strip())
            question_dir.mkdir(parents=True, exist_ok=True)

            pdf_url = question["questions_file_path_web"]
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
                    overwrite_existing=False,
                )
                download_results = await download_pdfs([pdf_url], config)
                file_path, was_downloaded = download_results[0]

                # Create ParliamentQuestion instance
                downloaded_question = ParliamentQuestion(
                    question_number=question["question_number"],
                    subjects=question["subjects"],
                    loksabha_number=question["loksabha_number"],
                    member=question["member"],
                    ministry=question["ministry"],
                    type=question["type"],
                    date=question["date"],
                    questions_file_path_web=question["questions_file_path_web"],
                    questions_file_path_local=str(relative_question_dir / filename_generator(pdf_url, 0)),
                    questions_file_path_hindi_web=question.get("questions_file_path_hindi_web"),
                )
                downloaded_questions.append(downloaded_question)

                context.log_step(
                    "question_processed",
                    question_number=question["question_number"],
                    ministry=ministry,
                    progress=f"{len(downloaded_questions)}/{len(questions)}",
                    action="downloaded" if was_downloaded else "found_existing",
                )

            except Exception as e:
                failed_downloads.append(pdf_url)
                context.log_step(
                    "download_failed", question_number=question["question_number"], ministry=ministry, error=str(e)
                )

    status = "PARTIAL" if failed_downloads else "SUCCESS"
    context.log_step(
        "complete", status=status, total_downloaded=len(downloaded_questions), total_failed=len(failed_downloads)
    )

    return {
        "failed_sansad_session_question_download": failed_downloads,
        "downloaded_sansad_session_questions": [q.dict() for q in downloaded_questions],
        "status": status,
    }
