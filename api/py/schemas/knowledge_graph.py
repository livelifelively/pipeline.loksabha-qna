# api/py/schemas/knowledge_graph.py

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from apps.py.knowledge_graph.types import PageData, TableData


class PageUpdate(BaseModel):
    """Schema for updating a single page's data"""

    page_number: int
    text: Optional[str] = None
    tables: Optional[List[TableData]] = None


class QuestionMetadata(BaseModel):
    """Metadata for identifying a question"""

    document_path: str = Field(..., description="The path to the question document folder", alias="documentPath")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        # Add any other format validations as needed
        return v


class CleanedDataUpdateRequest(BaseModel):
    """Request schema for updating cleaned data"""

    pages: list[PageData]
    metadata: QuestionMetadata


class CleanedDataUpdateResponse(BaseModel):
    """Response schema for cleaned data update"""

    status: str
    data: Dict[str, Any]  # Contains: updated_pages, progress_status, timestamp


class LlmExtractionRequest(BaseModel):
    """Request schema for LLM extraction"""

    document_path: str = Field(..., description="The path to the question document folder")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        return v


class LlmExtractionResponse(BaseModel):
    """Response schema for LLM extraction"""

    status: str
    data: Dict[str, Any]  # Full state data from question.progress.json
