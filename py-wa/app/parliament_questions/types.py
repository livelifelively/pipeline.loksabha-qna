from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ParliamentQuestion(BaseModel):
    """
    Represents a question asked in the Parliament.
    """
    ques_no: int = Field(..., description="Unique identifier for the question")
    subjects: str = Field(..., description="Topic or subject of the question")
    lok_no: str = Field(..., description="Lok Sabha session number")
    member: List[str] = Field(..., description="List of members who asked the question")
    ministry: str = Field(..., description="Ministry to which question is directed")
    type: str = Field(..., description="Type of question (STARRED/UNSTARRED)")
    date: str = Field(..., description="Date of the question")
    questions_file_path_local: str = Field(..., description="Local path to question PDF")
    questions_file_path_web: str = Field(..., description="Web URL of question PDF")
    questions_file_path_hindi_local: Optional[str] = Field(None, description="Local path to Hindi version")
    questions_file_path_hindi_web: Optional[str] = Field(None, description="Web URL of Hindi version")
    question_text: Optional[str] = Field(None, description="Extracted question text")
    answer_text: Optional[str] = Field(None, description="Extracted answer text")
    session_no: Optional[str] = Field(None, description="Parliament session number")

    class Config:
        """Pydantic model configuration"""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
class QuestionMetaAnalysis(BaseModel):
    """
    #TODO: Add more fields and structure_conformance is not a boolean, it is a percentage
    # need to review it while implementing it
    Metadata analysis of a parliament question.
    """
    num_pages: Optional[int] = Field(None, description="Number of pages in the PDF")
    has_table: Optional[bool] = Field(None, description="Whether the document contains tables")
    answer_length: Optional[int] = Field(None, description="Number of characters in the answer")
    structure_conformance: Optional[bool] = Field(None, description="Whether document follows standard structure")

class PipelineOutput(BaseModel):
    """
    Output structure for pipeline steps.
    """
    failed_sansad_session_question_download: List[str] = Field(
        default_factory=list,
        description="List of URLs that failed to download"
    )
    downloaded_sansad_session_questions: List[ParliamentQuestion] = Field(
        default_factory=list,
        description="List of successfully downloaded and processed questions"
    )
    cleaned_qna_data: Optional[List[ParliamentQuestion]] = Field(
        default_factory=list,
        description="List of cleaned question and answer data"
    )
    status: str = Field(..., description="Status of the pipeline step")
