from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionType(Enum):
    """Enum for parliament question types"""

    STARRED = "STARRED"
    UNSTARRED = "UNSTARRED"


class ParliamentQuestion(BaseModel):
    """
    Represents a question asked in the Parliament.
    """

    question_number: int = Field(..., description="Unique identifier for the question")
    subjects: str = Field(..., description="Topic or subject of the question")
    loksabha_number: str = Field(..., description="Lok Sabha session number")
    member: List[str] = Field(..., description="List of members who asked the question")
    ministry: str = Field(..., description="Ministry to which question is directed")
    type: QuestionType = Field(..., description="Type of question (STARRED/UNSTARRED)")
    date: str = Field(..., description="Date of the question")
    questions_file_path_local: Optional[str] = Field(None, description="Local path to question PDF")
    questions_file_path_web: str = Field(..., description="Web URL of question PDF")
    questions_file_path_hindi_local: Optional[str] = Field(None, description="Local path to Hindi version")
    questions_file_path_hindi_web: str = Field(..., description="Web URL of Hindi version")
    question_text: Optional[str] = Field(None, description="Extracted question text")
    answer_text: Optional[str] = Field(None, description="Extracted answer text")
    session_number: str = Field(..., description="Parliament session number")

    class Config:
        """Pydantic model configuration"""

        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class QuestionMetaAnalysis(BaseModel):
    """
    Enhanced metadata analysis of a parliament question using Marker.
    """

    num_pages: Optional[int] = Field(None, description="Number of pages in the PDF")
    has_table: Optional[bool] = Field(None, description="Whether the document contains tables")
    answer_length: Optional[int] = Field(None, description="Number of text blocks in the document")
    structure_conformance: Optional[float] = Field(
        None, description="Percentage indicating how well the document follows standard structure", ge=0.0, le=100.0
    )
    raw_metadata: Optional[Dict[str, Any]] = Field(None, description="Raw metadata from Marker analysis")


class ParliamentQuestionsPipelineState(BaseModel):
    """
    Shared state for parliament questions pipeline steps.
    Contains the cumulative state that gets passed between steps.
    """

    sansad: str = Field(..., description="Parliament session number")
    session: str = Field(..., description="Parliament session number")
    failed_sansad_session_question_download: List[str] = Field(
        default_factory=list, description="List of URLs that failed to download"
    )
    downloaded_sansad_session_questions: List[ParliamentQuestion] = Field(
        default_factory=list, description="List of successfully downloaded and processed questions"
    )
    cleaned_question_answer_data: Optional[List[ParliamentQuestion]] = Field(
        default_factory=list, description="List of cleaned question and answer data"
    )
    failed_analysis: Optional[List[QuestionMetaAnalysis]] = Field(
        default_factory=list, description="List of failed analysis"
    )
    status: str = Field(..., description="Status of the pipeline step")


class QuestionPipelineState(BaseModel):
    """State for individual question pipeline processing"""

    sansad: str = Field(..., description="Parliament session number")
    session: str = Field(..., description="Session number")
    question_number: int = Field(..., description="Question number")
    ministry: str = Field(..., description="Ministry name")
    status: str = Field(default="PENDING", description="Pipeline status")
