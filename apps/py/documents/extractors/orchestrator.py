import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from apps.py.documents.models import (
    CombinedResults,
    ExtractionResult,
    ExtractionSummary,
    PageIdentifier,
    SinglePageTableResult,
    TableResult,
)
from apps.py.documents.utils.progress_handler import ProgressHandler
from apps.py.utils.project_root import get_loksabha_data_root

from .base import BaseExtractor
from .page_splitter import PDFPageSplitter
from .result_combiner import ExtractionResultCombiner
from .table import MultiPageTableHandler, TableExtractor
from .table_range_detector import TableRangeDetector
from .text import TextExtractor


class PDFExtractionOrchestrator(BaseExtractor):
    """Orchestrates the extraction of text and tables from PDF pages."""

    def __init__(self):
        """
        Initialize the PDF extraction orchestrator.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        self.data_root = get_loksabha_data_root()
        self.document_path = None
        self.progress_handler = None

        # Initialize components
        self.text_extractor = TextExtractor(self.data_root)
        self.table_extractor = TableExtractor(self.data_root)
        self.multi_page_handler = MultiPageTableHandler(self.data_root)
        self.page_splitter = PDFPageSplitter()
        self.range_detector = TableRangeDetector()
        self.result_combiner = ExtractionResultCombiner()
        self.progress_handler = ProgressHandler(self.data_root)

    def _combine_extraction_results(
        self,
        multi_page_results: Dict[PageIdentifier, TableResult],
        single_page_results: Dict[PageIdentifier, TableResult],
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
        text_results = {}
        for page_num in page_numbers:
            try:
                # Create temporary PDF for this page
                temp_pdf = self.page_splitter.split_pages(pdf_path, [page_num], output_folder_path)
                if not temp_pdf:
                    error_msg = f"Failed to create temporary PDF for page {page_num}"
                    text_results[page_num] = ExtractionResult(
                        status="error",
                        error=error_msg,
                    )
                    continue

                # Extract text
                text_result = self.text_extractor.extract_text(temp_pdf, page_num, output_folder_path)
                text_results[page_num] = text_result

            except Exception as e:
                error_msg = f"Error extracting text from page {page_num}: {str(e)}"
                text_results[page_num] = ExtractionResult(
                    status="error",
                    error=error_msg,
                )
            finally:
                # Clean up temporary file
                if temp_pdf and Path(temp_pdf).exists():
                    Path(temp_pdf).unlink()

        return text_results

    def _prepare_step_data(self, combined_results: CombinedResults) -> dict:
        # Get base pages data from pdf_extraction step
        pages = {}
        try:
            # Get pages data from pdf_extraction step
            pdf_extraction_step = self.progress_handler.get_step_data(self.document_path, "pdf_extraction")
            if pdf_extraction_step and pdf_extraction_step["status"] == "success":
                pages = pdf_extraction_step["data"].get("pages", {})
        except Exception as e:
            print(f"Warning: Could not load pdf_extraction data: {e}")

        # Update pages that have tables
        for page_num in combined_results.pages_with_tables | combined_results.pages_with_errors:
            # Get table results for this page
            table_result = next((t for t in combined_results.single_page_tables if t.page_number == page_num), None)

            # Get text result for this page
            text_result = combined_results.text_results.get(page_num)

            # Determine page status
            status = "success"
            if page_num in combined_results.pages_with_errors:
                status = "error"

            # Build page data
            page_data = {
                "status": status,
                "has_multi_page_tables": page_num in combined_results.pages_with_multi_page_tables,
                "has_multiple_tables": table_result.tables_count > 1
                if table_result and table_result.tables_count
                else False,
            }

            # Add table information and content
            if table_result and table_result.status == "success":
                page_data["table_file_name"] = table_result.output_file
                # Read table content from file
                try:
                    table_file = Path(table_result.output_file)
                    if not table_file.is_absolute():
                        table_file = self.data_root / table_file
                    with open(table_file, "r") as f:
                        table_content = json.load(f)
                    # For single table, content is the array directly
                    # For multiple tables, content has a 'tables' key with array of tables
                    if isinstance(table_content, list):
                        page_data["tables"] = [table_content]
                    else:
                        page_data["tables"] = table_content.get("tables", [])
                except Exception as e:
                    print(f"Warning: Could not read table content for page {page_num}: {e}")

            # Add text information and content
            if text_result and text_result.status == "success":
                page_data["text_file_name"] = text_result.output_file
                # Read text content from file
                try:
                    text_file = Path(text_result.output_file)
                    if not text_file.is_absolute():
                        text_file = self.data_root / text_file
                    with open(text_file, "r") as f:
                        page_data["text"] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read text content for page {page_num}: {e}")

            # Add error information if any
            if status == "error":
                page_data["error"] = combined_results.errors.get(page_num)

            # Update the page data in the base pages dictionary
            pages[str(page_num)] = page_data

        # Add multi-page table information
        for table in combined_results.multi_page_tables:
            # Read multi-page table content
            try:
                table_file = Path(table.output_file)
                if not table_file.is_absolute():
                    table_file = self.data_root / table_file
                with open(table_file, "r") as f:
                    table_content = json.load(f)
                table_data = table_content.get("tables", [])
            except Exception as e:
                print(f"Warning: Could not read multi-page table content: {e}")
                table_data = []

            for page_num in table.pages:
                page_str = str(page_num)
                if page_str not in pages:
                    pages[page_str] = {
                        "status": "success",
                        "has_multi_page_tables": True,
                        "has_multiple_tables": False,
                        "tables": table_data,
                        "table_file_name": table.output_file,
                    }
                else:
                    pages[page_str]["table_file_name"] = table.output_file
                    pages[page_str]["tables"] = table_data
                    pages[page_str]["has_multi_page_tables"] = True

        return {
            "step": "tables_extraction",
            "timestamp": datetime.now().isoformat(),
            "status": "success" if not combined_results.pages_with_errors else "error",
            "pages": pages,
            # Summary statistics
            "total_tables": combined_results.summary.total_tables,
            "successful_tables": combined_results.summary.successful_tables,
            "failed_tables": combined_results.summary.failed_tables,
            "multi_page_tables": combined_results.summary.multi_page_tables,
            "single_page_tables": combined_results.summary.single_page_tables,
        }

    def _get_pages_with_multiple_tables(self, document_path: Path) -> Dict[int, List[dict]]:
        """
        Get information about pages that have multiple tables from the progress file.

        Args:
            document_path: Path to the document directory

        Returns:
            Dictionary mapping page numbers to their table information, but only for pages with multiple tables
        """
        pages_with_multiple_tables = {}

        try:
            # Get tables info from pdf_extraction step
            pdf_extraction_step = self.progress_handler.get_step_data(document_path, "pdf_extraction")

            if pdf_extraction_step and pdf_extraction_step["status"] == "success":
                tables_data = pdf_extraction_step["data"].get("tables_data", {})
                # Group tables by page
                page_tables = {}
                for table in tables_data.get("tables_summary", []):
                    page = table["page"]
                    if page not in page_tables:
                        page_tables[page] = []
                    page_tables[page].append(table)

                # Keep only pages with multiple tables
                pages_with_multiple_tables = {page: tables for page, tables in page_tables.items() if len(tables) > 1}

        except Exception as e:
            print(f"Warning: Could not load progress data: {e}")

        return pages_with_multiple_tables

    def _setup_output_folder(self) -> Path:
        """
        Creates and returns the output folder path.

        Returns:
            Path to the output folder
        """
        # Create output folder next to the PDF
        output_folder = self.document_path / "table_extraction"

        # Use base class method to ensure folder exists
        return self._ensure_output_folder(output_folder)

    def extract_and_save_content(self, pdf_path: str, page_numbers: List[int]) -> str:
        """
        Main entry point to extract and save text and table content from selected pages of a PDF.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract content from (1-based indexing)

        Returns:
            Path to the folder containing the extracted content
        """
        self.document_path = Path(pdf_path).parent

        # 1. Setup output folder
        output_folder_path = self._setup_output_folder()

        # Load existing progress data if available
        tables_info = self._get_pages_with_multiple_tables(self.document_path)

        # 2. Analyze page ranges using TableRangeDetector
        continuous_ranges = self.range_detector.detect_ranges(page_numbers)

        # 3. Process multi-page tables
        if continuous_ranges:
            multi_page_extraction_results = self.multi_page_handler.process_continuous_ranges(
                pdf_path, continuous_ranges, output_folder_path
            )
            multi_page_results = multi_page_extraction_results.results
            # Get pages that need single-page processing
            pending_pages = list(multi_page_extraction_results.pages_without_multi_page_tables)
        else:
            multi_page_results = {}
            pending_pages = []

        # Add pages that were never part of continuous ranges
        pending_pages.extend(self.range_detector.get_single_pages(page_numbers, continuous_ranges))

        # Process single pages
        single_page_results = {}
        for page_num in pending_pages:
            # If page has multiple tables, pass the count, otherwise default to 1
            num_tables = len(tables_info.get(page_num, [])) if page_num in tables_info else 1
            single_page_results[page_num] = self._process_single_page(
                pdf_path, page_num, output_folder_path, num_tables
            )

        # 6. Extract text from all pages
        text_results = self._extract_text_for_all_pages(pdf_path, page_numbers, output_folder_path)

        # 7. Combine all results
        combined_results = self._combine_extraction_results(multi_page_results, single_page_results, text_results)

        # 8. Prepare and save step data
        step_data = self._prepare_step_data(combined_results)
        self.progress_handler.append_step(step_data)

        return str(self.document_path)

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
                error_msg = f"Failed to create temporary PDF for page {page_num}"
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
                error="Unexpected result type from table extraction",
                page_number=page_num,
            )

        except Exception as e:
            error_msg = f"Error processing page {page_num}: {str(e)}"
            return SinglePageTableResult(
                status="error",
                error=error_msg,
                page_number=page_num,
            )
        finally:
            # Clean up temporary file
            if temp_pdf and Path(temp_pdf).exists():
                Path(temp_pdf).unlink()
