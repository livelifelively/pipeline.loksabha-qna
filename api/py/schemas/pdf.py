from typing import List, Optional

from pydantic import BaseModel


class PDFExtractRequest(BaseModel):
    """Request schema for PDF extraction."""

    file_path: str
    extractor_type: str = "marker"


class TableSummary(BaseModel):
    """Schema for table summary data."""

    table_number: int
    page: int
    accuracy: float
    num_rows: int
    num_columns: int


class TablesData(BaseModel):
    """Schema for tables data."""

    tables_summary: List[TableSummary]


class ExtractionData(BaseModel):
    """Schema for extraction step data."""

    extracted_text_path: str
    tables_path: str
    has_tables: bool
    num_tables: int
    tables_data: TablesData


class ExtractionStep(BaseModel):
    """Schema for extraction step."""

    step: str
    timestamp: str
    status: str
    data: ExtractionData


class Meta(BaseModel):
    question_number: int
    subjects: str
    loksabha_number: str
    member: List[str]
    ministry: str
    type: str
    date: str
    questions_file_path_local: str
    questions_file_path_web: str
    questions_file_path_hindi_local: Optional[str]
    questions_file_path_hindi_web: str
    question_text: Optional[str]
    answer_text: Optional[str]
    session_number: str


class PDFExtractResponse(BaseModel):
    """Response schema for PDF extraction."""

    meta: Meta
    steps: List[ExtractionStep]
