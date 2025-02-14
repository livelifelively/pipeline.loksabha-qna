from logging import Logger
from typing import Optional
from pydantic import BaseModel, Field

from ..utils.run_context import RunContext
from ..utils.logging import setup_logger

class PipelineContext(BaseModel):
    """Development context for pipeline execution"""
    run_id: str = Field(..., description="Unique identifier for the pipeline run")
    logger: Logger = Field(..., description="Logger instance")
    
    class Config:
        arbitrary_types_allowed = True  # To allow Logger type
    
    @classmethod
    def create(cls, name: str, sansad: str, session: str) -> 'PipelineContext':
        run_context = RunContext.create(sansad, session)
        logger = setup_logger(name, run_context)
        
        return cls(
            run_id=run_context.run_id,
            logger=logger
        )

    def log_step(self, event: str, step_num: int, step_name: str, **kwargs):
        """Log step-related events with consistent structure"""
        data = {
            "event": f"step_{event}",
            "step": step_num,
            "name": step_name,
            "run_id": self.run_id,
            **kwargs
        }
        
        if "error" in kwargs:
            self.logger.error(data, exc_info=True)
        else:
            self.logger.info(data)
    
    def log_pipeline(self, event: str, **kwargs):
        """Log pipeline-level events with consistent structure"""
        data = {
            "event": f"pipeline_{event}",
            "run_id": self.run_id,
            **kwargs
        }
        self.logger.info(data)

    def log_error(self, event: str, error: Exception, **kwargs):
        """Structured logging helper for errors"""
        self.logger.error({
            "event": event,
            "error": str(error),
            **kwargs
        }, exc_info=True) 