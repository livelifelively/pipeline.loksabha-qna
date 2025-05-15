from pathlib import Path
from typing import List, Tuple, Union

from apps.py.utils.project_root import get_loksabha_data_root


def find_all_document_paths(selected_ministries):
    """Find document paths across all selected ministries."""
    all_document_paths = []
    for ministry in selected_ministries:
        ministry_docs = find_document_paths(ministry)
        all_document_paths.extend(ministry_docs)

    return all_document_paths


def find_document_paths(ministry_path):
    """Find all document paths within the ministry directory."""
    try:
        # Each subfolder in the ministry directory may contain a PDF file
        document_dirs = [d for d in ministry_path.iterdir() if d.is_dir()]

        if not document_dirs:
            print(f"\nNo document directories found in {ministry_path.name}.")
            return []

        # Find directories containing PDF files
        pdf_dirs = []
        for doc_dir in document_dirs:
            pdf_files = list(doc_dir.glob("*.pdf"))
            if pdf_files:
                pdf_dirs.append(doc_dir)

        return pdf_dirs
    except Exception as e:
        print(f"\nError finding document paths: {str(e)}")
        return []


class PathValidationError(Exception):
    """Exception raised when path validation fails."""

    def __init__(self, message, status_code=404):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_and_get_ministry_paths(
    sansad: str, session: str, ministry_names: List[str]
) -> Tuple[Path, Path, List[Path]]:
    """
    Validate sansad, session, and ministry paths and return the valid paths.

    Args:
        sansad: Sansad name
        session: Session name
        ministry_names: List of ministry names

    Returns:
        Tuple of (session_path, ministries_dir, ministry_paths)

    Raises:
        PathValidationError: If any path is invalid
    """
    data_root = get_loksabha_data_root()

    # Validate session path
    session_path = data_root / sansad / session
    if not session_path.exists():
        raise PathValidationError(f"Session not found: {sansad}/{session}")

    # Validate ministries directory
    ministries_dir = session_path / "ministries"
    if not ministries_dir.exists():
        raise PathValidationError(f"Ministries directory not found for {sansad}/{session}")

    # Validate and collect ministry paths
    ministry_paths = []
    for ministry_name in ministry_names:
        ministry_path = ministries_dir / ministry_name
        if not ministry_path.exists():
            raise PathValidationError(f"Ministry not found: {ministry_name}")
        ministry_paths.append(ministry_path)

    return session_path, ministries_dir, ministry_paths


def validate_document_path(document_path: Union[str, Path]) -> Path:
    """
    Validate a document path and return the absolute path.

    Args:
        document_path: Document path (relative or absolute)

    Returns:
        Absolute Path object

    Raises:
        PathValidationError: If path is invalid or file doesn't exist
    """
    data_root = get_loksabha_data_root()

    # Convert to Path object
    doc_path = Path(document_path)

    # Convert to absolute path if needed
    if not doc_path.is_absolute():
        doc_path = data_root / doc_path

    # Validate the path
    try:
        doc_path = doc_path.resolve()
        if not str(doc_path).startswith(str(data_root.resolve())):
            raise PathValidationError("Invalid path: Must be within project directory", 400)
    except Exception as e:
        if isinstance(e, PathValidationError):
            raise
        raise PathValidationError("Invalid path", 400) from None

    # Check if file exists
    if not doc_path.exists():
        raise PathValidationError("Document not found")

    return doc_path


def get_absolute_document_path(doc_path_str: str) -> Path:
    """
    Convert a document path to an absolute path.

    Args:
        doc_path_str: Document path string (relative or absolute)

    Returns:
        Absolute Path object
    """
    data_root = get_loksabha_data_root()
    doc_path = Path(doc_path_str)

    if not doc_path.is_absolute():
        doc_path = data_root / doc_path

    return doc_path
