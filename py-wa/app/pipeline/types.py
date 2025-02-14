from typing import Any, Callable, Dict, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path

from .context import PipelineContext

# Type for pipeline step status
StepStatus = Literal["SUCCESS", "FAILURE", "PARTIAL"]

StepFunction = Callable[[Dict[str, Any], PipelineContext], Dict[str, Any]]

class PipelineStep(BaseModel):
    """A single step in the pipeline."""
    name: str = Field(..., description="Name of the pipeline step")
    function: StepFunction = Field(..., description="Function to execute for this step")
    key: str = Field(..., description="Unique identifier for the step")
    input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the step")
    status: Optional[str] = Field(None, description="Execution status of the step")
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
    timestamp: Optional[str] = Field(None, description="Timestamp of the progress entry")

class ProgressStep(BaseModel):
    """Information about a completed pipeline step."""
    step: int = Field(..., description="Step number")
    log_file: Path = Field(..., description="Path to the log file")
    status: str = Field(..., description="Step status")

class ProgressIteration(BaseModel):
    """Information about a pipeline iteration."""
    iteration: int = Field(..., description="Iteration number")
    timestamp: datetime = Field(default_factory=datetime.now, description="Iteration timestamp")
    steps: List[ProgressStep] = Field(default_factory=list, description="Completed steps")

class PipelineConfig(BaseModel):
    """Complete pipeline configuration"""
    steps: List[PipelineStep]
    initial_outputs: Dict[str, Any]
    progress_dir: Path
    progress_file: Path

    class Config:
        arbitrary_types_allowed = True  # To allow Callable type