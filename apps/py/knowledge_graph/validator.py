from pathlib import Path
from typing import Dict

from .exceptions import InvalidMetadataError, QuestionNotFoundError


class QuestionValidator:
    def __init__(self, base_path: Path = Path("data")):
        self.base_path = base_path

    async def validate_question_exists(self, metadata: Dict[str, str]) -> None:
        """
        Validate if the question exists and has required metadata.

        Args:
            metadata: Question metadata containing loksabha_number, session_number, question_id

        Raises:
            InvalidMetadataError: If required metadata is missing
            QuestionNotFoundError: If question directory doesn't exist
        """
        # Validate required metadata
        required_fields = ["loksabha_number", "session_number", "question_id"]
        missing_fields = [field for field in required_fields if field not in metadata]
        if missing_fields:
            raise InvalidMetadataError(f"Missing required metadata fields: {', '.join(missing_fields)}")

        # Check if question directory exists
        question_path = (
            self.base_path
            / metadata["loksabha_number"]
            / metadata["session_number"]
            / "ministries"
            / metadata["question_id"]
        )

        if not question_path.exists():
            raise QuestionNotFoundError(f"Question not found at path: {question_path}")
