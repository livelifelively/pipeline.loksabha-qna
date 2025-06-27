# apps/py/documents/models.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from ..utils.timestamps import get_current_timestamp
from .types import QuestionType


class GenericStateData(BaseModel):
    """Generic domain-agnostic state data structure"""

    state: str
    status: str
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)
    meta: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class BaseProgressFileStructure(BaseModel):
    """Generic base structure for progress files"""

    current_state: str  # Store as string to be enum-agnostic
    states: List[Dict[str, Any]]  # Generic states array storage, domain-specific validation happens elsewhere
    created_at: datetime
    updated_at: datetime
    # Note: states field is defined in subclasses with specific typing


class MultiPageTableInfo(BaseModel):
    """Information about a single multi-page table."""

    pages: List[int] = Field(description="List of page numbers that are part of this table")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this table detection")
    reasoning: str = Field(description="Explanation of why these pages are connected")
    output_file: Optional[str] = None


class ExtractionResult(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    output_file: Optional[str] = None
    error: Optional[str] = None
    tables_count: Optional[int] = None
    reused_existing: Optional[bool] = None


class MultiPageTableResult(ExtractionResult):
    pages: List[int]
    page_range: Tuple[int, int]
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for this table detection")
    detection_reasoning: Optional[str] = Field(None, description="Reasoning for this table detection")
    table_number: Optional[int] = Field(None, description="Sequential number of the table")
    table_dimensions: Optional[List[Dict[str, int]]] = Field(
        None, description="Array of table dimensions, where each element contains num_rows for that table"
    )
    raw_response: Optional[str] = Field(None, description="Raw response from the model in case of error")


class SinglePageTableResult(ExtractionResult):
    page_number: int
    table_number: Optional[int] = Field(None, description="Sequential number of the table")
    table_dimensions: Optional[List[Dict[str, int]]] = Field(
        None, description="Array of table dimensions, where each element contains num_rows for that table"
    )


class ExtractionSummary(BaseModel):
    """Summary statistics for the extraction process."""

    total_tables: int = Field(description="Total number of tables processed")
    successful_tables: int = Field(description="Number of successfully extracted tables")
    failed_tables: int = Field(description="Number of failed table extractions")
    multi_page_tables: int = Field(description="Number of multi-page tables")
    single_page_tables: int = Field(description="Number of single-page tables")


# Type aliases for better readability
PageNumber = int
PageRange = Tuple[int, int]
PageIdentifier = Union[PageNumber, PageRange]
TableResult = Union[SinglePageTableResult, MultiPageTableResult]


class CombinedResults(BaseModel):
    """Combined results from all extraction processes."""

    pages_processed: int = Field(description="Total number of pages processed")
    table_results: Dict[PageIdentifier, TableResult] = Field(
        description="Raw results mapping page numbers (for single pages) or page ranges (for multi-page tables) to their extraction results"
    )
    summary: ExtractionSummary = Field(description="Summary statistics for the extraction process")
    text_results: Dict[int, ExtractionResult] = Field(
        default_factory=dict, description="Mapping of page numbers to their text extraction results"
    )

    # Structured view of results
    multi_page_tables: List[MultiPageTableResult] = Field(
        default_factory=list, description="List of all multi-page tables found"
    )
    single_page_tables: List[SinglePageTableResult] = Field(
        default_factory=list, description="List of all single-page table results"
    )
    pages_with_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that are part of multi-page tables"
    )
    pages_with_single_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that contain single-page tables"
    )
    pages_with_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that contain any type of table"
    )
    pages_with_errors: Set[int] = Field(
        default_factory=set, description="Set of all pages that encountered errors during processing"
    )
    errors: Dict[int, str] = Field(default_factory=dict, description="Mapping of page numbers to error messages")

    def __init__(self, **data):
        super().__init__(**data)
        # Process results into structured format
        table_counter = 1  # Counter for assigning table numbers
        for key, result in self.table_results.items():
            if isinstance(key, tuple):  # Multi-page table
                if isinstance(result, MultiPageTableResult) and result.status == "success":
                    result.table_number = table_counter
                    self.multi_page_tables.append(result)  # Add the full MultiPageTableResult
                    self.pages_with_multi_page_tables.update(result.pages)
                    self.pages_with_tables.update(result.pages)
                    table_counter += 1
                elif result.status == "error":
                    self.pages_with_errors.update(result.pages)
            else:  # Single page
                if isinstance(result, SinglePageTableResult):
                    if result.status == "error":
                        self.errors[key] = result.error
                        self.pages_with_errors.add(key)
                    else:
                        result.table_number = table_counter
                        self.single_page_tables.append(result)
                        self.pages_with_tables.add(key)
                        table_counter += 1
                    self.pages_with_single_page_tables.add(key)

        # Process text results
        for page_num, text_result in self.text_results.items():
            if text_result.status == "error":
                self.errors[page_num] = text_result.error
                self.pages_with_errors.add(page_num)

    class Config:
        json_encoders = {
            set: list,  # Convert sets to lists in JSON
            Tuple: list,  # Convert tuples to lists in JSON
        }


