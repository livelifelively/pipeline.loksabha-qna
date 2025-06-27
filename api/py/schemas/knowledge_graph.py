# api/py/schemas/knowledge_graph.py

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from apps.py.knowledge_graph.types import PageData, TableData
from apps.py.types import ManualReviewPageData, ProcessingStatus


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


# ============================================================================
# MANUAL REVIEW SCHEMAS
# ============================================================================


class ManualReviewPageUpdateRequest(BaseModel):
    """Request schema for updating a single page in manual review"""

    document_path: str = Field(..., description="The path to the question document folder")
    page_number: int = Field(..., description="Page number to update", ge=1)
    page_data: ManualReviewPageData = Field(..., description="Complete page data for manual review")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        return v


class ManualReviewPageUpdateResponse(BaseModel):
    """Response schema for manual review page update"""

    status: str
    data: Dict[str, Any]  # Full state data from question.progress.json


class ManualReviewStatusUpdateRequest(BaseModel):
    """Request schema for updating manual review processing status"""

    document_path: str = Field(..., description="The path to the question document folder")
    status: ProcessingStatus = Field(..., description="New processing status")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the status update")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        return v


class ManualReviewStatusUpdateResponse(BaseModel):
    """Response schema for manual review status update"""

    status: str
    data: Dict[str, Any]  # Full state data from question.progress.json


class ManualReviewBulkPagesUpdateRequest(BaseModel):
    """Request schema for updating multiple pages in manual review"""

    document_path: str = Field(..., description="The path to the question document folder")
    pages_data: Dict[int, ManualReviewPageData] = Field(..., description="Dictionary mapping page numbers to page data")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        return v

    @field_validator("pages_data")
    def validate_pages_data(cls, v: Dict[int, ManualReviewPageData]) -> Dict[int, ManualReviewPageData]:
        """Validate that pages_data is not empty and page numbers are positive"""
        if not v:
            raise ValueError("pages_data cannot be empty")
        for page_num in v.keys():
            if page_num < 1:
                raise ValueError(f"Page number must be >= 1, got {page_num}")
        return v


class ManualReviewBulkPagesUpdateResponse(BaseModel):
    """Response schema for bulk pages update"""

    status: str
    data: Dict[str, Any]  # Full state data from question.progress.json


class ManualReviewStatusRequest(BaseModel):
    """Request schema for retrieving manual review status"""

    document_path: str = Field(..., description="The path to the question document folder")

    @field_validator("document_path")
    def validate_document_path(cls, v: str) -> str:
        """Validate that the document path is properly formatted"""
        if not v or v.isspace():
            raise ValueError("Document path cannot be empty")
        return v


class ManualReviewStatusResponse(BaseModel):
    """Response schema for manual review status retrieval"""

    status: str
    data: Dict[str, Any]  # Full state data from question.progress.json
