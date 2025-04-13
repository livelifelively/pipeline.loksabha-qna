from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from markitdown import MarkItDown


class PDFExtractor(ABC):
    """Abstract base class for PDF extractors."""

    @abstractmethod
    async def extract_text(self, file_path: Path | str) -> str:
        """Extract text from a PDF file."""
        pass


class MarkerExtractor(PDFExtractor):
    """PDF extractor using the Marker library."""

    async def extract_text(self, file_path: Path | str) -> str:
        """Extract text from a PDF file using Marker."""
        try:
            converter = PdfConverter(
                artifact_dict=create_model_dict(),
                config={
                    "output_format": "markdown",
                    "paginate_output": True,
                },
            )
            rendered = converter(str(file_path))
            return rendered.markdown
        except Exception as e:
            error_msg = f"Error extracting text from PDF using Marker: {str(e)}"
            print(error_msg)
            return f"[{error_msg}]"


class MarkItDownExtractor(PDFExtractor):
    """PDF extractor using the MarkItDown library."""

    async def extract_text(self, file_path: Path | str) -> str:
        """Extract text from a PDF file using MarkItDown."""
        try:
            md = MarkItDown()
            result = md.convert(str(file_path))
            return result.text_content
        except Exception as e:
            error_msg = f"Error extracting text from PDF using MarkItDown: {str(e)}"
            print(error_msg)
            return f"[{error_msg}]"


def get_pdf_extractor(extractor_type: Literal["marker", "markitdown"] = "marker") -> PDFExtractor:
    """Get a PDF extractor instance based on the specified type."""
    extractors = {
        "marker": MarkerExtractor,
        "markitdown": MarkItDownExtractor,
    }
    return extractors[extractor_type]()
