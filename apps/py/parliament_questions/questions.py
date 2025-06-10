import json
import logging
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict

from apps.py.documents.utils.progress_handler import DocumentProgressHandler

from ..pipeline.context import PipelineContext
from ..utils.file_utils import filename_generator, kebab_case_names
from ..utils.pdf import DownloadConfig, download_pdfs
from ..utils.project_root import get_loksabha_data_root
from .types import ParliamentQuestion, QuestionType

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuestionType):
            return obj.value  # Simply return the enum value
        return super().default(obj)


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

    # Setup directories and handlers
    sansad_session_directory = get_loksabha_data_root() / sansad / session
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
            relative_question_dir = question_dir.relative_to(get_loksabha_data_root())

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
                    session_number=question["session_number"],
                    member=question["member"],
                    ministry=question["ministry"],
                    type=question["type"],
                    date=question["date"],
                    questions_file_path_web=question["questions_file_path_web"],
                    questions_file_path_local=str(relative_question_dir / filename_generator(pdf_url, 0)),
                    questions_file_path_hindi_web=question.get("questions_file_path_hindi_web"),
                )
                downloaded_questions.append(downloaded_question)

                # Initialize progress tracking with question metadata
                question_metadata = downloaded_question.model_dump()
                context.log_step("question_metadata", data=question_metadata)
                progress_handler = DocumentProgressHandler(question_dir)
                progress_handler.transition_to_initialized(question_metadata)

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
        "downloaded_sansad_session_questions": [
            {
                **q.model_dump(),
                "type": str(q.type.value) if q.type else None,  # Explicitly convert enum to string
            }
            for q in downloaded_questions
        ],
        "status": status,
    }
