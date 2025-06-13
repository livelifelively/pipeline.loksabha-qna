from typing import Dict, Optional

from apps.py.types import (
    CombinedResults,
    ExtractionResult,
    ExtractionSummary,
    MultiPageTableResult,
    PageIdentifier,
    SinglePageTableResult,
    TableResult,
)


class ExtractionResultCombiner:
    """Combines results from different extraction processes."""

    def combine_results(
        self,
        single_page_results: Dict[PageIdentifier, TableResult],
        multi_page_results: Dict[PageIdentifier, TableResult],
        text_results: Optional[Dict[int, ExtractionResult]] = None,
    ) -> CombinedResults:
        """
        Combines single-page and multi-page extraction results.

        Args:
            single_page_results: Results from single-page extractions
            multi_page_results: Results from multi-page table extractions
            text_results: Optional dictionary of text extraction results

        Returns:
            CombinedResults object containing all extraction results
        """
        # Combine all results
        all_results = {**single_page_results, **multi_page_results}

        # Create summary
        summary = self.create_summary(all_results)

        return CombinedResults(
            pages_processed=len(all_results),
            table_results=all_results,
            summary=summary,
            text_results=text_results or {},
        )

    def create_summary(self, results: Dict[PageIdentifier, TableResult]) -> ExtractionSummary:
        """
        Creates summary statistics from results.

        Args:
            results: Dictionary of extraction results

        Returns:
            ExtractionSummary object with statistics
        """
        total_tables = 0
        successful_tables = 0
        failed_tables = 0
        multi_page_tables = 0
        single_page_tables = 0

        # Count tables from results
        for result in results.values():
            if isinstance(result, (SinglePageTableResult, MultiPageTableResult)):
                if result.tables_count:
                    total_tables += result.tables_count
                    if isinstance(result, MultiPageTableResult):
                        multi_page_tables += result.tables_count
                    else:
                        single_page_tables += result.tables_count
                if result.status == "success":
                    successful_tables += result.tables_count or 0
                else:
                    failed_tables += result.tables_count or 0

        return ExtractionSummary(
            total_tables=total_tables,
            successful_tables=successful_tables,
            failed_tables=failed_tables,
            multi_page_tables=multi_page_tables,
            single_page_tables=single_page_tables,
        )