class TableDetectionResult(BaseModel):
    status: str = Field(..., pattern="^(success|error)$")
    is_multi_page_table: Optional[bool] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    error: Optional[str] = None


class MultiPageTableDetectionResult(BaseModel):
    """Result of multi-page table detection."""

    status: str = Field(..., pattern="^(success|error)$", description="Status of the detection: 'success' or 'error'")
    multi_page_tables: List[MultiPageTableInfo] = Field(
        default_factory=list, description="List of detected multi-page tables"
    )
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


class TableSummary(BaseModel):
    """Summary statistics for table extraction."""

    total_tables: int = Field(description="Total number of tables processed")
    successful_tables: int = Field(description="Number of successfully extracted tables")
    failed_tables: int = Field(description="Number of failed table extractions")


class MultiPageTableExtractionResults(BaseModel):
    """Structured results for table extraction process."""

    pages_processed: int = Field(description="Total number of pages processed")

    # Results mapping using the type aliases
    table_results: Dict[PageIdentifier, TableResult] = Field(
        description="Raw results mapping page numbers (for single pages) or page ranges (for multi-page tables) to their extraction results"
    )

    summary: TableSummary = Field(description="Summary statistics for the extraction process")

    # Structured view of results
    multi_page_tables: List[MultiPageTableResult] = Field(
        default_factory=list, description="List of all multi-page table results"
    )
    pages_with_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that are part of multi-page tables"
    )
    pages_without_multi_page_tables: Set[int] = Field(
        default_factory=set, description="Set of all pages that need single-page processing"
    )
    errors: Dict[int, str] = Field(default_factory=dict, description="Mapping of page numbers to error messages")

    def __init__(self, **data):
        super().__init__(**data)
        # Process results into structured format
        table_counter = 1  # Counter for assigning table numbers
        for key, result in self.table_results.items():
            if isinstance(key, tuple):  # Multi-page table
                if isinstance(result, MultiPageTableResult) and result.status == "success":
                    result.table_number = table_counter
                    self.multi_page_tables.append(result)  # Use the result directly
                    self.pages_with_multi_page_tables.update(result.pages)
                    table_counter += 1
            else:  # Single page
                if isinstance(result, SinglePageTableResult):
                    if result.status == "error":
                        self.errors[key] = result.error
                    else:
                        result.table_number = table_counter
                        table_counter += 1
                    self.pages_without_multi_page_tables.add(key)

    class Config:
        json_encoders = {
            set: list,  # Convert sets to lists in JSON
            Tuple: list,  # Convert tuples to lists in JSON
        }


# ============================================================================
# PROGRESS TRACKING AND STATE MACHINE TYPES
# ============================================================================


class ProcessingState(Enum):
    """Enum for document processing states"""

    NOT_STARTED = "NOT_STARTED"
    INITIALIZED = "INITIALIZED"
    LOCAL_EXTRACTION = "LOCAL_EXTRACTION"
    LLM_EXTRACTION = "LLM_EXTRACTION"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    PREPARE_DATA = "PREPARE_DATA"
    CHUNKING = "CHUNKING"


class ProcessingStatus(Enum):
    """Enum for processing step status"""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class TransitionReason(Enum):
    """Enum for transition reasons"""

    AUTOMATIC_PROGRESSION = "automatic_progression"
    MANUAL_ROLLBACK = "manual_rollback"
    ERROR_RECOVERY = "error_recovery"
    MANUAL_ADVANCEMENT = "manual_advancement"
    SYSTEM_RETRY = "system_retry"


class TriggerSource(Enum):
    """Enum for who/what triggered a transition"""

    SYSTEM = "system"
    USER = "user"
    AUTOMATED_PROCESS = "automated_process"
    ERROR_HANDLER = "error_handler"


class TransitionCondition(Enum):
    """Enum for transition conditions"""

    HAS_TABLES = "has_tables"
    NO_TABLES = "no_tables"


class TableMetadata(BaseModel):
    """Metadata for an extracted table in progress tracking"""

    table_number: int
    page: int
    accuracy: float
    num_columns: int
    num_rows: int


class IssueFlag(BaseModel):
    """Flag for issues found during manual review"""

    type: str  # e.g., "missing_table_extraction", "wrong_table_structure", "custom_issue"
    description: str
    severity: str  # "high", "medium", "low"
    flagged_by: str
    flagged_at: datetime = Field(default_factory=get_current_timestamp)


class ProcessingMetadata(BaseModel):
    """Metadata for a processing step"""

    processing_time_seconds: float
    pages_processed: int
    pages_failed: int
    llm_model_used: Optional[str] = None  # For LLM extraction step
    reviewer: Optional[str] = None  # For manual review step


class InitializedData(BaseModel):
    """Data structure for INITIALIZED state"""

    status: ProcessingStatus

    # Question metadata
    question_number: int
    subjects: str
    loksabha_number: str
    member: List[str]
    ministry: str
    type: QuestionType  # Reverted back to QuestionType
    date: str
    questions_file_path_local: str
    questions_file_path_web: str
    questions_file_path_hindi_local: Optional[str] = None
    questions_file_path_hindi_web: Optional[str] = None
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    session_number: str

    # Processing metadata
    started_by: Optional[str] = None
    notes: Optional[str] = None


class LocalExtractionPageData(BaseModel):
    """Data structure for a single page during LOCAL_EXTRACTION state"""

    has_tables: bool
    num_tables: int
    text: str
    errors: Optional[List[str]] = Field(default_factory=list)


class LocalExtractionData(BaseModel):
    """Data structure for LOCAL_EXTRACTION state"""

    status: ProcessingStatus
    processing_metadata: ProcessingMetadata
    pages: Dict[int, LocalExtractionPageData]
    extracted_text_path: str
    extracted_tables_path: Optional[str] = None
    table_metadata: List[TableMetadata] = Field(default_factory=list)
    error_message: Optional[str] = None

    # Document-level table summary (aggregated from page-level data)
    has_tables: bool = Field(default=False, description="True if any page in the document has tables")
    total_tables: int = Field(default=0, description="Total number of tables across all pages")
    pages_with_tables: int = Field(default=0, description="Number of pages that contain tables")

    @model_validator(mode="after")
    def calculate_document_level_summary(self):
        """Calculate document-level table summary from page-level data."""
        if self.pages:
            # Calculate aggregated values
            self.total_tables = sum(page.num_tables for page in self.pages.values())
            self.pages_with_tables = sum(1 for page in self.pages.values() if page.has_tables)
            self.has_tables = any(page.has_tables for page in self.pages.values())
        else:
            # No pages means no tables
            self.total_tables = 0
            self.pages_with_tables = 0
            self.has_tables = False
        return self


class LlmExtractionPageData(BaseModel):
    """Data structure for a single page during LLM_EXTRACTION state"""

    has_tables: bool
    num_tables: int
    text: str

    # Separate fields for different table types
    single_page_tables: List[Dict[str, Any]] = Field(default_factory=list)
    multi_page_table_file_path: Optional[str] = None  # Key for multi_page_table_files lookup

    errors: Optional[List[str]] = Field(default_factory=list)

    # Table metadata
    has_multi_page_tables: bool = False
    has_multiple_tables: bool = False
    table_file_name: Optional[str] = None
    text_file_name: Optional[str] = None


class TableType(Enum):
    """Enum for table types during manual review"""

    SINGLE_PAGE = "single_page"
    MULTI_PAGE_START = "multi_page_start"
    MULTI_PAGE_MIDDLE = "multi_page_middle"
    MULTI_PAGE_END = "multi_page_end"


class ManualReviewTableData(BaseModel):
    """Data structure for a table during manual review"""

    id: str
    content: Dict[str, Any]
    table_type: TableType = TableType.SINGLE_PAGE


class ManualReviewPageData(BaseModel):
    """Data structure for a single page during MANUAL_REVIEW state"""

    text: str
    has_tables: bool
    num_tables: int
    has_multiple_tables: bool
    is_multi_page_table_starting_page: bool = False
    is_multi_page_table_ending_page: bool = False
    is_multi_page_table_middle_page: bool = False
    has_multi_page_tables: bool
    tables: List[ManualReviewTableData] = Field(default_factory=list)
    passed_review: bool = False
    flags: List[IssueFlag] = Field(default_factory=list)

    # Granular edit tracking
    text_edited: bool = False
    tables_edited_ids: List[str] = Field(default_factory=list)


class PrepareDataData(BaseModel):
    """Data structure for PREPARE_DATA state (minimal implementation)"""

    status: ProcessingStatus
    processing_metadata: ProcessingMetadata
    data: Dict[str, Any]
    error_message: Optional[str] = None


# Type alias for backward compatibility and type unions
PageData = Union[LocalExtractionPageData, LlmExtractionPageData, ManualReviewPageData]


class QuestionProcessingProgressStateData(BaseModel):
    """Question processing specific state data structure for progress file states array"""

    status: ProcessingStatus
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)
    state: ProcessingState
    meta: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)

    # Transition metadata for audit trail
    transition_reason: Optional[TransitionReason] = Field(
        default=None,
        description="Reason for transition: 'automatic_progression', 'manual_rollback', 'error_recovery', etc.",
    )
    triggered_by: Optional[TriggerSource] = Field(
        default=None, description="Who/what triggered the transition: user, system, etc."
    )
    previous_state: Optional[ProcessingState] = Field(
        default=None, description="Previous state (especially useful for rollbacks)"
    )

    @field_validator("state", mode="before")
    def validate_state(cls, v):
        """Validate and convert state to ProcessingState enum"""
        if isinstance(v, str):
            try:
                return ProcessingState(v)
            except ValueError:
                raise ValueError(f"Invalid state: {v}") from None
        return v

    @field_validator("previous_state", mode="before")
    def validate_previous_state(cls, v):
        """Validate and convert previous_state to ProcessingState enum"""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return ProcessingState(v)
            except ValueError:
                raise ValueError(f"Invalid previous_state: {v}") from None
        return v

    @field_validator("transition_reason", mode="before")
    def validate_transition_reason(cls, v):
        """Validate and convert transition_reason to TransitionReason enum"""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return TransitionReason(v)
            except ValueError:
                raise ValueError(f"Invalid transition_reason: {v}") from None
        return v

    @field_validator("triggered_by", mode="before")
    def validate_triggered_by(cls, v):
        """Validate and convert triggered_by to TriggerSource enum"""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return TriggerSource(v)
            except ValueError:
                raise ValueError(f"Invalid triggered_by: {v}") from None
        return v


class LlmExtractionData(BaseModel):
    """Data structure for LLM_EXTRACTION state"""

    status: ProcessingStatus
    processing_metadata: ProcessingMetadata
    pages: Dict[int, LlmExtractionPageData]
    extracted_text_path: str
    extracted_tables_path: Optional[str] = None
    error_message: Optional[str] = None

    # Table statistics
    total_tables: int = 0
    successful_tables: int = 0
    failed_tables: int = 0
    multi_page_tables: int = 0
    single_page_tables: int = 0
    multi_page_table_files: Optional[Dict[str, Dict[str, Any]]] = None


class ManualReviewData(BaseModel):
    """Data structure for MANUAL_REVIEW state"""

    status: ProcessingStatus
    processing_metadata: ProcessingMetadata
    pages: Dict[int, ManualReviewPageData]
    error_message: Optional[str] = None


# Type alias for backward compatibility and state-specific type unions
PageProcessingData = Union[InitializedData, LocalExtractionData, LlmExtractionData, ManualReviewData, PrepareDataData]


class ChunkingData(BaseModel):
    """Data structure for chunking step (different from page-based steps)"""

    chunks_path: str
    num_chunks: int
    chunk_size: int
    overlap_size: int
    chunking_strategy: str


