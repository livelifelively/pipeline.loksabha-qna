from pathlib import Path
from typing import Optional

from apps.py.utils.gemini_api import extract_text_from_pdf_page

from .base import BaseExtractor


class TextExtractor(BaseExtractor):
    """Extractor for text from PDF pages."""

    def extract_text(self, page_file: Path, page_num: int, output_folder: Optional[Path] = None) -> dict:
        """
        Extract text from a single-page PDF file and save as markdown.
        Args:
            page_file: Path to the single-page PDF file.
            page_num: Page number (for naming output).
            output_folder: Where to save the extracted text file.
        Returns:
            dict: { 'status': 'success'|'error', 'output_file': str, 'error': str|None }
        """
        output_folder = output_folder or page_file.parent
        self._ensure_output_folder(output_folder)
        text_result = extract_text_from_pdf_page(str(page_file))
        if text_result["status"] == "success":
            output_md = output_folder / f"page_{page_num}.md"
            with open(output_md, "w", encoding="utf-8") as f:
                f.write(text_result["content"])
            try:
                rel_path = output_md.relative_to(self.data_root)
                relative_path = str(rel_path)
            except ValueError:
                relative_path = str(output_md)
            return {"status": "success", "output_file": relative_path}
        else:
            return {"status": "error", "error": text_result.get("error", "Unknown error")}
