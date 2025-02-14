import os
import json
from pathlib import Path
from typing import List, Any, Dict, Optional

from .types import PipelineStep, PipelineConfig, ProgressIteration, ProgressData
from .progress import get_last_iteration, create_new_iteration, log_progress
from .exceptions import PipelineError, PipelineStepError
from ..utils.logging import setup_logger
from .context import PipelineContext

logger = setup_logger(__name__)

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
    context: PipelineContext,
    outputs: Dict[str, Any],
    steps: List[PipelineStep],
    resume_from_last_successful: bool = True
) -> Any:
    """
    Orchestrate the execution of pipeline steps.
    
    Args:
        context: Pipeline execution context with logger and run_id
        outputs: Initial outputs and configuration
        steps: List of pipeline steps to execute
        resume_from_last_successful: Whether to resume from last successful state
    """
    context.log_pipeline("pipeline_start", total_steps=len(steps))
    
    progress_file = Path(outputs["progress_file"])
    previous_iteration = await get_last_iteration(progress_file)
    
    if previous_iteration:
        context.log_pipeline("previous_iteration_found", step_count=len(previous_iteration.steps))
        
        if (resume_from_last_successful and 
            len(previous_iteration.steps) == len(steps) and 
            all(step.status == "SUCCESS" for step in previous_iteration.steps)):
            
            context.log_pipeline("using_previous_successful_run", iteration=previous_iteration.iteration)
            last_step = previous_iteration.steps[-1]
            last_step_data = json.loads(last_step.log_file.read_text())
            return last_step_data["data"]
    
    current_iteration = await create_new_iteration(progress_file)
    context.log_pipeline("new_iteration_created", iteration=current_iteration.iteration)
    
    last_step_output = None
    
    for i, step in enumerate(steps):
        context.log_step("step_start", i, step.name)
        
        try:
            result = await step.function(outputs, context)
            status = result.pop("status", "SUCCESS")
            step.status = status
            step.output = result
            outputs.update(result)
            last_step_output = result
            
            if step.status != "SUCCESS":
                context.log_step("step_failed", i, step.name, status=status)
                raise PipelineStepError(
                    message="Step execution failed",
                    step_name=step.name,
                    step_number=i,
                    step_context={"status": status}
                )
            
            progress_data = ProgressData(
                message=f"Step {i} ({step.name}) completed successfully.",
                data=step.output,
                key=f"STEP_{i}_{step.status}_{step.name}"
            )
            
            context.log_step("complete", i, step.name, status="SUCCESS")
            await log_progress(
                Path(outputs["progress_dir"]),
                progress_file,
                progress_data,
                "SUCCESS",
                current_iteration
            )
            
        except Exception as e:
            step.status = step.status or "FAILURE"
            context.log_step("failed", i, step.name, status=step.status, error=str(e))
            
            error_data = ProgressData(
                message=f"Step {i} ({step.name}) failed.",
                data=step.output or {},
                error={"error": [str(e), step.error]} if step.status != "PARTIAL" else {},
                key=f"STEP_{i}_{step.status}_{step.name}"
            )
            
            await log_progress(
                Path(outputs["progress_dir"]),
                progress_file,
                error_data,
                step.status,
                current_iteration
            )
            
            raise PipelineError(
                message=f"Step {i} ({step.name}) failed. Manual intervention required.",
                context={"step": i, "name": step.name}
            )
    
    context.log_pipeline("pipeline_complete")
    return last_step_output

async def run_pipeline(
    context: PipelineContext,
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
    context.log_pipeline("pipeline_init")
    
    try:
        progress_dir.mkdir(parents=True, exist_ok=True)
        if not progress_file.exists():
            context.log_pipeline("create_progress_file")
            progress_file.write_text(json.dumps([]))
    except Exception as e:
        context.log_pipeline("init_failed", error=str(e))
        raise PipelineError("Directory initialization failed", {"error": str(e)})
    
    try:
        outputs = {
            **initial_outputs,
            "progress_dir": str(progress_dir),
            "progress_file": str(progress_file)
        }
        return await orchestrate_pipeline(context, outputs, steps, resume_from_last_successful)
    except Exception as e:
        context.log_pipeline("failed", error=str(e))
        raise