class ProgressFileStructure(BaseProgressFileStructure):
    """Complete structure of the progress file"""

    current_state: ProcessingState  # Override to use enum instead of string
    states: List[QuestionProcessingProgressStateData]  # Array of state entries with audit trail

    @field_validator("current_state", mode="before")
    def validate_current_state(cls, v):
        """Validate and convert current_state to ProcessingState enum"""
        if isinstance(v, str):
            try:
                return ProcessingState(v)
            except ValueError:
                raise ValueError(f"Invalid current_state: {v}") from None
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_state_consistency(cls, values):
        """Validate overall state consistency"""
        current_state = values.get("current_state")
        states = values.get("states", [])

        if current_state and states:
            # Convert string to enum if necessary
            if isinstance(current_state, str):
                try:
                    current_state_enum = ProcessingState(current_state)
                except ValueError:
                    raise ValueError(f"Invalid current_state: {current_state}") from None
            else:
                current_state_enum = current_state

            # Ensure current state data exists in array
            current_state_found = False
            for state_entry in states:
                if isinstance(state_entry, dict) and "state" in state_entry:
                    if state_entry["state"] == current_state_enum.value:
                        current_state_found = True
                        break

            if not current_state_found:
                raise ValueError(f"Current state {current_state} not found in states") from None

            # Validate state ordering (audit trail aware)
            # In audit trail mode, we only validate the active progression up to current state
            current_index = STATE_ORDER.index(current_state_enum)

            # Check if any rollback has occurred to determine validation mode
            has_rollback = any(
                state_entry.get("meta", {}).get("rollback_target") is not None
                for state_entry in states
                if isinstance(state_entry, dict)
            )

            if has_rollback:
                # Audit trail mode: Allow all states since history is preserved
                # Only validate that current state exists (already done above)
                pass
            else:
                # Normal progression mode: Validate no future states exist
                seen_states = set()
                for state_entry in states:
                    if isinstance(state_entry, dict) and "state" in state_entry:
                        # Convert state key to enum
                        try:
                            state_enum = ProcessingState(state_entry["state"])
                        except ValueError:
                            raise ValueError(f"Invalid state in states array: {state_entry['state']}") from None

                        # For normal progression, check ordering
                        state_index = STATE_ORDER.index(state_enum)
                        if state_index > current_index and state_enum not in seen_states:
                            raise ValueError(
                                f"Future state {state_enum} should not exist when current state is {current_state_enum}"
                            )
                        seen_states.add(state_enum)

        return values

    def can_transition_to(self, target_state: ProcessingState) -> bool:
        """Check if transition to target state is valid"""
        # Get the current state data from states array (search from end for most recent)
        current_state_data = None
        for state_entry in reversed(self.states):
            if state_entry.state == self.current_state:
                # For transition validation, we need to reconstruct the state data object
                # For now, just pass None - validation will be based on state rules only
                current_state_data = None
                break

        return StateTransitionValidator.validate_transition(
            current_state=self.current_state,
            target_state=target_state,
            current_state_data=current_state_data,
        )

    def get_transition_details(self, target_state: ProcessingState) -> Dict[str, Any]:
        """Get detailed transition validation information"""
        # Get the current state data from states array (search from end for most recent)
        current_state_data = None
        for state_entry in reversed(self.states):
            if state_entry.state == self.current_state:
                # For transition validation, we need to reconstruct the state data object
                # For now, just pass None - validation will be based on state rules only
                current_state_data = None
                break

        return StateTransitionValidator.get_validation_details(
            current_state=self.current_state,
            target_state=target_state,
            current_state_data=current_state_data,
        )


class StateTransition(BaseModel):
    """Defines a valid state transition"""

    from_state: ProcessingState
    to_state: ProcessingState
    required_status: Optional[ProcessingStatus] = None
    condition: Optional[TransitionCondition] = None  # e.g., HAS_TABLES for LLM_EXTRACTION

    @field_validator("condition", mode="before")
    def validate_condition(cls, v):
        """Validate and convert condition to TransitionCondition enum"""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return TransitionCondition(v)
            except ValueError:
                raise ValueError(f"Invalid condition: {v}") from None
        return v


# Define valid transitions
VALID_TRANSITIONS = [
    StateTransition(from_state=ProcessingState.NOT_STARTED, to_state=ProcessingState.INITIALIZED),
    StateTransition(from_state=ProcessingState.INITIALIZED, to_state=ProcessingState.LOCAL_EXTRACTION),
    StateTransition(
        from_state=ProcessingState.LOCAL_EXTRACTION,
        to_state=ProcessingState.LLM_EXTRACTION,
        required_status=ProcessingStatus.SUCCESS,
        condition=TransitionCondition.HAS_TABLES,
    ),
    StateTransition(
        from_state=ProcessingState.LOCAL_EXTRACTION,
        to_state=ProcessingState.MANUAL_REVIEW,
        required_status=ProcessingStatus.SUCCESS,
        condition=TransitionCondition.NO_TABLES,
    ),
    StateTransition(
        from_state=ProcessingState.LLM_EXTRACTION,
        to_state=ProcessingState.LLM_EXTRACTION,
    ),
    StateTransition(
        from_state=ProcessingState.LLM_EXTRACTION,
        to_state=ProcessingState.MANUAL_REVIEW,
        required_status=ProcessingStatus.SUCCESS,
    ),
    StateTransition(
        from_state=ProcessingState.MANUAL_REVIEW,
        to_state=ProcessingState.PREPARE_DATA,
        required_status=ProcessingStatus.SUCCESS,
    ),
    StateTransition(
        from_state=ProcessingState.PREPARE_DATA,
        to_state=ProcessingState.CHUNKING,
        required_status=ProcessingStatus.SUCCESS,
    ),
]

