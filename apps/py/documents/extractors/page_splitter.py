from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfReader, PdfWriter


class PDFPageSplitter:
    """Handles splitting PDF files into individual pages."""

    def split_pages(self, pdf_path: str, page_numbers: List[int], output_folder: Path) -> str:
        """
        Splits specific pages from a PDF and saves them individually.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract (1-based indexing)
            output_folder: Folder to save individual pages

        Returns:
            Path to the folder containing the split pages
        """
        pdf_path = Path(pdf_path)
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        # Open the PDF file
        pdf = PdfReader(str(pdf_path))
        total_pages = len(pdf.pages)

        print(f"Processing '{pdf_path.name}' ({total_pages} pages)...")
        print(f"Extracting pages: {', '.join(map(str, page_numbers))}")

        # Validate and filter page numbers
        valid_page_numbers = self._validate_page_numbers(page_numbers, total_pages)

        # Process only the specified pages
        for page_number in valid_page_numbers:
            # Adjust for 0-based indexing
            page_index = page_number - 1

            # Create a writer for this page
            writer = PdfWriter()
            writer.add_page(pdf.pages[page_index])

            # Save the page to the output directory
            output_path = output_folder / f"page_{page_number}.pdf"
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            print(f"  ✓ Saved page {page_number} to {output_path.name}")

        print(f"Successfully saved {len(valid_page_numbers)} pages to folder: '{output_folder}'")
        return str(output_path)

    def _validate_page_numbers(self, page_numbers: List[int], total_pages: int) -> List[int]:
        """
        Validates and filters page numbers.

        Args:
            page_numbers: List of page numbers to validate
            total_pages: Total number of pages in the PDF

        Returns:
            List of valid page numbers
        """
        valid_pages = []
        for page_num in page_numbers:
            if 1 <= page_num <= total_pages:
                valid_pages.append(page_num)
            else:
                print(f"  ⚠ Warning: Page {page_num} is out of range (1-{total_pages})")
        return valid_pages

    def split_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int,
        output_folder: Optional[Path] = None,
        range_base: Optional[int] = None,
    ) -> Optional[str]:
        """
        Split a range of pages from a PDF into a single PDF file.

        Args:
            pdf_path: Path to the source PDF file
            start_page: Start page number (1-based)
            end_page: End page number (1-based)
            output_folder: Where to save the output PDF. If None, uses the same directory as the input.

        Returns:
            Path to the created PDF file, or None if splitting failed
        """
        new_start_page = start_page
        new_end_page = end_page

        if range_base is not None:
            new_start_page = start_page - range_base + 1
            new_end_page = end_page - range_base + 1

        try:
            # Create output folder if needed
            if output_folder:
                output_folder.mkdir(parents=True, exist_ok=True)
            else:
                output_folder = Path(pdf_path).parent

            # Create output filename
            output_file = output_folder / f"range_{start_page}_to_{end_page}.pdf"

            # Use PyPDF2 to extract the range
            with open(pdf_path, "rb") as file:
                reader = PdfReader(file)
                writer = PdfWriter()

                # Add all pages in the range
                for page_num in range(new_start_page - 1, new_end_page):  # Convert to 0-based index
                    if page_num < len(reader.pages):
                        writer.add_page(reader.pages[page_num])

                # Write the output file
                with open(output_file, "wb") as output:
                    writer.write(output)

            return str(output_file)

        except Exception as e:
            print(f"Error splitting range {start_page}-{end_page}: {str(e)}")
            return None
