import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from apps.py.types import (
    ExtractionResult,
    MultiPageTableExtractionResults,
    MultiPageTableInfo,
    MultiPageTableResult,
    SinglePageTableResult,
    TableDetectionResult,
    TableSummary,
)
from apps.py.utils.gemini_api import (
    detect_multi_page_tables,
    extract_multi_page_table,
    extract_multiple_tables_from_pdf_page,
    extract_tables_from_pdf_page,
)

from .base import BaseExtractor
from .page_splitter import PDFPageSplitter


class BaseTableExtractor(BaseExtractor):
    """Base class for table extraction functionality."""

    def _save_table_result(self, content: Dict, output_file: Path) -> str:
        """
        Save table content to a JSON file and return relative path.

        Args:
            content: Table content to save
            output_file: Path to save the file

        Returns:
            Relative path to the saved file
        """
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
        try:
            rel_path = output_file.relative_to(self.data_root)
            return str(rel_path)
        except ValueError:
            return str(output_file)

    def _get_tables_count(self, content: Dict) -> int:
        """
        Get the number of tables from content.

        Args:
            content: Table content dictionary

        Returns:
            Number of tables
        """
        return len(content) if isinstance(content, list) else len(content.get("tables", []))


class TableExtractor(BaseTableExtractor):
    """Extractor for tables from PDF pages."""

    def extract_tables(
        self, page_file: Path, page_num: int, output_folder: Optional[Path] = None, num_tables: int = 1
    ) -> ExtractionResult:
        """
        Extract tables from a single-page PDF file and save as JSON.
        Args:
            page_file: Path to the single-page PDF file.
            page_num: Page number (for naming output).
            output_folder: Where to save the extracted tables file.
            num_tables: Number of tables expected on this page (default: 1)
        Returns:
            ExtractionResult with status and output details
        """
        output_folder = output_folder or page_file.parent
        self._ensure_output_folder(output_folder)

        # Choose extraction strategy based on number of tables
        if num_tables > 1:
            # Use multi-table extraction for pages with multiple tables
            table_result = extract_multiple_tables_from_pdf_page(str(page_file), num_tables)
        else:
            # Use single table extraction for pages with one table
            table_result = extract_tables_from_pdf_page(str(page_file))

        if table_result["status"] == "success":
            output_json = output_folder / f"page_{page_num}_tables.json"
            content = table_result["content"]
            relative_path = self._save_table_result(content, output_json)
            tables_count = num_tables  # Use the known number of tables

            # Get dimensions for all tables
            try:
                if num_tables > 1:
                    # Multiple tables: content has 'tables' key with array of tables
                    tables = content.get("tables", [])
                    table_dimensions = [{"num_rows": len(table)} for table in tables]
                else:
                    # Single table: content is the array of row objects
                    table_dimensions = [{"num_rows": len(content)}]
            except Exception as e:
                print(f"Warning: Could not get table dimensions: {e}")
                table_dimensions = [{"num_rows": 0} for _ in range(num_tables)]

            return SinglePageTableResult(
                status="success",
                output_file=relative_path,
                tables_count=tables_count,
                page_number=page_num,
                table_dimensions=table_dimensions,
            )
        else:
            return SinglePageTableResult(
                status="error",
                error=table_result.get("error", "Unknown error"),
                page_number=page_num,
            )


