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


class ProgressFileStructure(BaseModel):
    """Generic structure for progress files"""

    meta: Dict[str, Any] = {}
    current_state: str  # Store as string to be enum-agnostic
    states: Dict[str, StateData] = {}
    created_at: datetime
    updated_at: datetime


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
            initial_state: Initial state enum value

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
        Initialize a new progress file with state machine structure.

        Raises:
            IOError: If file cannot be created
        """
        logger.info(
            "Initializing new progress file",
            extra={"progress_file": str(self.progress_file), "initial_state": self.initial_state.value},
        )

        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        # Use Pydantic model for type safety
        initial_progress = ProgressFileStructure(
            meta={},
            current_state=self.initial_state.value,
            states={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(initial_progress.model_dump(), f, indent=2, default=str)
            logger.debug("Progress file initialized successfully", extra={"progress_file": str(self.progress_file)})
        except Exception as e:
            logger.error(
                "Failed to initialize progress file", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise IOError(f"Failed to initialize progress file: {e}") from e

    def read_progress_file(self) -> ProgressFileStructure:
        """
        Read and parse a progress file using Pydantic validation.

        Returns:
            ProgressFileStructure containing validated progress data

        Raises:
            ValueError: If progress file is invalid
        """
        try:
            with open(self.progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Use Pydantic for validation and parsing
            progress = ProgressFileStructure(**data)
            logger.debug(
                "Progress file read successfully",
                extra={
                    "progress_file": str(self.progress_file),
                    "current_state": progress.current_state,
                    "states_count": len(progress.states),
                },
            )
            return progress
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in progress file", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise ValueError(f"Invalid JSON in progress file: {e}") from e
        except Exception as e:
            logger.error(
                "Invalid progress file structure", extra={"progress_file": str(self.progress_file), "error": str(e)}
            )
            raise ValueError(f"Invalid progress file structure: {e}") from e

    def _write_validated_progress(self, validated_progress: ProgressFileStructure) -> None:
        """
        Write validated progress data to file.

        Args:
            validated_progress: Validated ProgressFileStructure to write

        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(validated_progress.model_dump(), f, indent=2, default=str)
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
        return progress.current_state

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
        return progress.states.get(state_key)

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
        old_state = progress.current_state

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
        progress.current_state = new_state_str
        progress.states[new_state_str] = state_data
        progress.updated_at = datetime.now(UTC)

        # Validate the entire structure before writing
        try:
            # This will trigger all Pydantic validators
            validated_progress = ProgressFileStructure(**progress.model_dump())
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
        self._write_validated_progress(validated_progress)

        logger.info(
            "State transition completed successfully",
            extra={"progress_file": str(self.progress_file), "from_state": old_state, "to_state": new_state_str},
        )

    def update_meta(self, meta_data: Dict[str, Any]) -> None:
        """
        Update global metadata in the progress file.

        Args:
            meta_data: New metadata to update/merge

        Raises:
            ValueError: If progress file is invalid or validation fails
        """
        progress = self.read_progress_file()

        # Update the metadata
        progress.meta.update(meta_data)
        progress.updated_at = datetime.now(UTC)

        # Validate the entire structure before writing
        try:
            validated_progress = ProgressFileStructure(**progress.model_dump())
        except Exception as e:
            raise ValueError(f"Updated metadata failed validation: {e}") from e

        # Write the validated data back to file
        self._write_validated_progress(validated_progress)

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
        current_state = progress.current_state
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
        progress.current_state = target_state_str

        # Remove all states after the target state
        states_to_remove = []
        for i in range(target_index + 1, len(state_order_str)):
            state_to_remove = state_order_str[i]
            if state_to_remove in progress.states:
                states_to_remove.append(state_to_remove)

        for state in states_to_remove:
            del progress.states[state]

        progress.updated_at = datetime.now(UTC)

        logger.debug(
            "Removed states during rollback",
            extra={"progress_file": str(self.progress_file), "removed_states": states_to_remove},
        )

        # Validate and write
        try:
            validated_progress = ProgressFileStructure(**progress.model_dump())
        except Exception as e:
            logger.error(
                "Rollback failed validation",
                extra={"progress_file": str(self.progress_file), "target_state": target_state_str, "error": str(e)},
            )
            raise ValueError(f"Rollback failed validation: {e}") from e

        self._write_validated_progress(validated_progress)

        logger.info(
            "Rollback completed successfully",
            extra={
                "progress_file": str(self.progress_file),
                "from_state": current_state,
                "to_state": target_state_str,
                "removed_states": states_to_remove,
            },
        )
