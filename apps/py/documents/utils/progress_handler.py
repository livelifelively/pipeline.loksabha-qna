import json
from pathlib import Path
from typing import Optional

from apps.py.utils.project_root import get_loksabha_data_root


class ProgressHandler:
    """Handles reading and writing progress data to JSON files."""

    def __init__(self, data_root: Optional[Path] = None):
        """
        Initialize the progress handler.

        Args:
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()
        """
        self.data_root = data_root or get_loksabha_data_root()

    def append_step(self, progress_file: Path, step_data: dict) -> None:
        """
        Read progress.json file and append new step data.

        Args:
            progress_file: Path to progress.json file
            step_data: Complete step data to append

        Raises:
            FileNotFoundError: If progress.json doesn't exist
            ValueError: If progress.json is empty or doesn't have required structure
        """
        if not progress_file.exists():
            raise FileNotFoundError(f"progress.json not found in {progress_file.parent}")

        with open(progress_file, "r+", encoding="utf-8") as f:
            data = json.load(f)

            if not data or "steps" not in data:
                raise ValueError("progress.json is empty or missing required 'steps' array")

            # Append new step to steps array
            data["steps"].append(step_data)

            # Write back the updated data
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def get_relative_path(self, file_path: Path) -> str:
        """
        Gets relative path for a file.

        Args:
            file_path: Path to get relative path for

        Returns:
            Relative path string
        """
        try:
            return str(file_path.relative_to(self.data_root))
        except ValueError:
            return str(file_path)
