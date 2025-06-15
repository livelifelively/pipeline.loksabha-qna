import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from apps.py.types import (
    ChunkingData,
    InitializedData,
    LlmExtractionData,
    LlmExtractionPageData,
    LocalExtractionData,
    ManualReviewData,
    ManualReviewPageData,
    PageProcessingData,
    ProcessingMetadata,
    ProcessingState,
    ProcessingStatus,
    ProgressFileStructure,
)

from ...utils.state_manager import ProgressStateManager, StateData

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

    def get_initialized_data(self) -> Optional[StateData]:
        """Get INITIALIZED state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.INITIALIZED)

    def get_local_extraction_data(self) -> Optional[StateData]:
        """Get LOCAL_EXTRACTION state data with exact typing."""
        return self._state_manager.get_state_data(ProcessingState.LOCAL_EXTRACTION)

    def get_llm_extraction_data(self) -> Optional[LlmExtractionData]:
        """Get LLM_EXTRACTION state data with exact typing."""
        return self._get_page_processing_data(ProcessingState.LLM_EXTRACTION, LlmExtractionPageData, LlmExtractionData)

    def get_manual_review_data(self) -> Optional[ManualReviewData]:
        """Get MANUAL_REVIEW state data with exact typing."""
        return self._get_page_processing_data(ProcessingState.MANUAL_REVIEW, ManualReviewPageData, ManualReviewData)

    def get_chunking_data(self) -> Optional[ChunkingData]:
        """Get CHUNKING state data with exact typing."""
        generic_state_data = self._state_manager.get_state_data(ProcessingState.CHUNKING)
        if not generic_state_data:
            return None
        return ChunkingData(**generic_state_data.data)

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

    def _get_page_processing_data(self, state: ProcessingState, page_data_class, state_data_class):
        """Generic helper for getting page processing state data."""

        generic_state_data = self._state_manager.get_state_data(state)
        if not generic_state_data:
            return None

        data = generic_state_data.data
        if not isinstance(data, dict):
            logger.warning(f"Expected dict for state data, got {type(data)}")
            return None

        # Create default processing metadata if not present
        processing_metadata = ProcessingMetadata(
            processing_time_seconds=0.0,
            pages_processed=0,
            pages_failed=0,
            llm_model_used=None,
            reviewer=None,
        )
        if "processing_metadata" in data:
            try:
                processing_metadata = ProcessingMetadata(**data["processing_metadata"])
            except Exception as e:
                logger.warning(f"Failed to parse processing metadata: {e}")

        pages = {}
        if "pages" in data:
            try:
                for page_num_str, page_dict in data["pages"].items():
                    pages[int(page_num_str)] = page_data_class(**page_dict)
            except Exception as e:
                logger.warning(f"Failed to parse page data: {e}")

        return state_data_class(
            status=ProcessingStatus(generic_state_data.status),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now(UTC).isoformat())),
            processing_metadata=processing_metadata,
            pages=pages,
            error_message=data.get("error_message"),
        )

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
        generic_state_data = self._convert_to_generic_state_data(state_data)
        self._state_manager.transition_to_state(target_state, generic_state_data)

    def _convert_to_generic_state_data(self, state_data: Union[PageProcessingData, ChunkingData]) -> StateData:
        """Convert document-specific state data to generic format."""

        return StateData(
            status=state_data.status.value,
            data=state_data.model_dump(exclude={"status"}),
        )


# Legacy alias for backward compatibility
ProgressHandler = DocumentProgressHandler
