import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict

from api.py.schemas.knowledge_graph import QuestionMetadata

from .types import CleanedData


class CleanedDataRepository:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def get_cleaned_data_path(self, metadata: QuestionMetadata) -> Path:
        """
        Construct the cleaned data path from metadata and create it if it doesn't exist.
        Returns the path.
        """
        cleaned_data_path = Path(metadata.document_path) / "cleaned_data.json"
        if not cleaned_data_path.exists():
            # Create parent directories if they don't exist
            cleaned_data_path.parent.mkdir(parents=True, exist_ok=True)
            # Create an empty file
            cleaned_data_path.touch()
        return cleaned_data_path

    async def read_cleaned_data(self, file_path: Path) -> CleanedData:
        """
        Read existing cleaned data from file.

        Args:
            file_path: Path to cleaned data file

        Returns:
            CleanedData instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file content is invalid
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return CleanedData.model_validate(data)
        except FileNotFoundError:
            raise
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cleaned data file: {e}") from e
        except Exception as e:
            raise ValueError(f"Error reading cleaned data: {e}") from e

    async def save_cleaned_data(self, data: CleanedData, file_path: Path) -> None:
        """
        Save cleaned data to file.

        Args:
            data: CleanedData instance to save
            file_path: Path to save the file

        Raises:
            IOError: If file cannot be written
        """
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w") as f:
                json.dump(data.model_dump(), f, indent=2)
        except Exception as e:
            raise IOError(f"Error saving cleaned data: {e}") from e

    async def update_progress(self, metadata: QuestionMetadata, file_path: Path, data: CleanedData) -> None:
        """
        Update progress.json with new data_cleaning step.

        Args:
            metadata: Question metadata
            file_path: Path to cleaned data file
            data: CleanedData instance

        Raises:
            IOError: If progress file cannot be updated
        """
        progress_path = file_path.parent / "progress.json"

        try:
            # Read existing progress
            if progress_path.exists():
                with open(progress_path, "r") as f:
                    progress = json.load(f)
            else:
                progress = {"steps": []}

            # Add or update data_cleaning step
            step_data = {
                "step": "data_cleaning",
                "timestamp": datetime.now(UTC).isoformat(),
                "status": "success",
                "data": {
                    "cleaned_data_path": str(file_path),
                    "cleaning_metrics": {
                        "total_pages": len(data.pages),
                        "pages_with_tables": sum(1 for page in data.pages if page.tables),
                        "total_tables": sum(len(page.tables) for page in data.pages if page.tables),
                    },
                },
            }

            # Update or append step
            for i, step in enumerate(progress["steps"]):
                if step["step"] == "data_cleaning":
                    progress["steps"][i] = step_data
                    break
            else:
                progress["steps"].append(step_data)

            # Save updated progress
            with open(progress_path, "w") as f:
                json.dump(progress, f, indent=2)

        except Exception as e:
            raise IOError(f"Error updating progress: {e}") from e

    async def get_pdf_extraction_data(self, metadata: QuestionMetadata) -> Dict[str, Any]:
        """
        Get data from pdf_extraction step.

        Args:
            metadata: Question metadata containing document_path

        Returns:
            Dictionary containing pdf_extraction step data

        Raises:
            FileNotFoundError: If progress.json doesn't exist
            ValueError: If pdf_extraction step not found
        """
        progress_path = Path(metadata.document_path) / "progress.json"

        try:
            with open(progress_path, "r") as f:
                progress = json.load(f)

            # Find pdf_extraction step
            for step in progress["steps"]:
                if step["step"] == "pdf_extraction":
                    return step["data"]

            raise ValueError("pdf_extraction step not found in progress.json")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"progress.json not found at {progress_path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in progress.json: {e}") from e
