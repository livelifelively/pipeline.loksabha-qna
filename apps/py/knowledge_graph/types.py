from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TableData(BaseModel):
    """Table data structure - to be defined based on specific requirements"""

    table_number: int
    data: Dict[str, Any]


class PageData(BaseModel):
    """Represents the cleaned data for a single page"""

    page_number: int
    text: str
    tables: Optional[List[TableData]] = Field(default_factory=list)


class CleanedDataMetadata(BaseModel):
    """Metadata about the cleaned data"""

    total_pages: int
    pages_with_tables: int
    total_tables: int
    cleaning_timestamp: datetime


class CleanedData(BaseModel):
    """The complete cleaned data structure"""

    pages: List[PageData]
    metadata: CleanedDataMetadata
