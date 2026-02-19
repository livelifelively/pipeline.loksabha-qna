"""
Tests for DocumentProgressHandler — the domain-specific layer
on top of ProgressStateManager for document processing.
"""

import json
from pathlib import Path

import pytest

from apps.py.types.models import (
    ManualReviewPageData,
    ProcessingMetadata,
    ProcessingState,
    ProcessingStatus,
    ProgressFileStructure,
)
from apps.py.documents.utils.progress_handler import DocumentProgressHandler


class TestDocumentProgressHandlerRead:
    """Test reading progress files through the handler."""

    def test_read_progress_returns_typed_structure(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        progress = handler.read_progress_file()
        assert isinstance(progress, ProgressFileStructure)
        assert progress.current_state == ProcessingState.LOCAL_EXTRACTION

    def test_get_current_state(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        state = handler.get_current_state()
        assert state == ProcessingState.LOCAL_EXTRACTION

    def test_get_initialized_data(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        data = handler.get_initialized_data()
        assert data is not None
        assert data.state == "INITIALIZED"
        assert data.data["question_number"] == 64

    def test_get_local_extraction_data(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        data = handler.get_local_extraction_data()
        assert data is not None
        assert data.state == "LOCAL_EXTRACTION"
        assert "pages" in data.data

    def test_get_nonexistent_state_returns_none(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        data = handler.get_manual_review_data()
        assert data is None

    def test_get_state_data_generic(self, tmp_document_dir: Path):
        handler = DocumentProgressHandler(tmp_document_dir)
        data = handler.get_state_data(ProcessingState.LOCAL_EXTRACTION)
        assert data is not None


class TestDocumentProgressHandlerTransition:
    """Test state transitions through the handler."""

    def _build_manual_review_ready_dir(self, tmp_path: Path) -> Path:
        """Build a doc dir at MANUAL_REVIEW state for testing patches."""
        doc_dir = tmp_path / "mr-doc"
        doc_dir.mkdir()
        progress_file = doc_dir / "question.progress.json"
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "current_state": "MANUAL_REVIEW",
                    "states": [
                        {
                            "state": "NOT_STARTED",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:00:00+00:00",
                            "data": {},
                            "meta": {"auto_generated": True},
                            "errors": [],
                        },
                        {
                            "state": "INITIALIZED",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:01:00+00:00",
                            "data": {
                                "question_number": 64,
                                "subjects": "Test",
                                "loksabha_number": "18",
                                "member": ["Test Member"],
                                "ministry": "TEST",
                                "type": "STARRED",
                                "date": "01.01.2025",
                                "questions_file_path_local": "test.pdf",
                                "questions_file_path_web": "https://example.com/test.pdf",
                                "session_number": "1",
                            },
                            "meta": {},
                            "errors": [],
                        },
                        {
                            "state": "LOCAL_EXTRACTION",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:02:00+00:00",
                            "data": {
                                "processing_metadata": {
                                    "processing_time_seconds": 1.0,
                                    "pages_processed": 2,
                                    "pages_failed": 0,
                                },
                                "pages": {
                                    "1": {
                                        "has_tables": False,
                                        "num_tables": 0,
                                        "text": "Page 1 text",
                                    },
                                    "2": {
                                        "has_tables": False,
                                        "num_tables": 0,
                                        "text": "Page 2 text",
                                    },
                                },
                                "extracted_text_path": "extracted_text.md",
                                "has_tables": False,
                                "total_tables": 0,
                                "pages_with_tables": 0,
                            },
                            "meta": {},
                            "errors": [],
                        },
                        {
                            "state": "MANUAL_REVIEW",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:03:00+00:00",
                            "data": {
                                "processing_metadata": {
                                    "processing_time_seconds": 0.0,
                                    "pages_processed": 2,
                                    "pages_failed": 0,
                                },
                                "pages": {
                                    "1": {
                                        "text": "Page 1 text",
                                        "has_tables": False,
                                        "num_tables": 0,
                                        "has_multiple_tables": False,
                                        "has_multi_page_tables": False,
                                        "passed_review": False,
                                    },
                                    "2": {
                                        "text": "Page 2 text",
                                        "has_tables": False,
                                        "num_tables": 0,
                                        "has_multiple_tables": False,
                                        "has_multi_page_tables": False,
                                        "passed_review": False,
                                    },
                                },
                            },
                            "meta": {},
                            "errors": [],
                        },
                    ],
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:03:00+00:00",
                },
                f,
            )
        return doc_dir

    def test_patch_manual_review_page(self, tmp_path: Path):
        """Should update a single page in MANUAL_REVIEW state."""
        doc_dir = self._build_manual_review_ready_dir(tmp_path)
        handler = DocumentProgressHandler(doc_dir)

        page_data = ManualReviewPageData(
            text="Edited page 1 text",
            has_tables=False,
            num_tables=0,
            has_multiple_tables=False,
            has_multi_page_tables=False,
            passed_review=True,
            text_edited=True,
        )

        handler.patch_manual_review_page(1, page_data)

        # Verify the update
        progress = handler.read_progress_file()
        mr_state = None
        for s in reversed(progress.states):
            if s.state == ProcessingState.MANUAL_REVIEW:
                mr_state = s
                break

        assert mr_state is not None
        assert mr_state.data["pages"]["1"]["passed_review"] is True
        assert mr_state.data["pages"]["1"]["text"] == "Edited page 1 text"
        assert mr_state.data["pages"]["1"]["text_edited"] is True
        # Page 2 should be unchanged
        assert mr_state.data["pages"]["2"]["passed_review"] is False

    def test_patch_manual_review_page_wrong_state_raises(self, tmp_document_dir: Path):
        """Should raise if not in MANUAL_REVIEW state."""
        handler = DocumentProgressHandler(tmp_document_dir)
        # tmp_document_dir is at LOCAL_EXTRACTION

        page_data = ManualReviewPageData(
            text="test",
            has_tables=False,
            num_tables=0,
            has_multiple_tables=False,
            has_multi_page_tables=False,
        )

        with pytest.raises(ValueError, match="Cannot patch MANUAL_REVIEW"):
            handler.patch_manual_review_page(1, page_data)

    def test_patch_manual_review_bulk_pages(self, tmp_path: Path):
        """Should update multiple pages at once."""
        doc_dir = self._build_manual_review_ready_dir(tmp_path)
        handler = DocumentProgressHandler(doc_dir)

        pages_data = {
            1: ManualReviewPageData(
                text="Bulk edit page 1",
                has_tables=False,
                num_tables=0,
                has_multiple_tables=False,
                has_multi_page_tables=False,
                passed_review=True,
            ),
            2: ManualReviewPageData(
                text="Bulk edit page 2",
                has_tables=False,
                num_tables=0,
                has_multiple_tables=False,
                has_multi_page_tables=False,
                passed_review=True,
            ),
        }

        handler.patch_manual_review_bulk_pages(pages_data)

        progress = handler.read_progress_file()
        mr_state = None
        for s in reversed(progress.states):
            if s.state == ProcessingState.MANUAL_REVIEW:
                mr_state = s
                break

        assert mr_state.data["pages"]["1"]["text"] == "Bulk edit page 1"
        assert mr_state.data["pages"]["2"]["text"] == "Bulk edit page 2"
        assert mr_state.data["pages"]["1"]["passed_review"] is True
        assert mr_state.data["pages"]["2"]["passed_review"] is True

    def test_patch_manual_review_status(self, tmp_path: Path):
        """Should update status of MANUAL_REVIEW state."""
        doc_dir = self._build_manual_review_ready_dir(tmp_path)
        handler = DocumentProgressHandler(doc_dir)

        handler.patch_manual_review_status(
            ProcessingStatus.SUCCESS,
            processing_metadata={"reviewer": "test_user", "processing_time_seconds": 42.0},
        )

        # Read raw to check status at GenericStateData level
        with open(doc_dir / "question.progress.json") as f:
            raw = json.load(f)

        mr_entries = [s for s in raw["states"] if s["state"] == "MANUAL_REVIEW"]
        latest = mr_entries[-1]
        assert latest["status"] == "SUCCESS"

    def test_rollback_to_state(self, tmp_path: Path):
        doc_dir = self._build_manual_review_ready_dir(tmp_path)
        handler = DocumentProgressHandler(doc_dir)

        handler.rollback_to_state(ProcessingState.LOCAL_EXTRACTION)

        state = handler.get_current_state()
        assert state == ProcessingState.LOCAL_EXTRACTION


class TestDocumentProgressHandlerInit:
    """Test handler initialization with new directories."""

    def test_creates_progress_file_for_new_dir(self, tmp_path: Path):
        """Handler should create progress file when document dir has none."""
        doc_dir = tmp_path / "brand-new-doc"
        doc_dir.mkdir()

        handler = DocumentProgressHandler(doc_dir)

        progress = handler.read_progress_file()
        assert progress.current_state == ProcessingState.NOT_STARTED
        assert len(progress.states) == 1
