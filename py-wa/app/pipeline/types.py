from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, List, Literal, Optional
from datetime import datetime
from pathlib import Path

# Define literal type for step status
StepStatus = Literal["SUCCESS", "FAILURE", "PARTIAL"]

class ProgressData(BaseModel):
    """Data structure for progress logging"""
    message: str = Field(..., description="Human readable progress message")
    data: Dict[str, Any] = Field(..., description="Actual data payload")
    error: Optional[Dict[str, Any]] = Field(None, description="Error information if any")
    key: str = Field(..., description="Unique identifier for the progress entry")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProgressStep(BaseModel):
    """Single step in a pipeline iteration"""
    step: int = Field(..., ge=0)
    log_file: Path
    status: StepStatus

class ProgressIteration(BaseModel):
    """Complete iteration of pipeline execution"""
    iteration: int = Field(..., ge=1)
    timestamp: datetime = Field(default_factory=datetime.now)
    steps: List[ProgressStep] = Field(default_factory=list)
    last_iteration: Optional[int] = Field(None, ge=0)

class PipelineStep(BaseModel):
    """Configuration for a single pipeline step"""
    name: str = Field(..., min_length=1)
    function: Callable
    input: Dict[str, Any]
    key: str = Field(..., min_length=1)
    output: Optional[Dict[str, Any]] = None
    status: Optional[StepStatus] = None
    error: Optional[Dict[str, Any]] = None

    class Config:
        arbitrary_types_allowed = True  # To allow Callable type

class PipelineConfig(BaseModel):
    """Complete pipeline configuration"""
    steps: List[PipelineStep]
    initial_outputs: Dict[str, Any]
    progress_dir: Path
    progress_file: Path

    class Config:
        arbitrary_types_allowed = True  # To allow Callable type