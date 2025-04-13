import os


def kebab_case_names(text: str) -> str:
    """
    Convert text to kebab-case by removing commas, 'and', '&'
    and replacing spaces with hyphens.
    """
    # Remove commas, 'and', '&' and trim whitespace
    smaller_text = text.strip().replace(",", "").replace("and", "").replace("&", "")
    # Convert to lowercase and replace spaces with hyphens
    return "-".join(smaller_text.split()).lower()


def filename_generator(url: str, index: int) -> str:
    """Generate filename from URL."""
    # Extract the filename from the URL
    base_name = os.path.basename(url).split("?")[0]
    # If no extension, add .pdf
    if not os.path.splitext(base_name)[1]:
        base_name += ".pdf"
    return base_name
