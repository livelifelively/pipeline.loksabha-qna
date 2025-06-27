import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from apps.py.types import (
    ChunkingData,
    GenericStateData,
    InitializedData,
    LlmExtractionData,
    LocalExtractionData,
    ManualReviewData,
    ManualReviewPageData,
    PageProcessingData,
    PrepareDataData,
    ProcessingState,
    ProcessingStatus,
    ProgressFileStructure,
)

from ...utils.state_manager import ProgressStateManager

# Configure logger
logger = logging.getLogger(__name__)


class DocumentProgressHandler:
    """
    Document-focused progress handler that uses ProgressStateManager
    and provides document-specific typed operations.
    """

    def __init__(self, document_path: Path):
        """Initialize the document progress handler."""
        self.document_path = Path(document_path)
        progress_file = self.document_path / "question.progress.json"
        # File starts directly with INITIALIZED state
        self._state_manager = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)

    # ===============================
    # DOCUMENT-SPECIFIC TYPED METHODS
    # ===============================

    def read_progress_file(self) -> ProgressFileStructure:
        """Read progress file with document-specific typing."""
        raw_progress = self._state_manager.read_progress_file()

        try:
            return ProgressFileStructure(**raw_progress)
        except Exception as e:
            logger.error(
                "Progress file failed validation - this indicates a format mismatch or corrupted data",
                extra={
                    "progress_file": str(self._state_manager.progress_file),
                    "error": str(e),
                    "raw_data": raw_progress,
                },
            )
            # Don't fail silently - raise the validation error with context
            raise ValueError(
                f"Progress file validation failed for {self._state_manager.progress_file}. "
                f"This usually indicates a format mismatch between expected and actual JSON structure. "
                f"Error: {str(e)}"
            ) from e

    def get_current_state(self) -> ProcessingState:
        """Get current state with document-specific typing."""
        state_str = self._state_manager.get_current_state()
        return ProcessingState(state_str)

    # ===============================
    # STATE-SPECIFIC FUNCTIONS
    # ===============================

    def get_initialized_data(self) -> Optional[GenericStateData]:
        """Get INITIALIZED state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.INITIALIZED)

    def get_local_extraction_data(self) -> Optional[GenericStateData]:
        """Get LOCAL_EXTRACTION state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.LOCAL_EXTRACTION)

    def get_llm_extraction_data(self) -> Optional[GenericStateData]:
        """Get LLM_EXTRACTION state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.LLM_EXTRACTION)

    def get_manual_review_data(self) -> Optional[GenericStateData]:
        """Get MANUAL_REVIEW state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.MANUAL_REVIEW)

    def get_prepare_data_data(self) -> Optional[GenericStateData]:
        """Get PREPARE_DATA state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.PREPARE_DATA)

    def get_chunking_data(self) -> Optional[GenericStateData]:
        """Get CHUNKING state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.CHUNKING)

    def transition_to_initialized(self, question_metadata: Dict[str, Any]) -> None:
        """Transition to INITIALIZED state with question metadata."""
        current_state = self._state_manager.get_current_state()

        # Handle first-time initialization when current_state is None
        if current_state is None:
            logger.info(
                "Starting document processing for the first time",
                extra={"progress_file": str(self._state_manager.progress_file)},
            )

        state_data = InitializedData(
            status=ProcessingStatus.SUCCESS,
            question_number=question_metadata["question_number"],
            subjects=question_metadata["subjects"],
            loksabha_number=question_metadata["loksabha_number"],
            member=question_metadata["member"],
            ministry=question_metadata["ministry"],
            type=question_metadata["type"],
            date=question_metadata["date"],
            questions_file_path_local=question_metadata["questions_file_path_local"],
            questions_file_path_web=question_metadata["questions_file_path_web"],
            questions_file_path_hindi_local=question_metadata.get("questions_file_path_hindi_local"),
            questions_file_path_hindi_web=question_metadata.get("questions_file_path_hindi_web"),
            question_text=question_metadata.get("question_text"),
            answer_text=question_metadata.get("answer_text"),
            session_number=question_metadata["session_number"],
            started_by=question_metadata.get("started_by"),
            notes=question_metadata.get("notes"),
        )
        self._validate_and_transition(ProcessingState.INITIALIZED, state_data)

    def transition_to_local_extraction(self, state_data: LocalExtractionData) -> None:
        """Transition to LOCAL_EXTRACTION state with type safety."""
        self._validate_and_transition(ProcessingState.LOCAL_EXTRACTION, state_data)

    def transition_to_llm_extraction(self, state_data: LlmExtractionData) -> None:
        """Transition to LLM_EXTRACTION state with type safety."""
        self._validate_and_transition(ProcessingState.LLM_EXTRACTION, state_data)

    def transition_to_manual_review(self, state_data: ManualReviewData) -> None:
        """Transition to MANUAL_REVIEW state with type safety."""
        self._validate_and_transition(ProcessingState.MANUAL_REVIEW, state_data)

    def transition_to_prepare_data(self, state_data: PrepareDataData) -> None:
        """Transition to PREPARE_DATA state with type safety."""
        self._validate_and_transition(ProcessingState.PREPARE_DATA, state_data)

    def transition_to_chunking(self, state_data: ChunkingData) -> None:
        """Transition to CHUNKING state with type safety."""
        self._validate_and_transition(ProcessingState.CHUNKING, state_data)

    # ===============================
    # GENERIC FALLBACK FUNCTIONS (for backward compatibility)
    # ===============================

    def get_state_data(self, state: ProcessingState) -> Optional[Union[PageProcessingData, ChunkingData]]:
        """Get state data with document-specific typing (generic fallback)."""
        if state == ProcessingState.LOCAL_EXTRACTION:
            return self.get_local_extraction_data()
        elif state == ProcessingState.LLM_EXTRACTION:
            return self.get_llm_extraction_data()
        elif state == ProcessingState.MANUAL_REVIEW:
            return self.get_manual_review_data()
        elif state == ProcessingState.PREPARE_DATA:
            return self.get_prepare_data_data()
        elif state == ProcessingState.CHUNKING:
            return self.get_chunking_data()
        else:
            raise ValueError(f"Unknown state: {state}")

    def transition_to_state(
        self, target_state: ProcessingState, state_data: Union[PageProcessingData, ChunkingData]
    ) -> None:
        """Transition to state with document-specific validation (generic fallback)."""
        self._validate_and_transition(target_state, state_data)

    def rollback_to_state(self, target_state: ProcessingState) -> None:
        """Rollback to previous state."""
        # Use import from centralized types module
        from ...types import STATE_ORDER

        self._state_manager.rollback_to_state(target_state, STATE_ORDER)

    # ===============================
    # PRIVATE HELPER METHODS
    # ===============================

    def _validate_and_transition(
        self, target_state: ProcessingState, state_data: Union[PageProcessingData, ChunkingData]
    ) -> None:
        """Validate transition and delegate to state manager."""
        # Validate transition using document-specific rules
        progress = self.read_progress_file()
        if not progress.can_transition_to(target_state):
            details = progress.get_transition_details(target_state)
            raise ValueError(f"Invalid transition: {details['error']}")

        # Convert and delegate
        generic_state_data = self._convert_to_generic_state_data(target_state, state_data)
        self._state_manager.transition_to_state(target_state, generic_state_data)

    def _convert_to_generic_state_data(
        self, target_state: ProcessingState, state_data: Union[PageProcessingData, ChunkingData]
    ) -> GenericStateData:
        """Convert document-specific state data to generic format."""
        return GenericStateData(
            status=state_data.status.value,  # Convert enum to string for generic format
            timestamp=datetime.now(UTC),
            data=state_data.model_dump(exclude={"status"}),
            state=target_state.value,  # Use the actual target state
        )

    def patch_manual_review_page(self, page_number: int, page_data: ManualReviewPageData) -> None:
        """
        Update a single page in the current MANUAL_REVIEW state.

        This method updates the latest MANUAL_REVIEW state entry with new page data,
        preserving existing pages and merging the new page data.

        Args:
            page_number: Page number to update
            page_data: New page data for the specified page

        Raises:
            ValueError: If not currently in MANUAL_REVIEW state or state doesn't exist
        """
        # Verify we're in MANUAL_REVIEW state
        current_state = self.get_current_state()
        if current_state != ProcessingState.MANUAL_REVIEW:
            raise ValueError(f"Cannot patch MANUAL_REVIEW - current state is {current_state}")

        # Prepare partial data for the page update
        partial_data = {"pages": {str(page_number): page_data.model_dump()}}

        logger.info(
            "Patching MANUAL_REVIEW page data",
            extra={
                "progress_file": str(self._state_manager.progress_file),
                "page_number": page_number,
                "has_tables": page_data.has_tables,
                "passed_review": page_data.passed_review,
                "text_edited": page_data.text_edited,
                "tables_edited_count": len(page_data.tables_edited_ids),
            },
        )

        # Update the state data
        self._state_manager.update_state_data(ProcessingState.MANUAL_REVIEW, partial_data)

    def patch_manual_review_status(
        self, status: ProcessingStatus, processing_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the status of the current MANUAL_REVIEW state.

        This method updates only the status field (and optionally processing metadata)
        of the latest MANUAL_REVIEW state entry without affecting page data.

        Args:
            status: New processing status
            processing_metadata: Optional metadata updates (reviewer, processing_time, etc.)

        Raises:
            ValueError: If not currently in MANUAL_REVIEW state or state doesn't exist
        """
        # Verify we're in MANUAL_REVIEW state
        current_state = self.get_current_state()
        if current_state != ProcessingState.MANUAL_REVIEW:
            raise ValueError(f"Cannot patch MANUAL_REVIEW status - current state is {current_state}")

        # Prepare partial data for status update
        partial_data = {}

        # Update processing metadata if provided
        if processing_metadata:
            partial_data["processing_metadata"] = processing_metadata

        logger.info(
            "Patching MANUAL_REVIEW status",
            extra={
                "progress_file": str(self._state_manager.progress_file),
                "new_status": status.value,
                "metadata_updated": processing_metadata is not None,
            },
        )

        # Update the state data
        self._state_manager.update_state_data(ProcessingState.MANUAL_REVIEW, partial_data)

        # Also update the status field at the GenericStateData level
        # We need to handle this specially since status is not in the data field
        self._patch_state_status(ProcessingState.MANUAL_REVIEW, status)

    def patch_manual_review_bulk_pages(self, pages_data: Dict[int, ManualReviewPageData]) -> None:
        """
        Update multiple pages in the current MANUAL_REVIEW state in a single operation.

        Args:
            pages_data: Dictionary mapping page numbers to page data

        Raises:
            ValueError: If not currently in MANUAL_REVIEW state or state doesn't exist
        """
        # Verify we're in MANUAL_REVIEW state
        current_state = self.get_current_state()
        if current_state != ProcessingState.MANUAL_REVIEW:
            raise ValueError(f"Cannot patch MANUAL_REVIEW - current state is {current_state}")

        # Prepare partial data for bulk page update
        partial_data = {"pages": {str(page_num): page_data.model_dump() for page_num, page_data in pages_data.items()}}

        logger.info(
            "Patching MANUAL_REVIEW bulk pages",
            extra={
                "progress_file": str(self._state_manager.progress_file),
                "pages_count": len(pages_data),
                "page_numbers": list(pages_data.keys()),
            },
        )

        # Update the state data
        self._state_manager.update_state_data(ProcessingState.MANUAL_REVIEW, partial_data)

    def _patch_state_status(self, state: ProcessingState, status: ProcessingStatus) -> None:
        """
        Update the status field of a state entry (outside of the data field).

        This is a helper method since status is stored at the GenericStateData level,
        not within the data field.
        """
        # Read current progress
        progress = self._state_manager.read_progress_file()

        # Find the latest entry for this state
        for state_entry in reversed(progress["states"]):
            if isinstance(state_entry, dict) and state_entry.get("state") == state.value:
                state_entry["status"] = status.value
                state_entry["timestamp"] = datetime.now(UTC).isoformat()
                break

        progress["updated_at"] = datetime.now(UTC)

        # Write back to file
        self._state_manager._write_validated_progress(progress)


# Legacy alias for backward compatibility
ProgressHandler = DocumentProgressHandler
