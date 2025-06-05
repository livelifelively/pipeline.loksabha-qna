# apps/py/documents/models.py
from typing import Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class MultiPageTableInfo(BaseModel):
    """Information about a single multi-page table."""

    pages: List[int] = Field(description="List of page numbers that are part of this table")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this table detection")
    reasoning: str = Field(description="Explanation of why these pages are connected")


class ExtractionResult(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    output_file: Optional[str] = None
    error: Optional[str] = None
    tables_count: Optional[int] = None
    reused_existing: Optional[bool] = None


class MultiPageTableResult(ExtractionResult):
    pages: List[int]
    page_range: Tuple[int, int]
    table_number: Optional[int] = Field(None, description="Sequential number of the table")
    table_dimensions: Optional[List[Dict[str, int]]] = Field(
        None, description="Array of table dimensions, where each element contains num_rows for that table"
    )


class SinglePageTableResult(ExtractionResult):
    page_number: int
    table_number: Optional[int] = Field(None, description="Sequential number of the table")
    table_dimensions: Optional[List[Dict[str, int]]] = Field(
        None, description="Array of table dimensions, where each element contains num_rows for that table"
    )


class ExtractionSummary(BaseModel):
    """Summary statistics for the extraction process."""

    total_tables: int = Field(description="Total number of tables processed")
    successful_tables: int = Field(description="Number of successfully extracted tables")
    failed_tables: int = Field(description="Number of failed table extractions")
    multi_page_tables: int = Field(description="Number of multi-page tables")
    single_page_tables: int = Field(description="Number of single-page tables")


# Type aliases for better readability
PageNumber = int
PageRange = Tuple[int, int]
PageIdentifier = Union[PageNumber, PageRange]
TableResult = Union[SinglePageTableResult, MultiPageTableResult]


class CombinedResults(BaseModel):
    """Combined results from all extraction processes."""

    pages_processed: int = Field(description="Total number of pages processed")
    table_results: Dict[PageIdentifier, TableResult] = Field(
        description="Raw results mapping page numbers (for single pages) or page ranges (for multi-page tables) to their extraction results"
    )
    summary: ExtractionSummary = Field(description="Summary statistics for the extraction process")
    text_results: Dict[int, ExtractionResult] = Field(
        default_factory=dict, description="Mapping of page numbers to their text extraction results"
    )

    # Structured view of results
    multi_page_tables: List[MultiPageTableResult] = Field(
        default_factory=list, description="List of all multi-page tables found"
    )
    single_page_tables: List[SinglePageTableResult] = Field(
        default_factory=list, description="List of all single-page table results"
    )
    pages_with_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that are part of multi-page tables"
    )
    pages_with_single_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that contain single-page tables"
    )
    pages_with_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that contain any type of table"
    )
    pages_with_errors: Set[int] = Field(
        default_factory=set, description="Set of all pages that encountered errors during processing"
    )
    errors: Dict[int, str] = Field(default_factory=dict, description="Mapping of page numbers to error messages")

    def __init__(self, **data):
        super().__init__(**data)
        # Process results into structured format
        table_counter = 1  # Counter for assigning table numbers
        for key, result in self.table_results.items():
            if isinstance(key, tuple):  # Multi-page table
                if isinstance(result, MultiPageTableResult) and result.status == "success":
                    result.table_number = table_counter
                    self.multi_page_tables.append(result)  # Add the full MultiPageTableResult
                    self.pages_with_multi_page_tables.update(result.pages)
                    self.pages_with_tables.update(result.pages)
                    table_counter += 1
                elif result.status == "error":
                    self.pages_with_errors.update(result.pages)
            else:  # Single page
                if isinstance(result, SinglePageTableResult):
                    if result.status == "error":
                        self.errors[key] = result.error
                        self.pages_with_errors.add(key)
                    else:
                        result.table_number = table_counter
                        self.single_page_tables.append(result)
                        self.pages_with_tables.add(key)
                        table_counter += 1
                    self.pages_with_single_page_tables.add(key)

        # Process text results
        for page_num, text_result in self.text_results.items():
            if text_result.status == "error":
                self.errors[page_num] = text_result.error
                self.pages_with_errors.add(page_num)

    class Config:
        json_encoders = {
            set: list,  # Convert sets to lists in JSON
            Tuple: list,  # Convert tuples to lists in JSON
        }


class TableDetectionResult(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    is_multi_page_table: Optional[bool] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    error: Optional[str] = None


class MultiPageTableDetectionResult(BaseModel):
    """Result of multi-page table detection."""

    status: str = Field(..., pattern="^(success|error)$", description="Status of the detection: 'success' or 'error'")
    multi_page_tables: List[MultiPageTableInfo] = Field(
        default_factory=list, description="List of detected multi-page tables"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class TableSummary(BaseModel):
    """Summary statistics for table extraction."""

    total_tables: int = Field(description="Total number of tables processed")
    successful_tables: int = Field(description="Number of successfully extracted tables")
    failed_tables: int = Field(description="Number of failed table extractions")


class MultiPageTableExtractionResults(BaseModel):
    """Structured results for table extraction process."""

    pages_processed: int = Field(description="Total number of pages processed")

    # Results mapping using the type aliases
    table_results: Dict[PageIdentifier, TableResult] = Field(
        description="Raw results mapping page numbers (for single pages) or page ranges (for multi-page tables) to their extraction results"
    )

    summary: TableSummary = Field(description="Summary statistics for the extraction process")

    # Structured view of results
    multi_page_tables: List[MultiPageTableInfo] = Field(
        default_factory=list, description="List of all multi-page tables found"
    )
    pages_with_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that are part of multi-page tables"
    )
    pages_without_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that need single-page processing"
    )
    errors: Dict[int, str] = Field(default_factory=dict, description="Mapping of page numbers to error messages")

    def __init__(self, **data):
        super().__init__(**data)
        # Process results into structured format
        table_counter = 1  # Counter for assigning table numbers
        for key, result in self.table_results.items():
            if isinstance(key, tuple):  # Multi-page table
                if isinstance(result, MultiPageTableResult) and result.status == "success":
                    result.table_number = table_counter
                    self.multi_page_tables.append(
                        MultiPageTableInfo(
                            pages=result.pages,
                            page_range=result.page_range,
                            confidence=result.confidence,
                            output_file=result.output_file,
                        )
                    )
                    self.pages_with_multi_page_tables.update(result.pages)
                    table_counter += 1
            else:  # Single page
                if isinstance(result, SinglePageTableResult):
                    if result.status == "error":
                        self.errors[key] = result.error
                    else:
                        result.table_number = table_counter
                        table_counter += 1
                    self.pages_without_multi_page_tables.add(key)

    class Config:
        json_encoders = {
            set: list,  # Convert sets to lists in JSON
            Tuple: list,  # Convert tuples to lists in JSON
        }
