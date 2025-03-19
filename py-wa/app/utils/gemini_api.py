import os
from pathlib import Path
from typing import Any

import google.generativeai as genai


def init_gemini() -> Any:
    """Initialize Gemini API with API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


async def extract_text_from_pdf(file_path: Path | str, genai_model: Any) -> str:
    """
    Extract text from PDF using Marker for high-quality extraction.

    Args:
        file_path: Path to the PDF file
        genai_model: Initialized Gemini model

    Returns:
        Combined text in markdown format
    """
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    try:
        # Initialize Marker converter
        converter = PdfConverter(
            artifact_dict=create_model_dict(),
            config={
                "output_format": "markdown",
                "paginate_output": False,
            },
        )

        # Convert PDF to markdown
        rendered = converter(str(file_path))

        # Extract markdown content
        return rendered.markdown

    except Exception as e:
        error_msg = f"Error extracting text from PDF: {str(e)}"
        print(error_msg)
        return f"[{error_msg}]"
