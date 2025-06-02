from pathlib import Path
from typing import Optional


# If you have a project root utility, import it here. Otherwise, set a default.
def get_loksabha_data_root() -> Path:
    # Placeholder: update this to your actual data root logic if needed
    return Path("/data/loksabha")


class BaseExtractor:
    """Base class for all extractors with common functionality."""

    def __init__(self, data_root: Optional[Path] = None):
        self.data_root = data_root or get_loksabha_data_root()

    def _get_relative_path(self, path: Path) -> str:
        """Convert path to relative path from data root."""
        try:
            return str(path.relative_to(self.data_root))
        except ValueError:
            return str(path)

    def _ensure_output_folder(self, output_folder: Path) -> Path:
        """Ensure output folder exists."""
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder
