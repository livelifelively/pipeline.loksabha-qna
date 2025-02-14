import os
import re

def kebab_case_names(text: str) -> str:
    """Convert text to kebab-case."""
    # Convert camelCase to snake_case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
    # Convert to lowercase and replace spaces/underscores with hyphens
    return re.sub(r'[_\s]+', '-', s2.lower().strip())

def filename_generator(url: str, index: int) -> str:
    """Generate filename from URL."""
    # Extract the filename from the URL
    base_name = os.path.basename(url).split('?')[0]
    # If no extension, add .pdf
    if not os.path.splitext(base_name)[1]:
        base_name += '.pdf'
    return base_name 