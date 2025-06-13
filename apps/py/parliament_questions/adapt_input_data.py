import json
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from apps.py.types import ParliamentQuestion

from ..pipeline.context import PipelineContext
from ..utils.project_root import get_loksabha_data_root


class SourceParliamentQuestion(BaseModel):
    """Model for source parliament question data."""

    quesNo: int = Field(..., description="Question number")
    subjects: str = Field(..., description="Question subjects")
    lokNo: str = Field(..., description="Lok Sabha number")
    member: List[str] = Field(..., description="List of member names")
    ministry: str = Field(..., description="Ministry name")
    type: Literal["STARRED", "UNSTARRED"] = Field(..., description="Question type")
    date: str = Field(..., description="Question date")
    questionText: Optional[str] = Field(None, description="Question text")
    answerText: Optional[str] = Field(None, description="Answer text")
    answerTextHindi: Optional[str] = Field(None, description="Hindi answer text")
    questionsFilePath: str = Field(..., description="Path to questions file")
    questionsFilePathHindi: Optional[str] = Field(None, description="Path to Hindi questions file")
    sessionNo: str = Field(..., description="Session number")
    supplementaryQuestionResDtoList: Optional[List[Any]] = Field(
        default_factory=list, description="List of supplementary questions"
    )
    supplementaryType: Optional[bool] = Field(None, description="Whether question has supplementary type")


async def adapt_source_questions_list_to_parliament_questions(
    outputs: Dict[str, Any], context: PipelineContext
) -> Dict[str, Any]:
    """
    Adapt source questions list to standardized parliament questions format.

    Args:
        outputs: Pipeline outputs containing sansad and session info
        context: Pipeline context for logging

    Returns:
        Dict containing adapted parliament questions and status
    """
    sansad = outputs["sansad"]
    session = outputs["session"]

    context.log_step("init", params={"sansad": sansad, "session": session})

    # Setup file paths
    sansad_session_directory = get_loksabha_data_root() / sansad / session
    qna_file = sansad_session_directory / f"{sansad}_{session}.qna.source.json"

    if not qna_file.exists():
        context.log_step("qna_file_missing", error=f"Source QnA file not found: {qna_file}")
        return {
            "status": "FAILURE",
            "error": f"Source QnA file not found: {qna_file}",
        }

    try:
        # Load and parse source data
        qna_data = json.loads(qna_file.read_text())
        source_questions_list = [SourceParliamentQuestion(**question) for question in qna_data[0]["listOfQuestions"]]

        context.log_step("processing_start", total_questions=len(source_questions_list))

        # Transform to ParliamentQuestion format
        parliament_session_questions = []
        for question in source_questions_list:
            adapted_question = ParliamentQuestion(
                question_number=str(question.quesNo).strip(),
                subjects=str(question.subjects).strip(),
                loksabha_number=str(question.lokNo).strip(),
                session_number=str(question.sessionNo).strip(),
                member=[str(m).strip() for m in question.member],
                ministry=str(question.ministry).strip(),
                type=str(question.type).strip(),
                date=str(question.date).strip(),
                # questions_file_path_local=question.questionsFilePath,
                questions_file_path_web=str(question.questionsFilePath).strip(),
                # questions_file_path_hindi_local=question.questionsFilePathHindi,
                questions_file_path_hindi_web=str(question.questionsFilePathHindi).strip()
                if question.questionsFilePathHindi
                else "",
            )
            parliament_session_questions.append(adapted_question)

        context.log_step("complete", status="SUCCESS", total_adapted=len(parliament_session_questions))

        return {
            "parliament_session_questions": [q.model_dump() for q in parliament_session_questions],
            "status": "SUCCESS",
        }

    except Exception as e:
        context.log_step("adaptation_failed", error=str(e))
        return {
            "status": "FAILURE",
            "error": str(e),
        }
