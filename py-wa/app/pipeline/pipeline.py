import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.project_root import find_project_root
from .context import PipelineContext
from .exceptions import PipelineError, PipelineStepError
from .progress import create_new_iteration, get_last_iteration, log_progress
from .types import PipelineStep, ProgressData


def initialize_directories(progress_dir: Path, progress_file: Path, context: Optional[PipelineContext] = None) -> None:
    """
    Initializes the necessary directories and progress file.

    Args:
        progress_dir: The path to the directory where progress information will be stored
        progress_file: The path to the file that will store progress information
        context: Optional pipeline context for logging

    Raises:
        PipelineError: If directory initialization fails
    """
    try:
        progress_dir.mkdir(parents=True, exist_ok=True)
        if not progress_file.exists():
            if context:
                context.log_pipeline("create_progress_file")
            progress_file.write_text(json.dumps([]))
    except Exception as e:
        if context:
            context.log_pipeline("init_failed", error=str(e))
        raise PipelineError("Directory initialization failed", {"error": str(e)}) from e


async def orchestrate_pipeline(
    context: PipelineContext,
    outputs: Dict[str, Any],
    steps: List[PipelineStep],
    resume_from_last_successful: bool = True,
) -> Any:
    """
    Orchestrate execution of pipeline steps.

    Args:
        context: Pipeline execution context
        outputs: Initial pipeline outputs
        steps: List of pipeline steps to execute
        resume_from_last_successful: Whether to resume from last successful step

    Returns:
        Any: Output from last successful step
    """
    context.log_pipeline("pipeline_start", total_steps=len(steps))

    progress_file = Path(outputs["progress_file"])
    previous_iteration = await get_last_iteration(progress_file)
    project_root = Path(find_project_root())

    if previous_iteration:
        context.log_pipeline("previous_iteration_found", step_count=len(previous_iteration.steps))

        if (
            resume_from_last_successful
            and len(previous_iteration.steps) == len(steps)
            and all(step.status == "SUCCESS" for step in previous_iteration.steps)
        ):
            context.log_pipeline("using_previous_successful_run", iteration=previous_iteration.iteration)
            last_step = previous_iteration.steps[-1]

            absolute_log_file = project_root / last_step.log_file
            last_step_data = json.loads(absolute_log_file.read_text())
            return last_step_data["data"]

    current_iteration = await create_new_iteration(progress_file)
    context.log_pipeline("new_iteration_created", iteration=current_iteration.iteration)

    last_step_output = None

    for i, step in enumerate(steps):
        # Set step metadata using context method
        context.set_active_step(
            step_number=i,
            step_name=step.name,
            step_key=step.key,
            is_recovered=bool(
                previous_iteration and any(s.step == i and s.status == "SUCCESS" for s in previous_iteration.steps)
            ),
        )

        context.log_step("step_start")

        try:
            # Convert progress_dir to absolute path before passing to step function
            if "progress_dir" in outputs:
                outputs["progress_dir"] = str(Path(outputs["progress_dir"]).resolve())

            result = await step.function(outputs, context)
            status = result.pop("status", "SUCCESS")
            step.status = status
            context.update_step_status(status)  # Update status using context method
            step.output = result
            outputs.update(result)
            last_step_output = result

            if step.status != "SUCCESS":
                context.log_step("step_failed", status=status)
                raise PipelineStepError(
                    message="Step execution failed", step_name=step.name, step_number=i, step_context={"status": status}
                )

            progress_data = ProgressData(
                message=f"Step {i} ({step.name}) completed successfully.",
                data=step.output,
                key=f"STEP_{i}_{step.status}_{step.name}",
            )

            context.log_step("complete", status="SUCCESS")
            # Convert progress_dir to absolute path before logging progress
            await log_progress(
                Path(outputs["progress_dir"]).resolve(), progress_file, progress_data, "SUCCESS", current_iteration
            )

        except Exception as e:
            step.status = step.status or "FAILURE"
            context.update_step_status(step.status)  # Update status using context method
            context.log_step("failed", status=step.status, error=str(e))

            error_data = ProgressData(
                message=f"Step {i} ({step.name}) failed.",
                data=step.output or {},
                error={"error": [str(e), step.error]} if step.status != "PARTIAL" else {},
                key=f"STEP_{i}_{step.status}_{step.name}",
            )

            await log_progress(Path(outputs["progress_dir"]), progress_file, error_data, step.status, current_iteration)

            raise PipelineError(
                message=f"Step {i} ({step.name}) failed. Manual intervention required.",
                context={"step": i, "name": step.name},
            ) from e

    context.clear_step()  # Clear step using context method
    context.log_pipeline("pipeline_complete")
    return last_step_output


async def run_pipeline(
    context: PipelineContext,
    steps: List[PipelineStep],
    outputs: Dict[str, Any],
    progress_dir: Path,
    progress_file: Path,
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

    initialize_directories(progress_dir, progress_file, context)

    try:
        outputs = {**outputs, "progress_dir": str(progress_dir), "progress_file": str(progress_file)}
        return await orchestrate_pipeline(context, outputs, steps, True)
    except Exception as e:
        context.log_pipeline("failed", error=str(e))
        raise
