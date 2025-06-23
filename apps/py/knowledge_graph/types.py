from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TableData(BaseModel):
    """Table data structure - to be defined based on specific requirements"""

    table_number: int
    data: Dict[str, Any]


class PageData(BaseModel):
    """Represents the cleaned data for a single page"""

    page_number: int
    text: str
    # tables: Optional[List[TableData]] = Field(default_factory=list)
    tables: Optional[List[Any]] = None
