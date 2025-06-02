from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from apps.py.documents.models import (
    CombinedResults,
    ExtractionResult,
    ExtractionSummary,
    SinglePageTableResult,
)
from apps.py.documents.utils.progress_handler import ProgressHandler
from apps.py.utils.project_root import get_loksabha_data_root

from .base import BaseExtractor
from .page_splitter import PDFPageSplitter
from .result_combiner import ExtractionResultCombiner
from .result_saver import ExtractionResultSaver
from .table import MultiPageTableHandler, TableExtractor
from .table_range_detector import TableRangeDetector
from .text import TextExtractor


class PDFExtractionOrchestrator(BaseExtractor):
    """Orchestrates the extraction of text and tables from PDF pages."""

    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize the PDF extraction orchestrator.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        self.data_root = data_root or get_loksabha_data_root()

        # Initialize components
        self.text_extractor = TextExtractor(data_root)
        self.table_extractor = TableExtractor(data_root)
        self.multi_page_handler = MultiPageTableHandler(data_root)
        self.page_splitter = PDFPageSplitter()
        self.range_detector = TableRangeDetector()
        self.result_combiner = ExtractionResultCombiner()
        self.result_saver = ExtractionResultSaver(data_root)
        self.progress_handler = ProgressHandler(data_root)

    def _combine_extraction_results(
        self,
        multi_page_results: Dict,
        single_page_results: Dict,
        multi_page_summary: Optional[ExtractionSummary] = None,
        text_results: Optional[Dict[int, ExtractionResult]] = None,
    ) -> CombinedResults:
        """
        Combines multi-page and single-page extraction results into a structured CombinedResults object.

        Args:
            multi_page_results: Dictionary of results from multi-page table processing
            single_page_results: Dictionary of results from single-page processing
            multi_page_summary: Optional summary from multi-page table extraction
            text_results: Optional dictionary of text extraction results

        Returns:
            CombinedResults object containing all extraction results
        """
        # Create CombinedResults object with all results
        combined_results = CombinedResults(
            pages_processed=len(multi_page_results),
            results=multi_page_results,
            summary=multi_page_summary or ExtractionSummary(total_tables=0, successful_tables=0, failed_tables=0),
        )

        # Add single page results
        for page_num, result in single_page_results.items():
            if page_num not in combined_results.pages_with_multi_page_tables:
                combined_results.results[page_num] = result
                if result.status == "success":
                    combined_results.single_page_tables.append(result)
                    combined_results.pages_with_single_page_tables.add(page_num)
                    combined_results.pages_with_tables.add(page_num)
                elif result.status == "error":
                    combined_results.errors[page_num] = result.error
                    combined_results.pages_with_errors.add(page_num)

        # Add text results
        if text_results:
            combined_results.text_results = text_results

        # Update summary
        combined_results.summary = self.result_combiner.create_summary(combined_results.results, multi_page_summary)

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
        """
        Prepare step data for progress tracking.

        Args:
            combined_results: Combined results from extraction

        Returns:
            Dictionary containing step data
        """
        return {
            "step": "tables_extraction",
            "timestamp": datetime.now().isoformat(),
            "status": "success" if not combined_results.pages_with_errors else "error",
            "data": {
                "multi_page_tables": [
                    {
                        "table_number": table.table_number,
                        "pages": table.pages,
                        "page_range": table.page_range,
                        "confidence": table.confidence,
                        "output_file": table.output_file,
                        "num_rows": table.num_rows,
                        "num_columns": table.num_columns,
                    }
                    for table in combined_results.multi_page_tables
                ],
                "single_page_tables": [
                    {
                        "table_number": table.table_number,
                        "page": table.page_number,
                        "output_file": table.output_file,
                        "num_rows": table.num_rows,
                        "num_columns": table.num_columns,
                    }
                    for table in combined_results.single_page_tables
                ],
                "text_results": [
                    {
                        "page": page_num,
                        "output_file": result.output_file,
                        "status": result.status,
                        "error": result.error,
                    }
                    for page_num, result in combined_results.text_results.items()
                ],
                "summary": {
                    "total_tables": combined_results.summary.total_tables,
                    "successful_tables": combined_results.summary.successful_tables,
                    "failed_tables": combined_results.summary.failed_tables,
                    "multi_page_tables": combined_results.summary.multi_page_tables,
                    "single_page_tables": combined_results.summary.single_page_tables,
                },
                "errors": combined_results.errors,
            },
        }

    def extract_and_save_content(
        self, pdf_path: str, page_numbers: List[int], output_folder: Optional[str] = None
    ) -> str:
        """
        Main entry point to extract and save text and table content from selected pages of a PDF.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract content from (1-based indexing)
            output_folder: Folder to save extracted content (if None, creates a folder next to PDF)

        Returns:
            Path to the folder containing the extracted content
        """
        # 1. Setup output folder
        output_folder_path = self._setup_output_folder(pdf_path, output_folder)

        # 2. Analyze page ranges using TableRangeDetector
        continuous_ranges = self.range_detector.detect_ranges(page_numbers)

        # 3. Process multi-page tables
        multi_page_results, multi_page_summary = self._process_multi_page_tables(
            pdf_path, continuous_ranges, output_folder_path
        )

        # 4. Get single pages using TableRangeDetector
        single_pages = self.range_detector.get_single_pages(page_numbers, continuous_ranges)

        # 5. add single_page_results to pending pages from multi_page_results
        single_page_results = {}
        # Get pages marked as "pending" from multi-page results
        pending_pages = [
            page_num
            for page_num, result in multi_page_results.items()
            if isinstance(result, SinglePageTableResult) and result.status == "pending"
        ]
        # Add any pages that weren't part of continuous ranges
        pending_pages.extend(single_pages)

        for page_num in pending_pages:
            single_page_results[page_num] = self._process_single_page(pdf_path, page_num, output_folder_path)

        # 6. Extract text from all pages
        text_results = self._extract_text_for_all_pages(pdf_path, page_numbers, output_folder_path)

        # 7. Combine all results
        combined_results = self._combine_extraction_results(
            multi_page_results, single_page_results, multi_page_summary, text_results
        )

        # 8. Prepare and save step data
        step_data = self._prepare_step_data(combined_results)
        self.progress_handler.append_step(output_folder_path / "progress.json", step_data)

        return str(output_folder_path)

    def _setup_output_folder(self, pdf_path: str, output_folder: Optional[str] = None) -> Path:
        """
        Creates and returns the output folder path.

        Args:
            pdf_path: Path to the input PDF file
            output_folder: Optional output folder path

        Returns:
            Path to the output folder
        """
        pdf_path = Path(pdf_path)

        # If no output folder specified, create one next to the PDF
        if output_folder is None:
            output_folder = pdf_path.parent / "table_extraction"
        else:
            output_folder = Path(output_folder)

        # Use base class method to ensure folder exists
        return self._ensure_output_folder(output_folder)

    def _process_multi_page_tables(
        self, pdf_path: str, continuous_ranges: List[Tuple[int, int]], output_folder_path: Path
    ) -> Tuple[Dict, Optional[ExtractionSummary]]:
        """
        Process multi-page tables from continuous page ranges.

        Args:
            pdf_path: Path to the input PDF file
            continuous_ranges: List of continuous page ranges to process
            output_folder_path: Path to save extracted content

        Returns:
            Tuple of (multi_page_results dictionary, optional multi_page_summary)
        """
        multi_page_results = {}
        multi_page_summary = None
        try:
            multi_page_extraction_results = self.multi_page_handler.process_continuous_ranges(
                pdf_path, continuous_ranges, output_folder_path
            )
            multi_page_results = multi_page_extraction_results.results
            multi_page_summary = multi_page_extraction_results.summary
        except RuntimeError as e:
            error_msg = f"Error processing multi-page tables: {str(e)}"
            # Mark all pages in continuous ranges for single-page processing
            for start_page, end_page in continuous_ranges:
                for page_num in range(start_page, end_page + 1):
                    multi_page_results[page_num] = SinglePageTableResult(
                        status="error",
                        error=error_msg,
                        page_number=page_num,
                    )
        return multi_page_results, multi_page_summary

    def _process_single_page(
        self, pdf_path: str, page_num: int, output_folder_path: Path
    ) -> Union[SinglePageTableResult, CombinedResults]:
        """
        Process a single page for text and table extraction.

        Args:
            pdf_path: Path to the input PDF file
            page_num: Page number to process
            output_folder_path: Path to save extracted content

        Returns:
            Combined results from text and table extraction, or error result
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

            # Extract text
            text_result = self.text_extractor.extract_text(temp_pdf, page_num, output_folder_path)
            # Extract tables
            table_result = self.table_extractor.extract_tables(temp_pdf, page_num, output_folder_path)

            # Combine results
            if isinstance(table_result, SinglePageTableResult):
                # If table extraction was successful, use its dimensions
                if table_result.status == "success":
                    return table_result
                # If table extraction failed, return error result
                return table_result

            # If we got a different type of result, combine with text
            text_results = {page_num: text_result} if text_result else {}
            return self.result_combiner.combine_results(
                single_page_results={page_num: table_result}, multi_page_results={}, text_results=text_results
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
