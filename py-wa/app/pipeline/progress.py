import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.project_root import find_project_root
from .exceptions import FileOperationError, ProgressError
from .types import ProgressData, ProgressIteration, ProgressStep, StepStatus


def initialize_progress(progress_dir: Path, progress_file: Path) -> None:
    """Initialize progress tracking directory and file."""
    try:
        progress_dir.mkdir(parents=True, exist_ok=True)

        if not progress_file.exists():
            progress_file.write_text(json.dumps([]))
    except OSError as e:
        raise ProgressError(f"Failed to initialize progress: {e}") from e


async def create_new_iteration(progress_file: Path) -> ProgressIteration:
    """Create a new progress iteration.

    Args:
        progress_file: Path to the progress tracking file

    Returns:
        ProgressIteration: New iteration object

    Raises:
        FileOperationError: If file operations fail
    """
    try:
        progress_status = json.loads(progress_file.read_text())
        return ProgressIteration(iteration=len(progress_status) + 1, timestamp=datetime.now(), steps=[])
    except Exception as e:
        raise FileOperationError(str(e), str(progress_file), "read", {"error_type": "json_decode"}) from e


async def get_last_iteration(progress_file: Path) -> Optional[ProgressIteration]:
    """Get the last recorded iteration.

    Args:
        progress_file: Path to the progress tracking file

    Returns:
        Optional[ProgressIteration]: Last iteration if exists, None otherwise

    Raises:
        FileOperationError: If file operations fail
    """
    try:
        progress_status = json.loads(progress_file.read_text())
        if not progress_status:
            return None
        return ProgressIteration.model_validate(progress_status[-1])
    except Exception as e:
        raise FileOperationError(str(e), str(progress_file), "read", {"error_type": "json_decode"}) from e


async def log_progress(
    progress_dir: Path,
    progress_file: Path,
    progress_data: Dict[str, Any],
    status: StepStatus,
    iteration: ProgressIteration,
) -> None:
    """Log progress for current pipeline step.

    Args:
        progress_dir: Directory for progress files
        progress_file: Main progress tracking file
        progress_data: Data to log
        status: Status of the current step
        iteration: Current iteration object

    Raises:
        ProgressError: If progress logging fails
    """
    try:
        # Convert dict to ProgressData object
        if not isinstance(progress_data, ProgressData):
            progress_data = ProgressData(**progress_data)

        # Read current progress status
        progress_status = json.loads(progress_file.read_text())

        # Create log file path
        log_file = progress_dir / f"{iteration.iteration}.{progress_data.key}.log.json"
        project_root = Path(find_project_root())
        relative_log_file = log_file.relative_to(project_root)

        # Update iteration steps
        # iteration.steps.append({"step": len(iteration.steps), "log_file": relative_log_file, "status": status})
        iteration.steps.append(ProgressStep(step=len(iteration.steps), log_file=relative_log_file, status=status))

        # Write progress data to log file using model_dump_json instead of json()
        log_file.write_text(progress_data.model_dump_json(indent=2))

        # Update progress status file using model_dump_json
        existing_index = next(
            (i for i, iter in enumerate(progress_status) if iter["iteration"] == iteration.iteration), -1
        )

        if existing_index != -1:
            progress_status[existing_index] = json.loads(iteration.model_dump_json())
        else:
            progress_status.append(json.loads(iteration.model_dump_json()))

        progress_file.write_text(json.dumps(progress_status, indent=2))

    except Exception as e:
        raise ProgressError(f"Failed to log progress: {e}", {"original_error": str(e)}) from e