# Define the sequential order of processing states for rollback logic
STATE_ORDER = [
    ProcessingState.NOT_STARTED,
    ProcessingState.INITIALIZED,
    ProcessingState.LOCAL_EXTRACTION,
    ProcessingState.LLM_EXTRACTION,
    ProcessingState.MANUAL_REVIEW,
    ProcessingState.PREPARE_DATA,
    ProcessingState.CHUNKING,
]


class StateTransitionValidator(BaseModel):
    """Pydantic-based state transition validator"""

    @staticmethod
    def validate_transition(
        current_state: ProcessingState,
        target_state: ProcessingState,
        current_state_data: Optional[Union[PageProcessingData, ChunkingData]] = None,
    ) -> bool:
        """
        Validate if a state transition is allowed using Pydantic validation.

        Args:
            current_state: The source state
            target_state: The target state
            current_state_data: Current state data for condition checking

        Returns:
            True if transition is valid, False otherwise
        """
        # Find valid transition rule
        transition_rule = None
        for transition in VALID_TRANSITIONS:
            if transition.from_state == current_state and transition.to_state == target_state:
                transition_rule = transition
                break

        if not transition_rule:
            return False

        # Check status requirement
        if transition_rule.required_status and current_state_data:
            if isinstance(current_state_data, PageProcessingData):
                if current_state_data.status != transition_rule.required_status:
                    return False

        # Check condition requirement
        if transition_rule.condition and current_state_data:
            if isinstance(current_state_data, PageProcessingData):
                if not StateTransitionValidator._check_condition(current_state_data, transition_rule.condition):
                    return False

        return True

    @staticmethod
    def _check_condition(state_data: PageProcessingData, condition: str) -> bool:
        """Check if a transition condition is met"""
        if condition == "has_tables":
            return any(page.has_tables for page in state_data.pages.values())
        elif condition == "no_tables":
            return not any(page.has_tables for page in state_data.pages.values())
        return False

    @staticmethod
    def get_validation_details(
        current_state: ProcessingState,
        target_state: ProcessingState,
        current_state_data: Optional[Union[PageProcessingData, ChunkingData]] = None,
    ) -> Dict[str, Any]:
        """Get detailed validation information for debugging"""
        # Find transition rule
        transition_rule = None
        for transition in VALID_TRANSITIONS:
            if transition.from_state == current_state and transition.to_state == target_state:
                transition_rule = transition
                break

        if not transition_rule:
            return {
                "is_valid": False,
                "current_state": current_state.value,
                "target_state": target_state.value,
                "error": f"No valid transition defined from {current_state} to {target_state}",
                "details": {"transition_exists": False},
            }

        details = {
            "transition_exists": True,
            "required_status": transition_rule.required_status.value if transition_rule.required_status else None,
            "condition": transition_rule.condition.value if transition_rule.condition else None,
        }

        # Check status requirement
        status_valid = True
        if transition_rule.required_status:
            if not current_state_data or not isinstance(current_state_data, PageProcessingData):
                status_valid = False
                details["status_check"] = "No state data found"
            elif current_state_data.status != transition_rule.required_status:
                status_valid = False
                details["status_check"] = (
                    f"Current status is {current_state_data.status.value}, required {transition_rule.required_status.value}"
                )
            else:
                details["status_check"] = "Status requirement met"
        else:
            details["status_check"] = "No status requirement"

        # Check condition
        condition_valid = True
        if transition_rule.condition:
            if not current_state_data or not isinstance(current_state_data, PageProcessingData):
                condition_valid = False
                details["condition_check"] = "No state data found for condition check"
            else:
                condition_met = StateTransitionValidator._check_condition(
                    current_state_data, transition_rule.condition.value
                )
                condition_valid = condition_met
                details["condition_check"] = (
                    f"Condition '{transition_rule.condition.value}' {'met' if condition_met else 'not met'}"
                )
        else:
            details["condition_check"] = "No condition requirement"

        is_valid = status_valid and condition_valid

        return {
            "is_valid": is_valid,
            "current_state": current_state.value,
            "target_state": target_state.value,
            "error": None if is_valid else "Transition requirements not met",
            "details": details,
        }
