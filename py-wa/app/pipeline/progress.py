from pathlib import Path
import json
from typing import List, Any

class ProgressError(Exception):
    """Base exception for progress-related errors."""
    pass

def initialize_progress(progress_dir: Path, progress_file: Path) -> None:
    """Initialize progress tracking directory and file."""
    try:
        progress_dir.mkdir(parents=True, exist_ok=True)
        
        if not progress_file.exists():
            progress_file.write_text(json.dumps([]))
    except OSError as e:
        raise ProgressError(f"Failed to initialize progress: {e}") from e
