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
    def ensure_absolute_path(cls, v: str) -> str:
        """Ensure the path is absolute by prepending 'data/' if not present"""
        if not v.startswith("data/"):
            return f"data/{v}"
        return v


class CleanedDataUpdateRequest(BaseModel):
    """Request schema for updating cleaned data"""

    pages: list[PageData]
    metadata: QuestionMetadata


class CleanedDataUpdateResponse(BaseModel):
    """Response schema for cleaned data update"""

    status: str
    data: Dict[str, Any]
