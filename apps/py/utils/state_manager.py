import json
import logging
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel

# Configure structured logging for state manager
logger = logging.getLogger(__name__)

# Type variable for the state enum
StateEnum = TypeVar("StateEnum", bound=Enum)


class StateData(BaseModel):
    """Generic state data structure"""

    status: str
    data: Dict[str, Any] = {}
    meta: Dict[str, Any] = {}
    errors: List[str] = []


class BaseProgressFileStructure(BaseModel):
    """Generic base structure for progress files"""

    current_state: str  # Store as string to be enum-agnostic
    created_at: datetime
    updated_at: datetime
    # Note: states field is defined in subclasses with specific typing


class ProgressStateManager(Generic[StateEnum]):
    """
    Generic state machine manager that persists state to JSON files.

    This class is domain-agnostic and can be used for any workflow that needs
    state tracking with file persistence (document processing, approvals, pipelines, etc.).
    """

    def __init__(self, file_path: Union[str, Path], initial_state: StateEnum):
        """
        Initialize the state manager.

        Args:
            file_path: Path to the progress file
            initial_state: Initial state for the domain

        Raises:
            ValueError: If file_path is not provided
            IOError: If progress file cannot be created
        """
        self.progress_file = Path(file_path)
        self.initial_state = initial_state

        # Ensure progress file exists or create it
        if not self.progress_file.exists():
            self._initialize_progress_file()

    def _initialize_progress_file(self) -> None:
        """
        Initialize a new progress file with basic structure.
        Domain will set the first state when ready.

        Raises:
            IOError: If file cannot be created
        """
        logger.info(
            "Initializing new progress file",
            extra={"progress_file": str(self.progress_file)},
        )

        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        # Create file with basic structure, no current_state set
        initial_progress = {
            "current_state": None,  # Will be set by first domain transition
            "states": {},
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(initial_progress, f, indent=2, default=str)
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
            ValueError: If progress file cannot be read or has invalid JSON
        """
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(
                "Progress file is invalid or missing, falling back to initial structure",
                extra={"progress_file": str(self.progress_file), "error": str(e)},
            )
            return self._get_initial_progress_data()
        except Exception as e:
            logger.error(
                "Failed to read progress file", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise ValueError(f"Failed to read progress file: {e}") from e

        # Only handle core infrastructure fields
        now = datetime.now(UTC)
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

    def _get_initial_progress_data(self) -> Dict[str, Any]:
        """
        Get minimal initial progress data structure.
        Only includes core infrastructure fields.

        Returns:
            Dict with minimal progress structure
        """
        return {
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

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
                json.dump(progress_data, f, indent=2, default=str)
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

    def get_state_data(self, state: Union[StateEnum, str]) -> Optional[StateData]:
        """
        Get data for a specific state.

        Args:
            state: The state to get data for (Enum or string)

        Returns:
            State data if found, None otherwise

        Raises:
            ValueError: If progress file is invalid or state is invalid
        """
        progress = self.read_progress_file()
        state_key = state.value if isinstance(state, Enum) else state
        return progress["states"].get(state_key)

    def transition_to_state(self, new_state: Union[StateEnum, str], state_data: StateData) -> None:
        """
        Transition to a new state with data.

        Args:
            new_state: The target state to transition to (Enum or string)
            state_data: Complete state data for the new state

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

        # Update the progress structure
        progress["current_state"] = new_state_str
        progress["states"][new_state_str] = state_data
        progress["updated_at"] = datetime.now(UTC)

        # Validate the entire structure before writing
        try:
            # This will trigger all Pydantic validators
            validated_progress = BaseProgressFileStructure(**progress)
        except Exception as e:
            logger.error(
                "State transition failed validation",
                extra={
                    "progress_file": str(self.progress_file),
                    "from_state": old_state,
                    "to_state": new_state_str,
                    "error": str(e),
                },
            )
            raise ValueError(f"State transition failed validation: {e}") from e

        # Write the validated data back to file
        self._write_validated_progress(validated_progress.model_dump())

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

        # Remove all states after the target state
        states_to_remove = []
        for i in range(target_index + 1, len(state_order_str)):
            state_to_remove = state_order_str[i]
            if state_to_remove in progress["states"]:
                states_to_remove.append(state_to_remove)

        for state in states_to_remove:
            del progress["states"][state]

        progress["updated_at"] = datetime.now(UTC)

        logger.debug(
            "Removed states during rollback",
            extra={"progress_file": str(self.progress_file), "removed_states": states_to_remove},
        )

        # Validate and write
        try:
            validated_progress = BaseProgressFileStructure(**progress)
        except Exception as e:
            logger.error(
                "Rollback failed validation",
                extra={"progress_file": str(self.progress_file), "target_state": target_state_str, "error": str(e)},
            )
            raise ValueError(f"Rollback failed validation: {e}") from e

        self._write_validated_progress(validated_progress.model_dump())

        logger.info(
            "Rollback completed successfully",
            extra={
                "progress_file": str(self.progress_file),
                "from_state": current_state,
                "to_state": target_state_str,
                "removed_states": states_to_remove,
            },
        )