class MultiPageTableHandler(BaseTableExtractor):
    """Handler for extracting tables that span across multiple pages.

    TODO (Future Improvements):
    1. Reliability:
       - Add retry mechanism for API calls with exponential backoff
       - Add proper logging system instead of print statements
       - Add detailed logging for each step (detection, extraction)

    2. Performance:
       - Add progress tracking for long-running operations
       - Optimize memory usage for large PDFs
       - Add support for parallel processing of multiple ranges
       - Add caching for intermediate results

    3. Monitoring:
       - Add metrics collection for success/failure rates
       - Add monitoring for API call success rates
       - Add processing time tracking
    """

    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize the multi-page table handler.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        super().__init__(data_root)
        self.table_extractor = TableExtractor(data_root)
        self.page_splitter = PDFPageSplitter()

    def process_continuous_ranges(
        self, pdf_path: str, continuous_ranges: List[Tuple[int, int]], output_folder: Optional[Path] = None
    ) -> MultiPageTableExtractionResults:
        """
        Process all continuous ranges for multi-page tables.

        Args:
            pdf_path: Path to the PDF file
            continuous_ranges: List of continuous page ranges as (start, end) tuples
            output_folder: Where to save the extracted table files

        Returns:
            MultiPageTableExtractionResults containing all extraction results and summary

        Raises:
            RuntimeError: If PDF splitting fails for any range
        """
        results: Dict[Union[int, Tuple[int, int]], Union[SinglePageTableResult, MultiPageTableResult]] = {}
        total_tables = 0
        successful_tables = 0
        failed_tables = 0
        multi_page_tables = 0
        single_page_tables = 0

        for start_page, end_page in continuous_ranges:
            print(f"\nProcessing potential multi-page table on pages {start_page}-{end_page}")

            # Create temporary PDF for this range
            temp_pdf = self.page_splitter.split_pages(pdf_path, list(range(start_page, end_page + 1)), output_folder)
            if not temp_pdf:
                error_msg = f"Failed to create temporary PDF for range {start_page}-{end_page}"
                print(f"Error: {error_msg}")
                raise RuntimeError(error_msg)

            try:
                range_results = self._process_single_range(temp_pdf, start_page, end_page, output_folder)
                results.update(range_results)

                # Update summary statistics
                for result in range_results.values():
                    if isinstance(result, (SinglePageTableResult, MultiPageTableResult)):
                        if result.tables_count:
                            total_tables += result.tables_count
                        if result.status == "success":
                            successful_tables += result.tables_count or 0
                        else:
                            failed_tables += result.tables_count or 0
                        if isinstance(result, MultiPageTableResult):
                            multi_page_tables += result.tables_count or 0
                        elif isinstance(result, SinglePageTableResult):
                            single_page_tables += result.tables_count or 0
            finally:
                # Clean up temporary file
                if temp_pdf and Path(temp_pdf).exists():
                    Path(temp_pdf).unlink()

        # Create TableSummary for MultiPageTableExtractionResults
        table_summary = TableSummary(
            total_tables=total_tables,
            successful_tables=successful_tables,
            failed_tables=failed_tables,
        )

        return MultiPageTableExtractionResults(
            pages_processed=len(results),
            results=results,
            summary=table_summary,
        )

    def _process_single_range(
        self, pdf_path: str, start_page: int, end_page: int, output_folder: Optional[Path]
    ) -> Dict[Union[int, Tuple[int, int]], Union[SinglePageTableResult, MultiPageTableResult]]:
        """
        Process a single continuous range of pages.

        Args:
            pdf_path: Path to the PDF file
            start_page: Start page number
            end_page: End page number
            output_folder: Where to save the extracted table files

        Returns:
            Dictionary mapping page numbers to their extraction results. Pages without multi-page tables
            are marked as "pending" for single-page processing.
        """
        # First detect if this range contains any multi-page tables
        table_detection = detect_multi_page_tables(pdf_path)

        if table_detection.status == "error":
            return self._mark_range_for_single_page(start_page, end_page, table_detection)

        results = {}
        # Track which pages have been processed as part of multi-page tables
        processed_pages = set()

        # Process each detected multi-page table
        if table_detection.multi_page_tables:
            for table_info in table_detection.multi_page_tables:
                table_pages = table_info.pages
                if not table_pages:  # Skip if no pages in this table
                    continue

                # Create a temporary PDF for this specific table
                temp_pdf = self.page_splitter.split_pages(pdf_path, table_pages, output_folder)
                if not temp_pdf:
                    error_msg = f"Failed to create temporary PDF for table on pages {table_pages}"
                    raise RuntimeError(error_msg)

                try:
                    # Extract and save this multi-page table
                    table_result = self._extract_and_save_multi_page_table(
                        temp_pdf,
                        min(table_pages),
                        max(table_pages),
                        output_folder,
                        table_info,
                    )
                    results.update(table_result)
                    processed_pages.update(table_pages)
                finally:
                    # Clean up temporary file
                    if temp_pdf and Path(temp_pdf).exists():
                        Path(temp_pdf).unlink()

        # Mark remaining pages for single-page processing
        remaining_pages = set(range(start_page, end_page + 1)) - processed_pages
        if remaining_pages:
            for page_num in sorted(remaining_pages):
                results[page_num] = SinglePageTableResult(
                    status="pending",
                    page_number=page_num,
                )

        return results

    def _mark_range_for_single_page(
        self, start_page: int, end_page: int, detection_result: TableDetectionResult
    ) -> Dict[Union[int, Tuple[int, int]], Union[SinglePageTableResult, MultiPageTableResult]]:
        """
        Mark all pages in a range for single-page processing.

        Args:
            start_page: Start page number
            end_page: End page number
            detection_result: Result from table detection

        Returns:
            Dictionary mapping page numbers to their results
        """
        results = {}
        for page_num in range(start_page, end_page + 1):
            results[page_num] = SinglePageTableResult(
                status=detection_result.status,
                error=detection_result.error,
                page_number=page_num,
            )
        return results

    def _extract_and_save_multi_page_table(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int,
        output_folder: Optional[Path],
        table_info: MultiPageTableInfo,
    ) -> Dict[Union[int, Tuple[int, int]], Union[SinglePageTableResult, MultiPageTableResult]]:
        """
        Extract and save a multi-page table.

        Args:
            pdf_path: Path to the PDF file
            start_page: Start page number
            end_page: End page number
            output_folder: Where to save the extracted table files
            table_info: Information about the multi-page table

        Returns:
            Dictionary mapping page numbers to their extraction results

        Raises:
            RuntimeError: If table extraction fails
        """
        extraction_result = extract_multi_page_table(pdf_path, (start_page, end_page))
        result = ExtractionResult(**extraction_result)

        if result.status == "success":
            # Create output file
            output_file = output_folder / f"multi_page_table_{start_page}_to_{end_page}.json"
            relative_path = self._save_table_result(extraction_result["content"], output_file)

            # Get table dimensions from content
            content = extraction_result["content"]
            try:
                tables = content.get("tables", [{}])
                table_dimensions = [{"num_rows": len(table.get("rows", []))} for table in tables]
            except Exception as e:
                print(f"Warning: Could not get table dimensions: {e}")
                table_dimensions = [{"num_rows": 0}]

            # Store successful extraction result
            multi_page_result = MultiPageTableResult(
                status="success",
                is_multi_page_table=True,
                confidence=table_info.confidence,
                output_file=relative_path,
                tables_count=1,
                pages=table_info.pages,
                page_range=(start_page, end_page),
                table_dimensions=table_dimensions,
            )
            return {(start_page, end_page): multi_page_result}

        # If extraction failed, raise an error
        error_msg = f"Failed to extract multi-page table from pages {start_page}-{end_page}: {result.error}"
        print(f"Error: {error_msg}")
        raise RuntimeError(error_msg)
