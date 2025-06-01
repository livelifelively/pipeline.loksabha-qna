import json
from pathlib import Path
from typing import Dict, List, Optional

from PyPDF2 import PdfReader, PdfWriter

from apps.py.utils.gemini_api import extract_tables_from_pdf_page, extract_text_from_pdf_page
from apps.py.utils.project_root import get_loksabha_data_root


class PDFSelectedPagesTextTableExtractor:
    """Class to extract and save text and table content from selected pages of a PDF document."""

    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize the PDF page content extractor.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        self.data_root = data_root or get_loksabha_data_root()

    def extract_and_save_content(
        self, pdf_path: str, page_numbers: List[int], output_folder: Optional[str] = None
    ) -> str:
        """
        Main entry point to extract and save text and table content from selected pages of a PDF.
        This orchestrates the process of splitting pages and extracting their content.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract content from (1-based indexing)
            output_folder: Folder to save extracted content (if None, creates a folder next to PDF)

        Returns:
            Path to the folder containing the extracted content
        """
        # Split the PDF pages
        pages_folder = self._split_specific_pages(pdf_path, page_numbers, output_folder)

        # Process the pages to extract text and tables
        self._extract_page_contents(pages_folder, page_numbers)

        return pages_folder

    def _split_specific_pages(self, pdf_path: str, page_numbers: List[int], output_folder: Optional[str] = None) -> str:
        """
        Split specific pages from a PDF file and save them individually.

        Args:
            pdf_path: Path to the input PDF file
            page_numbers: List of page numbers to extract (1-based indexing)
            output_folder: Folder to save pages (if None, creates a folder next to PDF)

        Returns:
            Path to the folder containing the split pages
        """
        pdf_path = Path(pdf_path)

        # If no output folder specified, create one next to the PDF
        if output_folder is None:
            output_folder = pdf_path.parent / "pages"

        # Create output folder if it doesn't exist
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        # Open the PDF file
        pdf = PdfReader(str(pdf_path))
        total_pages = len(pdf.pages)

        print(f"Processing '{pdf_path.name}' ({total_pages} pages)...")
        print(f"Extracting pages: {', '.join(map(str, page_numbers))}")

        # Process only the specified pages
        for page_number in page_numbers:
            # Adjust for 0-based indexing
            page_index = page_number - 1 if page_number > 0 else page_number

            # Check if page index is valid
            if page_index < 0 or page_index >= total_pages:
                print(f"  ⚠ Warning: Page {page_number} is out of range (1-{total_pages})")
                continue

            # Create a writer for this page
            writer = PdfWriter()
            writer.add_page(pdf.pages[page_index])

            # Save the page to the output directory
            output_path = output_folder / f"page_{page_number}.pdf"
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            print(f"  ✓ Saved page {page_number} to {output_path.name}")

        print(f"Successfully saved {len(page_numbers)} pages to folder: '{output_folder}'")
        return str(output_folder)

    def _get_page_file(self, pages_folder: Path, page_num: int) -> Optional[Path]:
        """
        Get the path to a page file if it exists.

        Args:
            pages_folder: Path to folder containing split PDF pages
            page_num: Page number to check

        Returns:
            Path to the page file if it exists, None otherwise
        """
        page_file = pages_folder / f"page_{page_num}.pdf"
        if not page_file.exists():
            print(f"  ⚠ Warning: Page file for page {page_num} not found")
            return None
        return page_file

    def _extract_page_contents(self, pages_folder: str, page_numbers: List[int]) -> Dict:
        """
        Extract text and table content from split PDF pages.

        Args:
            pages_folder: Path to folder containing split PDF pages
            page_numbers: List of page numbers to process

        Returns:
            Dictionary with results for each processed page
        """
        pages_folder = Path(pages_folder)
        print(f"Processing pages in folder: {pages_folder}")
        results = {}

        for page_num in page_numbers:
            page_file = self._get_page_file(pages_folder, page_num)
            if page_file is None:
                continue

            page_results = {"page_number": page_num, "text_extraction": None, "table_extraction": None}

            # Check if extraction has already been done for this page
            existing_extraction = self._check_existing_extraction(pages_folder, page_num)

            try:
                print(f"  Processing page {page_num} from file: {page_file.name}")

                # Extract text content
                page_results["text_extraction"] = self._extract_text_content(page_file, page_num, existing_extraction)

                # Extract table content
                page_results["table_extraction"] = self._extract_table_content(page_file, page_num, existing_extraction)

            except Exception as e:
                print(f"  Error processing page {page_num}: {str(e)}")
                if "text_extraction" not in page_results:
                    page_results["text_extraction"] = {"status": "error", "error": str(e)}
                if "table_extraction" not in page_results:
                    page_results["table_extraction"] = {"status": "error", "error": str(e)}

            results[page_num] = page_results

        # Save overall results
        self._save_extraction_results(pages_folder, page_numbers, results)
        return results

    def _handle_existing_extraction(self, extraction_type: str, existing_extraction: dict) -> Optional[dict]:
        """
        Handle existing extraction for either text or tables.

        Args:
            extraction_type: Type of extraction ('text_extraction' or 'table_extraction')
            existing_extraction: Dictionary containing existing extraction info

        Returns:
            Dictionary with extraction results if exists, None otherwise
        """
        if existing_extraction[extraction_type]["exists"]:
            print(
                f"    ✓ {extraction_type.split('_')[0].title()} already extracted, using existing file: {Path(existing_extraction[extraction_type]['path']).name}"
            )
            try:
                rel_path = Path(existing_extraction[extraction_type]["path"]).relative_to(self.data_root)
                relative_path = str(rel_path)
            except ValueError:
                relative_path = existing_extraction[extraction_type]["path"]

            result = {
                "status": "success",
                "output_file": relative_path,
                "reused_existing": True,
            }

            # Add tables_count for table extraction
            if extraction_type == "table_extraction":
                result["tables_count"] = existing_extraction[extraction_type].get("tables_count", 0)

            return result
        return None

    def _handle_text_result(self, text_result: dict, page_file: Path, page_num: int) -> dict:
        """
        Handle the result from text extraction API.

        Args:
            text_result: Result from extract_text_from_pdf_page
            page_file: Path to the page file
            page_num: Page number

        Returns:
            Dictionary with extraction status and output file path
        """
        if text_result["status"] == "success":
            output_md = page_file.parent / f"page_{page_num}.md"
            with open(output_md, "w", encoding="utf-8") as f:
                f.write(text_result["content"])

            try:
                rel_path = output_md.relative_to(self.data_root)
                relative_path = str(rel_path)
            except ValueError:
                relative_path = str(output_md)

            print(f"    ✓ Extracted text saved to {output_md.name}")
            return {"status": "success", "output_file": relative_path}
        else:
            print(f"    ✗ Failed to extract text: {text_result.get('error', 'Unknown error')}")
            return {
                "status": "error",
                "error": text_result.get("error", "Unknown error"),
            }

    def _handle_table_result(self, table_result: dict, page_file: Path, page_num: int) -> dict:
        """
        Handle the result from table extraction API.

        Args:
            table_result: Result from extract_tables_from_pdf_page
            page_file: Path to the page file
            page_num: Page number

        Returns:
            Dictionary with extraction status, output file path, and table count
        """
        if table_result["status"] == "success":
            output_json = page_file.parent / f"page_{page_num}_tables.json"
            content = table_result["content"]

            with open(output_json, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)

            try:
                rel_path = output_json.relative_to(self.data_root)
                relative_path = str(rel_path)
            except ValueError:
                relative_path = str(output_json)

            tables_count = len(content) if isinstance(content, list) else len(content.get("tables", []))

            if tables_count > 0:
                print(f"    ✓ Extracted {tables_count} tables saved to {output_json.name}")
            else:
                print("    ✓ No tables found on this page")

            return {
                "status": "success",
                "output_file": relative_path,
                "tables_count": tables_count,
            }
        else:
            print(f"    ✗ Failed to extract tables: {table_result.get('error', 'Unknown error')}")
            return {
                "status": "error",
                "error": table_result.get("error", "Unknown error"),
            }

    def _extract_text_content(self, page_file: Path, page_num: int, existing_extraction: dict) -> dict:
        """Extract text content from a PDF page."""
        # Check for existing extraction
        existing_result = self._handle_existing_extraction("text_extraction", existing_extraction)
        if existing_result:
            return existing_result

        print("    Extracting text content...")
        text_result = extract_text_from_pdf_page(str(page_file))
        return self._handle_text_result(text_result, page_file, page_num)

    def _extract_table_content(self, page_file: Path, page_num: int, existing_extraction: dict) -> dict:
        """Extract table content from a PDF page."""
        # Check for existing extraction
        existing_result = self._handle_existing_extraction("table_extraction", existing_extraction)
        if existing_result:
            return existing_result

        print("    Extracting tables...")
        try:
            table_result = extract_tables_from_pdf_page(str(page_file))
            return self._handle_table_result(table_result, page_file, page_num)
        except Exception as table_error:
            print(f"    ✗ Exception in table extraction: {str(table_error)}")
            return {"status": "error", "error": str(table_error)}

    def _check_existing_extraction(self, pages_folder: Path, page_num: int) -> dict:
        """
        Check if extraction has already been done for a page.

        Args:
            pages_folder: Path to the folder containing pages
            page_num: Page number to check

        Returns:
            Dictionary with text and table extraction status
        """
        result = {
            "text_extraction": {"exists": False, "path": None},
            "table_extraction": {"exists": False, "path": None},
        }

        # Check for text extraction (markdown file)
        md_file = pages_folder / f"page_{page_num}.md"
        if md_file.exists() and md_file.stat().st_size > 0:
            result["text_extraction"]["exists"] = True
            result["text_extraction"]["path"] = str(md_file)

        # Check for table extraction (JSON file)
        json_file = pages_folder / f"page_{page_num}_tables.json"
        if json_file.exists() and json_file.stat().st_size > 0:
            result["table_extraction"]["exists"] = True
            result["table_extraction"]["path"] = str(json_file)

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    tables_data = json.load(f)
                    if isinstance(tables_data, dict) and "tables" in tables_data:
                        result["table_extraction"]["tables_count"] = len(tables_data["tables"])
                    elif isinstance(tables_data, list):
                        result["table_extraction"]["tables_count"] = len(tables_data)
            except:
                result["table_extraction"]["exists"] = False
                result["table_extraction"]["path"] = None

        return result

    def _save_extraction_results(self, pages_folder: Path, page_numbers: List[int], results: Dict) -> None:
        """Save the overall extraction results to a JSON file."""
        results_file = pages_folder / "extraction_results.json"

        try:
            rel_results_path = results_file.relative_to(self.data_root)
            relative_results_path = str(rel_results_path)
        except ValueError:
            relative_results_path = str(results_file)

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(
                {"pages_processed": len(page_numbers), "results": results, "results_path": relative_results_path},
                f,
                indent=2,
            )

        print(f"Processing complete. Results saved to {results_file}")
