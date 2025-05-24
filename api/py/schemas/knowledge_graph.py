# api/py/schemas/knowledge_graph.py

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from apps.py.knowledge_graph.types import PageData, TableData


class PageUpdate(BaseModel):
    """Schema for updating a single page's data"""

    page_number: int
    text: Optional[str] = None
    tables: Optional[List[TableData]] = None


class CleanedDataUpdateRequest(BaseModel):
    """Request schema for updating cleaned data"""

    pages: list[PageData]
    metadata: Dict[str, str] = Field(
        ..., description="Metadata containing question_id, loksabha_number, and session_number"
    )


class CleanedDataUpdateResponse(BaseModel):
    """Response schema for cleaned data update"""

    status: str
    data: Dict[str, Any]
