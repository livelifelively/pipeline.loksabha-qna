from datetime import datetime
from logging import Logger, LoggerAdapter
from typing import Optional, Union

from pydantic import BaseModel, Field

from ..utils.logging import setup_logger
from ..utils.run_context import RunContext
from .step_types import StepStatus


class StepMetadata(BaseModel):
    """Metadata for the current pipeline step"""

    number: int = Field(..., description="Current step number in pipeline")
    name: str = Field(..., description="Name of the current step")
    key: str = Field(..., description="Unique identifier for the step")
    is_recovered: bool = Field(default=False, description="Whether step data was recovered from previous run")
    status: Optional[StepStatus] = Field(None, description="Current status of the step")
    start_time: datetime = Field(default_factory=datetime.now, description="When step execution began")


class PipelineContext(BaseModel):
    """Development context for pipeline execution"""

    run_id: str = Field(..., description="Unique identifier for the pipeline run")
    logger: Union[Logger, LoggerAdapter] = Field(..., description="Logger instance")
    step_meta: Optional[StepMetadata] = Field(None, description="Current step metadata")

    class Config:
        arbitrary_types_allowed = True  # To allow Logger and LoggerAdapter types

    @classmethod
    def create(cls, name: str, sansad: str, session: str) -> "PipelineContext":
        run_context = RunContext.create(sansad, session)
        logger = setup_logger(name, run_context)
        return cls(run_id=run_context.run_id, logger=logger)

    def set_active_step(self, step_number: int, step_name: str, step_key: str, is_recovered: bool = False) -> None:
        """Set the currently active pipeline step"""
        self.step_meta = StepMetadata(number=step_number, name=step_name, key=step_key, is_recovered=is_recovered)

    def update_step_status(self, status: StepStatus) -> None:
        """Update the status of current step"""
        if not self.step_meta:
            raise ValueError("No active step metadata found")
        self.step_meta.status = status

    def clear_step(self) -> None:
        """Clear the current step metadata"""
        self.step_meta = None

    def log_step(self, event: str, **kwargs):
        """Log step-related events with consistent structure"""
        if not self.step_meta:
            raise ValueError("No active step metadata found")

        data = {
            "event": f"step_{event}",
            "step": self.step_meta.number,
            "name": self.step_meta.name,
            "run_id": self.run_id,
            **kwargs,
        }

        if "error" in kwargs:
            self.logger.error(data, exc_info=True)
        else:
            self.logger.info(data)

    def log_pipeline(self, event: str, **kwargs):
        """Log pipeline-level events with consistent structure"""
        data = {"event": f"pipeline_{event}", "run_id": self.run_id, **kwargs}
        self.logger.info(data)

    def log_error(self, event: str, error: Exception, **kwargs):
        """Structured logging helper for errors"""
        self.logger.error({"event": event, "error": str(error), **kwargs}, exc_info=True)
