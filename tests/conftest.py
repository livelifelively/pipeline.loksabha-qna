"""
Root conftest.py — sets up sys.path so tests can import app modules.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

# Add project root to sys.path so `apps.py.*` imports resolve
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Path to the real data directory (used for read-only fixture loading)
# PROJECT_ROOT = .../implementation/code/pipeline.loksabha-qna
# We need:       .../implementation/data/loksabha-qna
DATA_ROOT = PROJECT_ROOT.parent.parent / "data" / "loksabha-qna"

# Fixture: path constants
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
SAMPLE_DOC_PATH = DATA_ROOT / "18" / "iv" / "ministries" / "health-and-family-welfare" / "s-64"


@pytest.fixture
def sample_progress_json() -> dict:
    """Load the real s-64 question.progress.json as a Python dict."""
    progress_file = SAMPLE_DOC_PATH / "question.progress.json"
    assert progress_file.exists(), f"Test fixture not found: {progress_file}"
    with open(progress_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def tmp_document_dir(tmp_path: Path, sample_progress_json: dict) -> Path:
    """
    Create a temporary document directory with a copy of the real progress file.
    Safe for write tests — doesn't touch production data.
    """
    doc_dir = tmp_path / "test-doc"
    doc_dir.mkdir()
    progress_file = doc_dir / "question.progress.json"
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(sample_progress_json, f, indent=2)
    return doc_dir


@pytest.fixture
def minimal_progress_json() -> dict:
    """Minimal valid progress JSON (just NOT_STARTED)."""
    return {
        "current_state": "NOT_STARTED",
        "states": [
            {
                "state": "NOT_STARTED",
                "status": "SUCCESS",
                "timestamp": "2025-06-27T15:08:01.368215+00:00",
                "data": {},
                "meta": {"auto_generated": True},
                "errors": [],
            }
        ],
        "created_at": "2025-06-27T15:08:01.368228+00:00",
        "updated_at": "2025-06-27T15:08:01.368228+00:00",
    }


@pytest.fixture
def tmp_minimal_doc_dir(tmp_path: Path, minimal_progress_json: dict) -> Path:
    """
    Temporary document directory with a minimal progress file (NOT_STARTED only).
    """
    doc_dir = tmp_path / "minimal-doc"
    doc_dir.mkdir()
    progress_file = doc_dir / "question.progress.json"
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(minimal_progress_json, f, indent=2)
    return doc_dir
