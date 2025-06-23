import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def safe_mkdir_with_conflict_detection(target_path: Path) -> None:
    """
    Safely create directory structure with clear error reporting for file conflicts.

    Args:
        target_path: Path to the directory to create

    Raises:
        IOError: If directory cannot be created due to file conflicts or other issues
    """
    try:
        target_path.mkdir(parents=True, exist_ok=True)
    except FileExistsError as e:
        # This can happen if there's a file with the same name as a directory we're trying to create
        logger.error(
            "Cannot create directory structure - file exists with same name",
            extra={
                "target_path": str(target_path),
                "error": str(e),
            },
        )

        # Check what's conflicting by walking up the path
        conflicting_path = target_path
        while conflicting_path != conflicting_path.parent:  # Stop at filesystem root
            if conflicting_path.exists() and conflicting_path.is_file():
                logger.error(
                    "Found conflicting file in directory path",
                    extra={"conflicting_file": str(conflicting_path), "expected_to_be": "directory"},
                )
                break
            conflicting_path = conflicting_path.parent

        raise IOError(
            f"Cannot create directory structure. File exists where directory expected: {conflicting_path}"
        ) from e


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
