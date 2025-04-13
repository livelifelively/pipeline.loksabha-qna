import os
from pathlib import Path
from typing import Any

import google.generativeai as genai

from .pdf_extractors import get_pdf_extractor


def init_gemini() -> Any:
    """Initialize Gemini API with API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")


async def extract_text_from_pdf(file_path: Path | str, genai_model: Any, extractor_type: str = "marker") -> str:
    """
    Extract text from PDF using the specified extractor.

    Args:
        file_path: Path to the PDF file
        genai_model: Initialized Gemini model
        extractor_type: Type of PDF extractor to use ("marker" or "markitdown")

    Returns:
        Combined text in markdown format
    """
    try:
        extractor = get_pdf_extractor(extractor_type)
        return await extractor.extract_text(file_path)
    except Exception as e:
        error_msg = f"Error extracting text from PDF: {str(e)}"
        print(error_msg)
        return f"[{error_msg}]"
