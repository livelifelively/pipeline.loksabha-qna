import re
from typing import List

def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text)
    return text

def extract_member_names(text: str) -> List[str]:
    """Extract and clean member names from text."""
    # Split by common separators
    names = re.split(r'[,;]', text)
    # Clean each name
    return [clean_text(name) for name in names if name.strip()]
