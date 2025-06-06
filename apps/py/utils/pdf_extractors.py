from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path
from typing import Literal

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict


class PDFExtractor(ABC):
    """Abstract base class for PDF extractors."""

    @abstractmethod
    async def extract_text(self, file_path: Path | str) -> str:
        """Extract text from a PDF file."""
        pass


class MarkerExtractor(PDFExtractor):
    """PDF extractor using the Marker library."""

    def __init__(self):
        self.converter = self._get_cached_converter()

    @staticmethod
    @lru_cache()
    def _get_cached_converter() -> PdfConverter:
        """Get a cached PDF converter instance."""
        return PdfConverter(
            artifact_dict=create_model_dict(),
            config={
                "output_format": "markdown",
                "paginate_output": True,
            },
        )

    async def extract_text(self, file_path: Path | str) -> str:
        """Extract text from a PDF file using Marker."""
        try:
            rendered = self.converter(str(file_path))
            return rendered.markdown
        except Exception as e:
            raise Exception(f"Error extracting text from PDF using Marker: {str(e)}") from e


def get_pdf_extractor(extractor_type: Literal["marker"] = "marker") -> PDFExtractor:
    """Get a PDF extractor instance based on the specified type."""
    if extractor_type != "marker":
        raise ValueError(f"Unsupported extractor type '{extractor_type}'. Use 'marker'.")
    return MarkerExtractor()
