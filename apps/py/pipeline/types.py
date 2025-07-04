from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field

from ..utils.timestamps import get_current_timestamp
from .context import PipelineContext
from .step_types import StepStatus

StepFunction = Callable[[Dict[str, Any], PipelineContext], Dict[str, Any]]


class PipelineStep(BaseModel):
    """A single step in the pipeline."""

    name: str = Field(..., description="Name of the pipeline step")
    function: StepFunction = Field(..., description="Function to execute for this step")
    key: str = Field(..., description="Unique identifier for the step")
    input: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Input parameters for the step")
    status: Optional[StepStatus] = Field(None, description="Execution status of the step")
    error: Optional[str] = Field(None, description="Error message if step failed")
    output: Optional[Dict[str, Any]] = Field(None, description="Output data from the step")

    class Config:
        arbitrary_types_allowed = True  # To allow Callable type

    @property
    def is_successful(self) -> bool:
        """Check if step completed successfully."""
        return self.status == "SUCCESS"


class PipelineError(BaseModel):
    """Pipeline execution error."""

    message: str = Field(..., description="Error message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")

    def __str__(self) -> str:
        return f"{self.message} (context: {self.context})"


class PipelineStepError(PipelineError):
    """Error during pipeline step execution."""

    step_name: str = Field(..., description="Name of the failed step")
    step_number: int = Field(..., description="Index of the failed step")
    step_context: Dict[str, Any] = Field(default_factory=dict, description="Step-specific context")

    def __str__(self) -> str:
        return f"Step {self.step_number} ({self.step_name}) failed: {self.message}"


class ProgressData(BaseModel):
    """Progress data for a pipeline step."""

    message: str = Field(..., description="Progress message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Step output data")
    error: Dict[str, Any] = Field(default_factory=dict, description="Error information if any")
    key: str = Field(..., description="Unique key for the progress entry")
    timestamp: Optional[datetime] = Field(
        default_factory=get_current_timestamp, description="Timestamp of the progress entry"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ProgressStep(BaseModel):
    """Information about a completed pipeline step."""

    step: int = Field(..., description="Step number")
    log_file: Path = Field(..., description="Path to the log file")
    status: str = Field(..., description="Step status")
    key: str = Field(..., description="Step Function key")


class ProgressIteration(BaseModel):
    """Information about a pipeline iteration."""

    iteration: int = Field(..., description="Iteration number")
    timestamp: datetime = Field(default_factory=get_current_timestamp, description="Iteration timestamp")
    steps: List[ProgressStep] = Field(default_factory=list, description="Completed steps")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class PipelineConfig(BaseModel):
    """Complete pipeline configuration"""

    steps: List[PipelineStep]
    initial_outputs: Dict[str, Any]
    progress_dir: Path
    progress_file: Path

    class Config:
        arbitrary_types_allowed = True  # To allow Callable type
