import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from apps.py.types import (
    CombinedResults,
    ExtractionResult,
    ExtractionSummary,
    LlmExtractionData,
    LlmExtractionPageData,
    LocalExtractionData,
    PageIdentifier,
    ProcessingMetadata,
    ProcessingStatus,
    SinglePageTableResult,
    TableResult,
)
from apps.py.utils.project_root import get_loksabha_data_root

from ..utils.progress_handler import DocumentProgressHandler
from .base import BaseExtractor
from .page_splitter import PDFPageSplitter
from .result_combiner import ExtractionResultCombiner
from .table import MultiPageTableHandler, TableExtractor
from .table_range_detector import TableRangeDetector
from .text import TextExtractor


class ExtractionConfig:
    """Configuration constants for PDF extraction orchestrator."""

    # Output folder and file names
    TABLE_EXTRACTION_FOLDER = "table_extraction"
    EXTRACTED_TEXT_FILENAME = "extracted_text.md"

    # Default values
    DEFAULT_NUM_TABLES_PER_PAGE = 1

    # Error messages
    FAILED_PDF_CREATION_ERROR = "Failed to create temporary PDF for page {page_num}"
    UNEXPECTED_RESULT_TYPE_ERROR = "Unexpected result type from table extraction"
    PAGE_PROCESSING_ERROR = "Error processing page {page_num}: {error}"
    TEXT_EXTRACTION_ERROR = "Error extracting text from page {page_num}: {error}"
    TABLE_CONTENT_READ_ERROR = "Could not read table content: {error}"
    TEXT_CONTENT_READ_ERROR = "Could not read text content: {error}"
    TABLE_EXTRACTION_FAILED_ERROR = "Table extraction failed: {error}"
    TEXT_EXTRACTION_FAILED_ERROR = "Text extraction failed: {error}"
    MULTIPAGE_TABLE_READ_WARNING = "Warning: Could not read multi-page table content: {error}"
    PROGRESS_DATA_LOAD_WARNING = "Warning: Could not load progress data: {error}"
    LOCAL_EXTRACTION_DATA_WARNING = "Warning: Could not load LOCAL_EXTRACTION data: {error}"

    # Status messages
    PROCESSING_FAILURE_MESSAGE = "Some pages failed processing"

    # File processing
    TEMP_FILE_CLEANUP_ENABLED = True


class PDFExtractionOrchestrator(BaseExtractor):
    """Orchestrates the extraction of text and tables from PDF pages."""

    def __init__(self):
        """
        Initialize the PDF extraction orchestrator.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        self.data_root: Path = get_loksabha_data_root()
        self.document_path: Optional[Path] = None
        self.progress_handler: Optional[DocumentProgressHandler] = None
        self.pdf_path: Optional[str] = None

        # Initialize components
        self.text_extractor = TextExtractor(self.data_root)
        self.table_extractor = TableExtractor(self.data_root)
        self.multi_page_handler = MultiPageTableHandler(self.data_root)
        self.page_splitter = PDFPageSplitter()
        self.range_detector = TableRangeDetector()
        self.result_combiner = ExtractionResultCombiner()

    def _combine_extraction_results(
        self,
        multi_page_results: Dict[PageIdentifier, TableResult],
        single_page_results: Dict[int, TableResult],
        text_results: Optional[Dict[int, ExtractionResult]] = None,
    ) -> CombinedResults:
        """
        Combines multi-page and single-page extraction results into a structured CombinedResults object.

        Args:
            multi_page_results: Dictionary of results from multi-page table processing
            single_page_results: Dictionary of results from single-page processing
            multi_page_summary: Optional summary from multi-page table extraction (deprecated)
            text_results: Optional dictionary of text extraction results

        Returns:
            CombinedResults object containing all extraction results
        """
        # Create CombinedResults object with all results
        combined_results = CombinedResults(
            pages_processed=len(multi_page_results) + len(single_page_results),
            table_results={**multi_page_results, **single_page_results},  # Merge both result dictionaries
            summary=ExtractionSummary(
                total_tables=0, successful_tables=0, failed_tables=0, multi_page_tables=0, single_page_tables=0
            ),
            text_results=text_results or {},
        )

        # Update summary
        combined_results.summary = self.result_combiner.create_summary(combined_results.table_results)

        return combined_results

    def _extract_text_for_all_pages(
        self, pdf_path: str, page_numbers: List[int], output_folder_path: Path
    ) -> Dict[int, ExtractionResult]:
        """
        Extract text from all pages, including those with multi-page tables.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to process
            output_folder_path: Path to save extracted content

        Returns:
            Dictionary mapping page numbers to their text extraction results
        """
        text_results: Dict[int, ExtractionResult] = {}
        for page_num in page_numbers:
            try:
                # Create temporary PDF for this page
                temp_pdf = self.page_splitter.split_pages(pdf_path, [page_num], output_folder_path)
                if not temp_pdf:
                    error_msg = ExtractionConfig.FAILED_PDF_CREATION_ERROR.format(page_num=page_num)
                    text_results[page_num] = ExtractionResult(
                        status="error",
                        error=error_msg,
                    )
                    continue

                # Extract text
                text_result = self.text_extractor.extract_text(temp_pdf, page_num, output_folder_path)
                text_results[page_num] = text_result

            except Exception as e:
                error_msg = ExtractionConfig.TEXT_EXTRACTION_ERROR.format(page_num=page_num, error=str(e))
                text_results[page_num] = ExtractionResult(
                    status="error",
                    error=error_msg,
                )
            finally:
                # Clean up temporary file
                if ExtractionConfig.TEMP_FILE_CLEANUP_ENABLED and temp_pdf and Path(temp_pdf).exists():
                    Path(temp_pdf).unlink()

        return text_results

    def _get_pages_with_multiple_tables(self, document_path: Path) -> Dict[int, List[dict]]:
        """
        Get information about pages that have multiple tables from the progress file.

        Args:
            document_path: Path to the document directory

        Returns:
            Dictionary mapping page numbers to their table information, but only for pages with multiple tables
        """
        pages_with_multiple_tables: Dict[int, List[dict]] = {}

        try:
            # Get tables info from LOCAL_EXTRACTION state
            local_extraction_data = self.progress_handler.get_local_extraction_data()

            if local_extraction_data and local_extraction_data.table_metadata:
                # Group tables by page from metadata
                page_tables: Dict[int, List[dict]] = {}
                for table in local_extraction_data.table_metadata:
                    page = table.page
                    if page not in page_tables:
                        page_tables[page] = []
                    page_tables[page].append(table.model_dump())

                # Keep only pages with multiple tables
                pages_with_multiple_tables = {page: tables for page, tables in page_tables.items() if len(tables) > 1}

        except Exception as e:
            print(ExtractionConfig.PROGRESS_DATA_LOAD_WARNING.format(error=str(e)))

        return pages_with_multiple_tables

    def _setup_output_folder(self) -> Path:
        """
        Creates and returns the output folder path.

        Returns:
            Path to the output folder
        """
        # Create output folder next to the PDF
        output_folder = self.document_path / ExtractionConfig.TABLE_EXTRACTION_FOLDER

        # Use base class method to ensure folder exists
        return self._ensure_output_folder(output_folder)

    def _process_single_page(
        self, pdf_path: str, page_num: int, output_folder_path: Path, num_tables: int
    ) -> SinglePageTableResult:
        """
        Process a single page for table extraction.

        Args:
            pdf_path: Path to the input PDF file
            page_num: Page number to process
            output_folder_path: Path to save extracted content
            num_tables: Number of tables on the page

        Returns:
            SinglePageTableResult containing the table extraction results
        """
        temp_pdf = None
        try:
            temp_pdf = self.page_splitter.split_pages(pdf_path, [page_num], output_folder_path)
            if not temp_pdf:
                error_msg = ExtractionConfig.FAILED_PDF_CREATION_ERROR.format(page_num=page_num)
                return SinglePageTableResult(
                    status="error",
                    error=error_msg,
                    page_number=page_num,
                )

            # Extract tables
            table_result = self.table_extractor.extract_tables(temp_pdf, page_num, output_folder_path, num_tables)
            if isinstance(table_result, SinglePageTableResult):
                return table_result

            # If we got a different type of result (which shouldn't happen), return an error
            return SinglePageTableResult(
                status="error",
                error=ExtractionConfig.UNEXPECTED_RESULT_TYPE_ERROR,
                page_number=page_num,
            )

        except Exception as e:
            error_msg = ExtractionConfig.PAGE_PROCESSING_ERROR.format(page_num=page_num, error=str(e))
            return SinglePageTableResult(
                status="error",
                error=error_msg,
                page_number=page_num,
            )
        finally:
            # Clean up temporary file
            if ExtractionConfig.TEMP_FILE_CLEANUP_ENABLED and temp_pdf and Path(temp_pdf).exists():
                Path(temp_pdf).unlink()

    def _get_local_extraction_reference(self) -> Optional[LocalExtractionData]:
        """Get existing local extraction data for reference (but don't copy incompatible types)."""
        local_extraction_data = None
        try:
            local_extraction_data = self.progress_handler.get_local_extraction_data()
        except Exception as e:
            print(ExtractionConfig.LOCAL_EXTRACTION_DATA_WARNING.format(error=str(e)))
        return local_extraction_data

    def _read_extraction_file(self, file_path: str, read_as_json: bool = False) -> tuple[Any, List[str]]:
        """
        Generic helper to read extraction files with error handling.

        Args:
            file_path: Path to the file to read
            read_as_json: Whether to parse the file as JSON

        Returns:
            Tuple of (content, errors) where content is the parsed content and errors is a list of error messages
        """
        errors: List[str] = []
        content = None

        try:
            file_obj = Path(file_path)
            if not file_obj.is_absolute():
                file_obj = self.data_root / file_obj

            with open(file_obj, "r") as f:
                if read_as_json:
                    content = json.load(f)
                else:
                    content = f.read()

        except Exception as e:
            error_msg = (
                ExtractionConfig.TABLE_CONTENT_READ_ERROR.format(error=str(e))
                if read_as_json
                else ExtractionConfig.TEXT_CONTENT_READ_ERROR.format(error=str(e))
            )
            errors.append(error_msg)

        return content, errors

    def _process_table_content(self, table_result) -> tuple[List[Dict[str, Any]], Optional[str], List[str]]:
        """Process table content and return tables, filename, and any errors."""
        tables: List[Dict[str, Any]] = []
        table_file_name: Optional[str] = None
        errors: List[str] = []

        if table_result and table_result.status == "success":
            table_file_name = table_result.output_file
            content, file_errors = self._read_extraction_file(table_result.output_file, read_as_json=True)
            errors.extend(file_errors)

            if content is not None:
                tables = content if isinstance(content, list) else content.get("tables", [])

        elif table_result:
            errors.append(ExtractionConfig.TABLE_EXTRACTION_FAILED_ERROR.format(error=table_result.error))

        return tables, table_file_name, errors

    def _process_text_content(self, text_result) -> tuple[str, Optional[str], List[str]]:
        """Process text content and return text, filename, and any errors."""
        text = ""
        text_file_name: Optional[str] = None
        errors: List[str] = []

        if text_result and text_result.status == "success":
            text_file_name = text_result.output_file
            content, file_errors = self._read_extraction_file(text_result.output_file, read_as_json=False)
            errors.extend(file_errors)

            if content is not None:
                text = content

        elif text_result:
            errors.append(ExtractionConfig.TEXT_EXTRACTION_FAILED_ERROR.format(error=text_result.error))

        return text, text_file_name, errors

    def _create_single_page_data(self, page_num: int, combined_results: CombinedResults) -> LlmExtractionPageData:
        """Create LlmExtractionPageData for a single page with tables or errors."""
        # Get table results for this page
        table_result = next((t for t in combined_results.single_page_tables if t.page_number == page_num), None)

        # Get text result for this page
        text_result = combined_results.text_results.get(page_num)

        # Process table content
        tables, table_file_name, table_errors = self._process_table_content(table_result)

        # Process text content
        text, text_file_name, text_errors = self._process_text_content(text_result)

        # Combine all errors
        all_errors = table_errors + text_errors

        return LlmExtractionPageData(
            has_tables=len(tables) > 0,
            num_tables=len(tables),
            text=text,
            tables=tables,
            errors=all_errors,
            has_multi_page_tables=page_num in combined_results.pages_with_multi_page_tables,
            has_multiple_tables=(table_result.tables_count or 0) > 1,  # Handle Optional[int] safely
            table_file_name=table_file_name,
            text_file_name=text_file_name,
        )

    def _process_multipage_tables(
        self, combined_results: CombinedResults, local_extraction_data
    ) -> tuple[Dict[int, LlmExtractionPageData], Dict[str, List[int]]]:
        """Process multi-page table information and return updated pages and file tracking."""
        typed_pages: Dict[int, LlmExtractionPageData] = {}
        multi_page_table_files: Dict[str, List[int]] = {}

        for table in combined_results.multi_page_tables:
            # Read multi-page table content
            table_data: List[Dict[str, Any]] = []
            content, file_errors = self._read_extraction_file(table.output_file, read_as_json=True)

            if content is not None:
                table_data = content.get("tables", [])
                # Track multi-page table files
                multi_page_table_files[table.output_file] = table.pages
            elif file_errors:
                # Print the first error message (our helper returns standardized error messages)
                print(ExtractionConfig.MULTIPAGE_TABLE_READ_WARNING.format(error=file_errors[0]))

            for page_num in table.pages:
                # Get text from local extraction data if available
                page_text = ""
                if local_extraction_data and page_num in local_extraction_data.pages:
                    page_text = local_extraction_data.pages[page_num].text

                # Create page data for pages with multi-page tables
                typed_pages[page_num] = LlmExtractionPageData(
                    has_tables=True,
                    num_tables=len(table_data),
                    text=page_text,  # Use text from local extraction if available
                    tables=table_data,
                    errors=[],  # Empty list, not None
                    has_multi_page_tables=True,
                    has_multiple_tables=False,  # Multi-page table is one table across pages
                    table_file_name=table.output_file,
                    text_file_name=None,
                )

        return typed_pages, multi_page_table_files

    def _create_processing_metadata(
        self, typed_pages: Dict[int, LlmExtractionPageData], processing_time_seconds: float
    ) -> ProcessingMetadata:
        """Create ProcessingMetadata from the processed pages.

        Args:
            typed_pages: Dictionary of processed page data
            processing_time_seconds: Actual time taken for processing in seconds
        """
        return ProcessingMetadata(
            processing_time_seconds=processing_time_seconds,
            pages_processed=len(typed_pages),
            pages_failed=len([p for p in typed_pages.values() if p.errors]),  # Count pages with non-empty error lists
            llm_model_used=None,
            reviewer=None,
        )

    def _prepare_step_data(
        self, combined_results: CombinedResults, processing_time_seconds: float
    ) -> LlmExtractionData:
        """Prepare step data as LlmExtractionData for state transition.

        This method orchestrates the creation of LlmExtractionData by:
        1. Getting reference data from LOCAL_EXTRACTION state
        2. Processing pages with tables or errors
        3. Processing multi-page table data
        4. Creating metadata and assembling the final result

        Args:
            combined_results: Combined extraction results from all processing steps
            processing_time_seconds: Actual time taken for processing in seconds
        """
        # Initialize typed pages dictionary
        typed_pages: Dict[int, LlmExtractionPageData] = {}

        # Get existing local extraction data for reference
        local_extraction_data = self._get_local_extraction_reference()

        # Process pages with tables or errors
        for page_num in combined_results.pages_with_tables | combined_results.pages_with_errors:
            typed_pages[page_num] = self._create_single_page_data(page_num, combined_results)

        # Process multi-page table information
        multipage_pages, multi_page_table_files = self._process_multipage_tables(
            combined_results, local_extraction_data
        )

        # Merge multi-page results (they take precedence over single-page results)
        typed_pages.update(multipage_pages)

        # Create processing metadata
        processing_metadata = self._create_processing_metadata(typed_pages, processing_time_seconds)

        # Create and return LlmExtractionData
        return LlmExtractionData(
            status=ProcessingStatus.SUCCESS if not combined_results.pages_with_errors else ProcessingStatus.FAILED,
            timestamp=datetime.now(UTC),
            processing_metadata=processing_metadata,
            pages=typed_pages,
            extracted_text_path=str(self.document_path / ExtractionConfig.EXTRACTED_TEXT_FILENAME),
            extracted_tables_path=str(self.document_path / ExtractionConfig.TABLE_EXTRACTION_FOLDER),
            error_message=None
            if not combined_results.pages_with_errors
            else ExtractionConfig.PROCESSING_FAILURE_MESSAGE,
            total_tables=combined_results.summary.total_tables,
            successful_tables=combined_results.summary.successful_tables,
            failed_tables=combined_results.summary.failed_tables,
            multi_page_tables=combined_results.summary.multi_page_tables,
            single_page_tables=combined_results.summary.single_page_tables,
            multi_page_table_files=multi_page_table_files,
        )

    def _initialize_extraction(self, pdf_path: str) -> Path:
        """Initialize extraction setup including document path, progress handler, and output folder.

        Args:
            pdf_path: Path to the input PDF file

        Returns:
            Path to the output folder for extraction results
        """
        self.document_path = Path(pdf_path).parent

        # Initialize the progress handler for this document
        self.progress_handler = DocumentProgressHandler(self.document_path)

        # Setup output folder
        return self._setup_output_folder()

    def _process_table_extraction(
        self, page_numbers: List[int], output_folder_path: Path, tables_info: Dict[int, List[dict]]
    ) -> tuple[Dict[PageIdentifier, TableResult], Dict[int, TableResult]]:
        """Process table extraction for both multi-page and single-page tables.

        Args:
            page_numbers: List of page numbers to process
            output_folder_path: Path to save extracted content
            tables_info: Information about pages with multiple tables

        Returns:
            Tuple of (multi_page_results, single_page_results)
        """
        # Analyze page ranges using TableRangeDetector
        continuous_ranges = self.range_detector.detect_ranges(page_numbers)

        # Process multi-page tables
        if continuous_ranges:
            multi_page_extraction_results = self.multi_page_handler.process_continuous_ranges(
                self.pdf_path, continuous_ranges, output_folder_path
            )
            multi_page_results = multi_page_extraction_results.results
            # Get pages that need single-page processing
            pending_pages = list(multi_page_extraction_results.pages_without_multi_page_tables)
        else:
            multi_page_results: Dict[PageIdentifier, TableResult] = {}
            pending_pages = []

        # Add pages that were never part of continuous ranges
        pending_pages.extend(self.range_detector.get_single_pages(page_numbers, continuous_ranges))

        # Process single pages
        single_page_results: Dict[int, TableResult] = {}
        for page_num in pending_pages:
            # If page has multiple tables, pass the count, otherwise use default
            num_tables = (
                len(tables_info.get(page_num, []))
                if page_num in tables_info
                else ExtractionConfig.DEFAULT_NUM_TABLES_PER_PAGE
            )
            single_page_results[page_num] = self._process_single_page(
                self.pdf_path, page_num, output_folder_path, num_tables
            )

        return multi_page_results, single_page_results

    def _finalize_extraction(
        self,
        multi_page_results: Dict[PageIdentifier, TableResult],
        single_page_results: Dict[int, TableResult],
        text_results: Dict[int, ExtractionResult],
        processing_time_seconds: float,
    ) -> None:
        """Finalize extraction by combining results and transitioning to LLM_EXTRACTION state.

        Args:
            multi_page_results: Results from multi-page table processing
            single_page_results: Results from single-page processing
            text_results: Results from text extraction
            processing_time_seconds: Actual time taken for processing in seconds
        """
        # Combine all results
        combined_results = self._combine_extraction_results(multi_page_results, single_page_results, text_results)

        # Prepare and transition to LLM_EXTRACTION state
        step_data = self._prepare_step_data(combined_results, processing_time_seconds)
        self.progress_handler.transition_to_llm_extraction(step_data)

    def extract_and_save_content(self, pdf_path: str, page_numbers: List[int]) -> str:
        """
        Main entry point to extract and save text and table content from selected pages of a PDF.

        This method orchestrates the complete extraction workflow:
        1. Initialize extraction setup
        2. Load existing progress data
        3. Process table extraction (multi-page and single-page)
        4. Extract text content from all pages
        5. Finalize by combining results and transitioning state

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract content from (1-based indexing)

        Returns:
            Path to the folder containing the extracted content
        """
        # Start timing the extraction process
        start_time = time.time()

        # Store pdf_path for use in helper methods
        self.pdf_path = pdf_path

        # 1. Initialize extraction setup
        output_folder_path = self._initialize_extraction(pdf_path)

        # 2. Load existing progress data
        tables_info = self._get_pages_with_multiple_tables(self.document_path)

        # 3. Process table extraction
        multi_page_results, single_page_results = self._process_table_extraction(
            page_numbers, output_folder_path, tables_info
        )

        # 4. Extract text content
        text_results = self._extract_text_for_all_pages(pdf_path, page_numbers, output_folder_path)

        # Calculate total processing time
        processing_time_seconds = time.time() - start_time

        # 5. Finalize extraction with actual timing
        self._finalize_extraction(multi_page_results, single_page_results, text_results, processing_time_seconds)

        return str(self.document_path)
