import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from ..types import BaseProgressFileStructure
from ..types.models import GenericStateData
from .file_utils import safe_mkdir_with_conflict_detection
from .timestamps import get_current_timestamp, get_current_timestamp_iso

# Configure structured logging for state manager
logger = logging.getLogger(__name__)

# Type variable for the state enum
StateEnum = TypeVar("StateEnum", bound=Enum)

# Import the generic state data from types


class ProgressStateManager(Generic[StateEnum]):
    """
    Generic state machine manager that persists state to JSON files.

    ARCHITECTURAL DESIGN:
    This class is intentionally domain-agnostic and generic to support any workflow
    that needs state tracking with file persistence (document processing, approvals,
    pipelines, etc.).

    WHY DICTS INSTEAD OF STRICT TYPES:
    - Generic Design: Cannot know about specific domain types (ProcessingState, LocalExtractionData, etc.)
    - Domain Separation: Business logic should be separate from infrastructure
    - Flexibility: Different domains can store different data structures using the same state manager
    - Future-Proof: New domains and state enums can use this without modification

    RESPONSIBILITY SEPARATION:
    - State Manager: Handles state transitions, persistence, rollbacks (infrastructure)
    - Domain Layer: Handles type conversion, domain-specific validation (business logic)
    - ProgressFileStructure: Domain-specific validation for document processing only

    USAGE PATTERN:
    1. Domain creates StateEnum (ProcessingState, ApprovalState, etc.)
    2. Domain converts typed objects to/from dicts when calling state manager
    3. State manager stores/retrieves dicts without knowing their internal structure
    4. Domain validates retrieved dicts and converts back to typed objects
    """

    def __init__(
        self,
        file_path: Union[str, Path],
        initial_state: StateEnum,
        initial_state_data: Optional[GenericStateData] = None,
    ):
        """
        Initialize the state manager.

        Args:
            file_path: Path to the progress file
            initial_state: Initial state for the domain
            initial_state_data: Optional initial state data. If not provided, creates minimal entry.

        Raises:
            ValueError: If file_path is not provided
            IOError: If progress file cannot be created
        """
        self.progress_file = Path(file_path)
        self.initial_state = initial_state
        self.initial_state_data = initial_state_data

        # Ensure progress file exists and has content, or create/initialize it
        if not self.progress_file.exists() or self.progress_file.stat().st_size == 0:
            self._initialize_progress_file()

    def _json_serializer(self, obj):
        """Custom JSON serializer that handles enums and other types"""
        if isinstance(obj, Enum):
            return obj.value  # Convert enum to its value
        return str(obj)  # Fallback to string for other types

    def _validate_and_write_progress(self, progress_data: Dict[str, Any], operation_context: str) -> None:
        """
        Validate progress data and write to file.

        Args:
            progress_data: Progress data dictionary to validate and write
            operation_context: Description of the operation for error logging

        Raises:
            ValueError: If validation fails
            IOError: If file cannot be written
        """
        try:
            validated_progress = BaseProgressFileStructure(**progress_data)
        except Exception as e:
            logger.error(
                f"{operation_context} failed validation",
                extra={"progress_file": str(self.progress_file), "error": str(e)},
            )
            raise ValueError(f"{operation_context} failed validation: {e}") from e

        self._write_validated_progress(validated_progress.model_dump())

    def _initialize_progress_file(self) -> None:
        """
        Initialize a new progress file with array-based structure.
        Creates a minimal state entry if no initial data was provided.

        Raises:
            IOError: If file cannot be created
        """
        logger.info(
            "Initializing new progress file",
            extra={"progress_file": str(self.progress_file)},
        )

        # Create directory structure safely
        safe_mkdir_with_conflict_detection(self.progress_file.parent)

        # If no initial data provided, create minimal state entry
        if self.initial_state_data is None:
            self.initial_state_data = GenericStateData(
                state=self.initial_state.value,
                status="SUCCESS",
                timestamp=get_current_timestamp(),
                data={},
                meta={"auto_generated": True},
                errors=[],
            )

        # Create file with array-based structure
        initial_progress = {
            "current_state": self.initial_state.value,
            "states": [self.initial_state_data.model_dump()],
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp(),
        }

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(initial_progress, f, indent=2, default=self._json_serializer)
            logger.debug("Progress file initialized successfully", extra={"progress_file": str(self.progress_file)})
        except Exception as e:
            logger.error(
                "Failed to initialize progress file", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise IOError(f"Failed to initialize progress file: {e}") from e

    def read_progress_file(self) -> Dict[str, Any]:
        """
        Read and parse a progress file as raw data.
        Only validates core infrastructure fields, not domain-specific content.

        Returns:
            Dict containing progress data

        Raises:
            FileNotFoundError: If progress file doesn't exist
            ValueError: If progress file has invalid JSON or structure
        """
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(
                "Progress file not found",
                extra={"progress_file": str(self.progress_file)},
            )
            raise FileNotFoundError(f"Progress file not found: {self.progress_file}") from None
        except json.JSONDecodeError as e:
            logger.error(
                "Progress file contains invalid JSON",
                extra={"progress_file": str(self.progress_file), "error": str(e)},
            )
            raise ValueError(f"Progress file contains invalid JSON: {e}") from e
        except Exception as e:
            logger.error(
                "Failed to read progress file", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise ValueError(f"Failed to read progress file: {e}") from e

        # Only handle core infrastructure fields
        now = get_current_timestamp()
        fields_added = []

        if "created_at" not in data:
            data["created_at"] = now
            fields_added.append("created_at")
        if "updated_at" not in data:
            data["updated_at"] = now
            fields_added.append("updated_at")

        if fields_added:
            logger.warning(
                "Progress file missing core infrastructure fields, adding defaults",
                extra={"progress_file": str(self.progress_file), "missing_fields": fields_added},
            )

        logger.debug(
            "Progress file read successfully",
            extra={"progress_file": str(self.progress_file)},
        )
        return data

    def _write_validated_progress(self, progress_data: Dict[str, Any]) -> None:
        """
        Write progress data to file.

        Args:
            progress_data: Progress data dictionary to write

        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, default=self._json_serializer)
        except Exception as e:
            raise IOError(f"Failed to write progress file: {e}") from e

    def get_current_state(self) -> str:
        """
        Get the current state as string.

        Returns:
            Current state string

        Raises:
            ValueError: If progress file is invalid
        """
        progress = self.read_progress_file()
        return progress["current_state"]

    def get_state_data(self, state: Union[StateEnum, str]) -> Optional[GenericStateData]:
        """
        Get data for a specific state from the states array.

        NOTE: Returns GenericStateData objects (which contain dicts in the 'data' field).
        The domain layer is responsible for converting the 'data' dict back to
        domain-specific typed objects (LocalExtractionData, etc.).

        Args:
            state: The state to get data for (Enum or string)

        Returns:
            State data if found, None otherwise

        Raises:
            ValueError: If progress file is invalid or state entries are malformed
        """
        progress = self.read_progress_file()
        state_key = state.value if isinstance(state, Enum) else state

        # Search through states array from end (most recent first)
        for i, state_entry in enumerate(reversed(progress["states"])):
            if not isinstance(state_entry, dict):
                raise ValueError(
                    f"Malformed state entry at index {len(progress['states']) - 1 - i}: expected dict, got {type(state_entry)}"
                )

            if "state" not in state_entry:
                raise ValueError(
                    f"Malformed state entry at index {len(progress['states']) - 1 - i}: missing 'state' field"
                )

            if state_entry["state"] == state_key:
                try:
                    # Convert dict back to GenericStateData object with validation
                    return GenericStateData(**state_entry)
                except Exception as e:
                    raise ValueError(
                        f"Invalid state data structure at index {len(progress['states']) - 1 - i}: {e}"
                    ) from e

        return None

    def transition_to_state(
        self, new_state: Union[StateEnum, str], state_data: GenericStateData, validate_transition: bool = True
    ) -> None:
        """
        Transition to a new state by appending to the states array.

        DOMAIN RESPONSIBILITY: The calling domain should convert their typed objects
        (LocalExtractionData, etc.) to GenericStateData before calling this method. The 'data'
        field in GenericStateData should contain the serialized dict representation.

        Args:
            new_state: The target state to transition to (Enum or string)
            state_data: Complete state data for the new state
            validate_transition: Whether to validate the transition (default: True)

        Raises:
            ValueError: If the transition fails validation
        """
        # Read current progress
        progress = self.read_progress_file()
        old_state = progress["current_state"]

        # Convert state to string if it's an enum
        new_state_str = new_state.value if isinstance(new_state, Enum) else new_state

        logger.info(
            "Transitioning state",
            extra={
                "progress_file": str(self.progress_file),
                "from_state": old_state,
                "to_state": new_state_str,
                "status": state_data.status,
            },
        )

        # Update the progress structure - append to array instead of dict assignment
        progress["current_state"] = new_state_str
        progress["states"].append(state_data.model_dump())
        progress["updated_at"] = get_current_timestamp()

        # Validate the entire structure before writing
        self._validate_and_write_progress(progress, "State transition")

        logger.info(
            "State transition completed successfully",
            extra={"progress_file": str(self.progress_file), "from_state": old_state, "to_state": new_state_str},
        )

    def rollback_to_state(self, target_state: Union[StateEnum, str], state_order: List[Union[StateEnum, str]]) -> None:
        """
        Rollback to a previous state by removing all subsequent states.

        Args:
            target_state: The state to rollback to (Enum or string)
            state_order: Ordered list of states to determine sequence

        Raises:
            ValueError: If target_state is invalid or not reachable
        """
        target_state_str = target_state.value if isinstance(target_state, Enum) else target_state

        # Convert state_order to strings for comparison
        state_order_str = [s.value if isinstance(s, Enum) else s for s in state_order]

        try:
            target_index = state_order_str.index(target_state_str)
        except ValueError:
            logger.error(
                "Invalid rollback target state",
                extra={
                    "progress_file": str(self.progress_file),
                    "target_state": target_state_str,
                    "available_states": state_order_str,
                },
            )
            raise ValueError(f"Invalid target state: {target_state_str}") from None

        # Read current progress
        progress = self.read_progress_file()
        current_state = progress["current_state"]
        current_index = state_order_str.index(current_state)

        if target_index > current_index:
            logger.error(
                "Cannot rollback to future state",
                extra={
                    "progress_file": str(self.progress_file),
                    "current_state": current_state,
                    "target_state": target_state_str,
                },
            )
            raise ValueError(f"Cannot rollback to future state {target_state_str} from current state {current_state}")

        logger.info(
            "Starting rollback operation",
            extra={"progress_file": str(self.progress_file), "from_state": current_state, "to_state": target_state_str},
        )

        # Update current state
        progress["current_state"] = target_state_str

        # Create rollback entries for all states after the target state (audit trail approach)
        # Instead of deleting, we add rollback entries to maintain complete history
        rollback_timestamp = get_current_timestamp()
        states_rolled_back = []

        # Find states that come after the target state and create rollback entries
        for i in range(target_index + 1, len(state_order_str)):
            state_to_rollback = state_order_str[i]

            # Check if this state exists in our current states array
            state_exists = False
            for state_entry in progress["states"]:
                if isinstance(state_entry, dict) and state_entry.get("state") == state_to_rollback:
                    state_exists = True
                    break

            if state_exists:
                # Create rollback entry for audit trail
                rollback_entry = GenericStateData(
                    state=state_to_rollback,
                    status="SUCCESS",
                    timestamp=rollback_timestamp,
                    data={},
                    meta={
                        "rollback_target": target_state_str,
                        "rollback_reason": "manual_rollback",
                        "rollback_from": current_state,
                    },
                    errors=[],
                )
                progress["states"].append(rollback_entry.model_dump())
                states_rolled_back.append(state_to_rollback)

        progress["updated_at"] = get_current_timestamp()

        logger.debug(
            "Created rollback entries during rollback",
            extra={"progress_file": str(self.progress_file), "states_rolled_back": states_rolled_back},
        )

        # Validate and write
        self._validate_and_write_progress(progress, "Rollback")

        logger.info(
            "Rollback completed successfully",
            extra={
                "progress_file": str(self.progress_file),
                "from_state": current_state,
                "to_state": target_state_str,
                "states_rolled_back": states_rolled_back,
            },
        )

    def update_state_data(self, state: Union[StateEnum, str], partial_data: Dict[str, Any]) -> None:
        """
        Update the latest state entry with partial data (upsert approach).

        This method finds the most recent entry for the specified state and merges
        the partial_data into the existing data field, preserving audit trail
        while allowing incremental updates within the same state.

        Args:
            state: The state to update (Enum or string)
            partial_data: Partial data to merge into existing state data

        Raises:
            ValueError: If no existing state entry is found or merge fails
            IOError: If file cannot be written
        """
        state_key = state.value if isinstance(state, Enum) else state

        # Read current progress
        progress = self.read_progress_file()

        # Find the latest entry for this state (search from end)
        target_entry_index = None
        for i, state_entry in enumerate(reversed(progress["states"])):
            if not isinstance(state_entry, dict):
                continue

            if state_entry.get("state") == state_key:
                target_entry_index = len(progress["states"]) - 1 - i
                break

        if target_entry_index is None:
            logger.error(
                "Cannot update state - no existing entry found",
                extra={
                    "progress_file": str(self.progress_file),
                    "target_state": state_key,
                    "available_states": [s.get("state") for s in progress["states"] if isinstance(s, dict)],
                },
            )
            raise ValueError(f"No existing entry found for state {state_key}")

        # Get the target entry
        target_entry = progress["states"][target_entry_index]

        logger.info(
            "Updating state data",
            extra={
                "progress_file": str(self.progress_file),
                "target_state": state_key,
                "entry_index": target_entry_index,
                "partial_data_keys": list(partial_data.keys()),
            },
        )

        # Deep merge partial_data into existing data field
        existing_data = target_entry.get("data", {})
        updated_data = self._deep_merge_dicts(existing_data, partial_data)

        # Update the entry
        target_entry["data"] = updated_data
        target_entry["timestamp"] = get_current_timestamp_iso()
        progress["updated_at"] = get_current_timestamp()

        # Validate and write
        self._validate_and_write_progress(progress, "State update")

        logger.info(
            "State data updated successfully",
            extra={
                "progress_file": str(self.progress_file),
                "target_state": state_key,
                "entry_index": target_entry_index,
            },
        )

    def _deep_merge_dicts(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with update_dict taking precedence.

        Args:
            base_dict: Base dictionary to merge into
            update_dict: Dictionary with updates to apply

        Returns:
            Merged dictionary
        """
        result = base_dict.copy()

        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                # Replace or add the value
                result[key] = value

        return result
