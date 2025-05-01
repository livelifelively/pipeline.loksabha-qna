from pathlib import Path


def find_project_root() -> str:
    """
    Finds the project root directory by traversing upwards until a project marker file is found.

    Looks for common Python project markers in this order:
    1. pyproject.toml
    2. setup.py
    3. .project-root

    Returns:
        str: The absolute path to the project root directory.

    Raises:
        RuntimeError: If the project root cannot be found.
    """
    current_dir = Path(__file__).resolve().parent

    marker_files = [".project-root"]

    while True:
        # Check for any of the marker files
        for marker in marker_files:
            if (current_dir / marker).exists():
                return str(current_dir)

        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:  # Reached filesystem root
            raise RuntimeError(
                "Could not find project root. Create a .project-root file in your project root directory."
            )

        current_dir = parent_dir


def get_loksabha_data_root() -> Path:
    """
    Gets the path to the sansad data root directory.

    Returns:
        Path: The absolute path to the sansad data directory (loksabha-qna).

    Note:
        This assumes the data directory is located at '../data/loksabha-qna'
        relative to the project root.
    """
    return Path(find_project_root()).parent / "data" / "loksabha-qna"
