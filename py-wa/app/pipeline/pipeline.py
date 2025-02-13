import os
import json
import logging
from pathlib import Path
from typing import List, Any, Dict, Optional

from .types import PipelineStep, PipelineConfig, ProgressIteration
from .progress import get_last_iteration, create_new_iteration, log_progress
from .exceptions import PipelineError, PipelineStepError

logger = logging.getLogger(__name__)

def initialize_directories(progress_dir: str, progress_file: str) -> None:
    """
    Initializes the necessary directories and progress file.

    Creates the progress directory if it doesn't exist (including parent directories).
    If the progress file doesn't exist, it creates it and initializes it with an empty JSON array.

    Args:
        progress_dir: The path to the directory where progress information will be stored.
        progress_file: The path to the file that will store progress information (as a JSON array).

    Returns:
        None
    """
    # Ensure the progress directory exists. Create it recursively if necessary.
    os.makedirs(progress_dir, exist_ok=True)  # Using exist_ok=True is best practice to avoid errors if the directory already exists

    # Check if the progress file exists
    if not os.path.exists(progress_file):
        # If it doesn't exist, create it and initialize with an empty JSON array.
        try:
            with open(progress_file, 'w') as f: # Use 'with open' for automatic file closing (best practice)
                json.dump([], f) # Use json.dump to serialize a Python list to JSON and write to the file
        except IOError as e:
            # Handle potential file writing errors gracefully (best practice)
            print(f"Error writing to progress file '{progress_file}': {e}")
            # Consider raising the exception again or handling it in a way appropriate for your application
            raise

async def orchestrate_pipeline(
    outputs: Dict[str, Any],
    steps: List[PipelineStep],
    resume_from_last_successful: bool = True
) -> Any:
    """
    Orchestrate the execution of pipeline steps.
    
    Args:
        outputs: Initial outputs and configuration
        steps: List of pipeline steps to execute
        resume_from_last_successful: Whether to resume from last successful state
        
    Returns:
        Any: Output from the last successful step
        
    Raises:
        PipelineError: If pipeline execution fails
    """
    progress_file = Path(outputs["progress_file"])
    previous_iteration = await get_last_iteration(progress_file)
    
    # Check if previous iteration was completely successful
    if (resume_from_last_successful and 
        previous_iteration and 
        len(previous_iteration.steps) == len(steps) and 
        all(step.status == "SUCCESS" for step in previous_iteration.steps)):
        
        logger.info("All steps were previously completed successfully. Returning last step output.")
        last_step = previous_iteration.steps[-1]
        last_step_data = json.loads(last_step.log_file.read_text())
        return last_step_data["data"]
    
    current_iteration = await create_new_iteration(progress_file)
    
    # Resume from last successful step if applicable
    if previous_iteration and (
        len(steps) != len(previous_iteration.steps) or 
        previous_iteration.steps[-1].status != "SUCCESS"
    ):
        for s, prev_step in enumerate(previous_iteration.steps):
            if prev_step.status == "SUCCESS":
                current_iteration.steps.append(prev_step)
                step_output = json.loads(prev_step.log_file.read_text())
                outputs.update(step_output["data"])
            else:
                break
    
    last_step_output = None
    
    # Execute pipeline steps
    for i, step in enumerate(steps):
        progress_step = next(
            (s for s in current_iteration.steps if s.step == i),
            None
        )
        
        if progress_step and progress_step.status == "SUCCESS":
            logger.info(f"Step {i} ({step.name}) already completed successfully.")
            outputs.update(step.output or {})
            last_step_output = step.output
            continue
            
        try:
            logger.info(f"Executing step {i} ({step.name})...")
            result = await step.function(outputs)
            
            status = result.pop("status", "SUCCESS")
            step.status = status
            step.output = result
            outputs.update(result)
            last_step_output = result
            
            if step.status != "SUCCESS":
                raise PipelineStepError(
                    "Step execution failed",
                    step.name,
                    i,
                    {"status": status}
                )
            
            await log_progress(
                Path(outputs["progress_dir"]),
                progress_file,
                {
                    "message": f"Step {i} ({step.name}) completed successfully.",
                    "data": step.output,
                    "key": f"STEP_{i}_{step.status}_{step.name}"
                },
                "SUCCESS",
                current_iteration
            )
            
        except Exception as e:
            step.status = step.status or "FAILURE"
            await log_progress(
                Path(outputs["progress_dir"]),
                progress_file,
                {
                    "message": f"Step {i} ({step.name}) failed.",
                    "data": step.output or {},
                    "error": {"error": [str(e), step.error]} if step.status != "PARTIAL" else {},
                    "key": f"STEP_{i}_{step.status}_{step.name}"
                },
                step.status,
                current_iteration
            )
            
            error_msg = f"Step {i} ({step.name}) failed. Manual intervention required."
            logger.error(error_msg)
            raise PipelineError(error_msg, {"step": i, "name": step.name})
    
    return last_step_output

async def run_pipeline(
    steps: List[PipelineStep],
    initial_outputs: Dict[str, Any],
    progress_dir: Path,
    progress_file: Path,
    resume_from_last_successful: bool = True
) -> Any:
    """
    Run the pipeline with the given configuration.
    
    Args:
        steps: List of pipeline steps to execute
        initial_outputs: Initial data for the pipeline
        progress_dir: Directory for progress tracking
        progress_file: File for storing progress state
        resume_from_last_successful: Whether to resume from last successful state
        
    Returns:
        Any: Output from the last successful step
        
    Raises:
        PipelineError: If pipeline execution fails
    """
    progress_dir.mkdir(parents=True, exist_ok=True)
    if not progress_file.exists():
        progress_file.write_text(json.dumps([]))
    
    try:
        outputs = {
            **initial_outputs,
            "progress_dir": str(progress_dir),
            "progress_file": str(progress_file)
        }
        return await orchestrate_pipeline(outputs, steps, resume_from_last_successful)
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise

