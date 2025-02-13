from typing import Optional, Any, Dict

class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class PipelineConfigError(PipelineError):
    """Raised when there's an error in pipeline configuration."""
    pass

class PipelineStepError(PipelineError):
    """Raised when a pipeline step fails."""
    def __init__(
        self, 
        message: str, 
        step_name: str, 
        step_number: int, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.step_name = step_name
        self.step_number = step_number
        super().__init__(
            f"Step {step_number} ({step_name}) failed: {message}",
            details
        )

class ProgressError(PipelineError):
    """Raised when there's an error in progress tracking."""
    pass

class FileOperationError(PipelineError):
    """Raised when file operations fail."""
    def __init__(
        self, 
        message: str, 
        file_path: str, 
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.file_path = file_path
        self.operation = operation
        super().__init__(
            f"{operation} operation failed for '{file_path}': {message}",
            details
        )

class PipelineResumeError(PipelineError):
    """Raised when pipeline resume operation fails."""
    pass

class ValidationError(PipelineError):
    """Raised when data validation fails."""
    pass
