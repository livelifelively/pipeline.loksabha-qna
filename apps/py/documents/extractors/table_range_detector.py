from typing import List, Set


class TableRangeDetector:
    """Detects continuous ranges of pages that might contain tables."""

    def detect_ranges(self, page_numbers: List[int]) -> List[tuple[int, int]]:
        """
        Detects continuous page ranges.

        Args:
            page_numbers: List of page numbers to analyze

        Returns:
            List of tuples containing (start_page, end_page) for continuous ranges
            where start_page != end_page, indicating potential multi-page tables
        """
        if not page_numbers:
            return []

        # Sort page numbers to ensure continuous ranges
        sorted_pages = sorted(page_numbers)
        ranges = []
        start = sorted_pages[0]
        prev = start

        for page in sorted_pages[1:]:
            if page != prev + 1:
                # End of a range
                if start != prev:  # Only add ranges with multiple pages
                    ranges.append((start, prev))
                start = page
            prev = page

        # Add the last range if it has multiple pages
        if start != prev:
            ranges.append((start, prev))

        return ranges

    def get_single_pages(self, all_pages: List[int], continuous_ranges: List[tuple[int, int]]) -> List[int]:
        """
        Identify pages that are not part of any continuous range.

        Args:
            all_pages: List of all page numbers to process
            continuous_ranges: List of continuous page ranges as (start, end) tuples

        Returns:
            List of page numbers that are not part of any continuous range
        """
        # Create a set of all pages in continuous ranges
        pages_in_ranges: Set[int] = set()
        for start, end in continuous_ranges:
            pages_in_ranges.update(range(start, end + 1))

        # Return pages that are not in any range
