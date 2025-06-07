import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from apps.py.utils.project_root import get_loksabha_data_root

# HOW ABOUT IT being a state machine? on which step it is?
# revert will delete the steps after that.
# you can only get the state and update if it is in the particular step, for the next step.


class ProgressHandler:
    """Handles reading and writing progress data to JSON files."""

    PROGRESS_FILE_NAME = "question.progress.json"

    def __init__(self, document_path: Union[str, Path]):
        """
        Initialize the progress handler.

        Args:
            document_path: Path to the document directory or file. Required for initialization.
            data_root: Root directory for data storage. If None, uses get_loksabha_data_root()

        Raises:
            ValueError: If document_path is not provided
            IOError: If progress file cannot be created
        """
        self.data_root = get_loksabha_data_root()
        self.progress_file = None

        if not document_path:
            raise ValueError("document_path is required for initialization")

        self.set_document_path(document_path)

        # Ensure progress file exists or create it
        if not self.progress_file.exists():
            self._initialize_progress_file()

    def set_document_path(self, document_path: Union[str, Path]) -> None:
        """
        Set the document path and initialize the progress file path.

        Args:
            document_path: Path to the document directory or file
        """
        document_path = Path(document_path)
        # If path is absolute and outside data_root, make it relative
        if document_path.is_absolute() and not str(document_path).startswith(str(self.data_root)):
            try:
                document_path = document_path.relative_to(self.data_root)
            except ValueError:
                pass
        # If path is relative, make it absolute relative to data_root
        elif not document_path.is_absolute():
            document_path = self.data_root / document_path

        if document_path.is_file():
            document_path = document_path.parent

        self.document_path = document_path
        self.progress_file = document_path / self.PROGRESS_FILE_NAME

    def _initialize_progress_file(self) -> None:
        """
        Initialize a new progress file with basic structure.

        Args:
            meta_data: Optional metadata to include in the progress file

        Raises:
            IOError: If file cannot be created
        """
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "meta": {},
            "steps": [],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2)
        except Exception as e:
            raise IOError(f"Failed to initialize progress file: {e}") from e

    def read_progress_file(self) -> Dict[str, Any]:
        """
        Read and parse a progress file.

        Returns:
            Dict containing progress data

        Raises:
            ValueError: If progress file is invalid JSON
        """
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Progress file must contain a JSON object")

            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in progress file: {e}") from e

    def get_step_data(self, step_name: str) -> Optional[Dict[str, Any]]:
        """
        Get data for a specific step from the progress file.

        Args:
            step_name: Name of the step to get data for

        Returns:
            Step data if found, None otherwise

        Raises:
            ValueError: If progress file is invalid
        """
        data = self.read_progress_file()

        if "steps" not in data:
            return None

        for step in data["steps"]:
            if step.get("step") == step_name:
                return step

        return None

    def append_step(self, step_data: dict) -> None:
        """
        Read progress file and append new step data.

        Args:
            step_data: Complete step data to append
        """
        with open(self.progress_file, "r+", encoding="utf-8") as f:
            data = json.load(f)

            # Update or append step
            step_name = step_data.get("step")
            if step_name:
                # Remove existing step with same name if present
                data["steps"] = [step for step in data["steps"] if step.get("step") != step_name]

            # Append new step
            data["steps"].append(step_data)

            # Update timestamp
            data["updated_at"] = datetime.now(UTC).isoformat()

            # Write back the updated data
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def update_meta(self, meta_data: Dict[str, Any]) -> None:
        """
        Update metadata in the progress file.

        Args:
            meta_data: New metadata to update/merge

        Raises:
            ValueError: If progress file is invalid
        """
        with open(self.progress_file, "r+", encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, dict):
                raise ValueError("Progress file must contain a JSON object")

            # Create or update meta section
            if "meta" not in data:
                data["meta"] = {}
            data["meta"].update(meta_data)

            # Update timestamp
            data["updated_at"] = datetime.now(UTC).isoformat()

            # Write back the updated data
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
