"""
Tests for the manual review FastAPI endpoints.

Strategy: We build a minimal FastAPI test app that mirrors the real endpoint logic
(which is a thin wrapper around DocumentProgressHandler) but avoids importing the
heavy parliament_questions module. The logic under test is identical — same handler
calls, same schema validation.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

from apps.py.documents.utils.progress_handler import DocumentProgressHandler
from apps.py.types import ManualReviewPageData, ProcessingStatus


# ---------------------------------------------------------------------------
# Minimal request/response schemas (mirrors api/py/schemas/knowledge_graph.py)
# ---------------------------------------------------------------------------


class ManualReviewPageUpdateRequest(BaseModel):
    document_path: str = Field(...)
    page_number: int = Field(..., ge=1)
    page_data: ManualReviewPageData


class ManualReviewStatusUpdateRequest(BaseModel):
    document_path: str = Field(...)
    status: ProcessingStatus
    processing_metadata: Optional[Dict[str, Any]] = None


class ManualReviewBulkPagesUpdateRequest(BaseModel):
    document_path: str = Field(...)
    pages_data: Dict[int, ManualReviewPageData]

    @field_validator("pages_data")
    def validate_pages_data(cls, v):
        if not v:
            raise ValueError("pages_data cannot be empty")
        for page_num in v.keys():
            if page_num < 1:
                raise ValueError(f"Page number must be >= 1, got {page_num}")
        return v


class ManualReviewStatusRequest(BaseModel):
    document_path: str = Field(...)


# ---------------------------------------------------------------------------
# Test app factory — creates a FastAPI app pointing at a given data root
# ---------------------------------------------------------------------------


def create_test_app(data_root: Path) -> FastAPI:
    """Create a minimal FastAPI app with manual review endpoints pointing at data_root."""
    app = FastAPI()

    def get_doc_path(document_path: str) -> Path:
        return data_root / document_path

    @app.patch("/api/knowledge-graph/manual-review/page")
    async def update_manual_review_page(request: ManualReviewPageUpdateRequest):
        try:
            document_path = get_doc_path(request.document_path)
            handler = DocumentProgressHandler(document_path)
            handler.patch_manual_review_page(request.page_number, request.page_data)
            updated_data = handler.get_manual_review_data()
            return {
                "status": "success",
                "data": updated_data.model_dump() if updated_data else {},
            }
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.patch("/api/knowledge-graph/manual-review/status")
    async def update_manual_review_status(request: ManualReviewStatusUpdateRequest):
        try:
            document_path = get_doc_path(request.document_path)
            handler = DocumentProgressHandler(document_path)
            handler.patch_manual_review_status(request.status, request.processing_metadata)
            updated_data = handler.get_manual_review_data()
            return {
                "status": "success",
                "data": updated_data.model_dump() if updated_data else {},
            }
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.patch("/api/knowledge-graph/manual-review/pages")
    async def update_manual_review_bulk_pages(request: ManualReviewBulkPagesUpdateRequest):
        try:
            document_path = get_doc_path(request.document_path)
            handler = DocumentProgressHandler(document_path)
            handler.patch_manual_review_bulk_pages(request.pages_data)
            updated_data = handler.get_manual_review_data()
            return {
                "status": "success",
                "data": updated_data.model_dump() if updated_data else {},
            }
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/api/knowledge-graph/manual-review/status")
    async def get_manual_review_status(document_path: str):
        try:
            full_path = get_doc_path(document_path)
            handler = DocumentProgressHandler(full_path)
            manual_review_data = handler.get_manual_review_data()
            if manual_review_data is None:
                raise ValueError("Document is not in MANUAL_REVIEW state")
            return {
                "status": "success",
                "data": manual_review_data.model_dump(),
            }
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MANUAL_REVIEW_PROGRESS = {
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
                    "1": {"has_tables": False, "num_tables": 0, "text": "Page 1"},
                    "2": {"has_tables": False, "num_tables": 0, "text": "Page 2"},
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
}


@pytest.fixture
def mr_data_root(tmp_path: Path) -> Path:
    """Create a data root with a document in MANUAL_REVIEW state."""
    doc_dir = tmp_path / "test-doc"
    doc_dir.mkdir(parents=True)
    with open(doc_dir / "question.progress.json", "w") as f:
        json.dump(MANUAL_REVIEW_PROGRESS, f, indent=2)
    return tmp_path


@pytest.fixture
def client(mr_data_root: Path) -> TestClient:
    """Create a test client pointing at the temp data root."""
    app = create_test_app(mr_data_root)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPatchManualReviewPage:
    """PATCH /api/knowledge-graph/manual-review/page"""

    def test_update_page_text(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "test-doc",
                "page_number": 1,
                "page_data": {
                    "text": "Edited text for page 1",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                    "passed_review": True,
                    "text_edited": True,
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["data"]["pages"]["1"]["text"] == "Edited text for page 1"
        assert body["data"]["data"]["pages"]["1"]["passed_review"] is True
        # Page 2 should be untouched
        assert body["data"]["data"]["pages"]["2"]["passed_review"] is False

    def test_update_page_preserves_other_pages(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "test-doc",
                "page_number": 2,
                "page_data": {
                    "text": "Only page 2 changed",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                    "passed_review": True,
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]["data"]
        assert data["pages"]["1"]["text"] == "Page 1 text"  # unchanged
        assert data["pages"]["2"]["text"] == "Only page 2 changed"

    def test_update_page_invalid_document_path(self, client: TestClient):
        """Document that doesn't exist should init a new progress file (NOT_STARTED),
        then fail because it's not in MANUAL_REVIEW state."""
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "nonexistent-doc",
                "page_number": 1,
                "page_data": {
                    "text": "test",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                },
            },
        )
        # DocumentProgressHandler creates the file at NOT_STARTED, then patch fails
        assert resp.status_code == 400
        assert "Cannot patch MANUAL_REVIEW" in resp.json()["detail"]

    def test_update_page_zero_rejected(self, client: TestClient):
        """Page number must be >= 1."""
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "test-doc",
                "page_number": 0,
                "page_data": {
                    "text": "test",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                },
            },
        )
        assert resp.status_code == 422  # Pydantic validation error


class TestPatchManualReviewStatus:
    """PATCH /api/knowledge-graph/manual-review/status"""

    def test_update_status_success(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/status",
            json={
                "document_path": "test-doc",
                "status": "SUCCESS",
                "processing_metadata": {
                    "reviewer": "test_user",
                    "processing_time_seconds": 120.5,
                },
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"

    def test_update_status_without_metadata(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/status",
            json={
                "document_path": "test-doc",
                "status": "SUCCESS",
            },
        )
        assert resp.status_code == 200

    def test_update_status_wrong_state(self, client: TestClient, mr_data_root: Path):
        """Write a progress file at LOCAL_EXTRACTION, then try to update MR status."""
        wrong_doc = mr_data_root / "wrong-state-doc"
        wrong_doc.mkdir()
        with open(wrong_doc / "question.progress.json", "w") as f:
            json.dump(
                {
                    "current_state": "LOCAL_EXTRACTION",
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
                            "data": {},
                            "meta": {},
                            "errors": [],
                        },
                        {
                            "state": "LOCAL_EXTRACTION",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:02:00+00:00",
                            "data": {},
                            "meta": {},
                            "errors": [],
                        },
                    ],
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:02:00+00:00",
                },
                f,
            )
        resp = client.patch(
            "/api/knowledge-graph/manual-review/status",
            json={
                "document_path": "wrong-state-doc",
                "status": "SUCCESS",
            },
        )
        assert resp.status_code == 400
        assert "Cannot patch MANUAL_REVIEW" in resp.json()["detail"]


class TestPatchManualReviewBulkPages:
    """PATCH /api/knowledge-graph/manual-review/pages"""

    def test_bulk_update_multiple_pages(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/pages",
            json={
                "document_path": "test-doc",
                "pages_data": {
                    "1": {
                        "text": "Bulk page 1",
                        "has_tables": False,
                        "num_tables": 0,
                        "has_multiple_tables": False,
                        "has_multi_page_tables": False,
                        "passed_review": True,
                    },
                    "2": {
                        "text": "Bulk page 2",
                        "has_tables": False,
                        "num_tables": 0,
                        "has_multiple_tables": False,
                        "has_multi_page_tables": False,
                        "passed_review": True,
                    },
                },
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]["data"]
        assert data["pages"]["1"]["text"] == "Bulk page 1"
        assert data["pages"]["2"]["text"] == "Bulk page 2"
        assert data["pages"]["1"]["passed_review"] is True
        assert data["pages"]["2"]["passed_review"] is True

    def test_bulk_update_empty_pages_rejected(self, client: TestClient):
        resp = client.patch(
            "/api/knowledge-graph/manual-review/pages",
            json={
                "document_path": "test-doc",
                "pages_data": {},
            },
        )
        assert resp.status_code == 422  # Pydantic validation


class TestGetManualReviewStatus:
    """GET /api/knowledge-graph/manual-review/status"""

    def test_get_status_success(self, client: TestClient):
        resp = client.get(
            "/api/knowledge-graph/manual-review/status",
            params={"document_path": "test-doc"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "pages" in body["data"]["data"]

    def test_get_status_not_in_manual_review(self, client: TestClient, mr_data_root: Path):
        """Document not in MANUAL_REVIEW should return 400."""
        not_mr_doc = mr_data_root / "not-mr-doc"
        not_mr_doc.mkdir()
        with open(not_mr_doc / "question.progress.json", "w") as f:
            json.dump(
                {
                    "current_state": "NOT_STARTED",
                    "states": [
                        {
                            "state": "NOT_STARTED",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:00:00+00:00",
                            "data": {},
                            "meta": {"auto_generated": True},
                            "errors": [],
                        }
                    ],
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:00:00+00:00",
                },
                f,
            )
        resp = client.get(
            "/api/knowledge-graph/manual-review/status",
            params={"document_path": "not-mr-doc"},
        )
        assert resp.status_code == 400
        assert "not in MANUAL_REVIEW" in resp.json()["detail"]


class TestEndToEndPageReviewFlow:
    """Integration test: complete manual review page-by-page flow."""

    def test_review_both_pages_then_complete(self, client: TestClient):
        """Simulate reviewing page 1, then page 2, then marking complete."""
        # Step 1: Review page 1
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "test-doc",
                "page_number": 1,
                "page_data": {
                    "text": "Reviewed page 1",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                    "passed_review": True,
                },
            },
        )
        assert resp.status_code == 200

        # Step 2: Review page 2
        resp = client.patch(
            "/api/knowledge-graph/manual-review/page",
            json={
                "document_path": "test-doc",
                "page_number": 2,
                "page_data": {
                    "text": "Reviewed page 2",
                    "has_tables": False,
                    "num_tables": 0,
                    "has_multiple_tables": False,
                    "has_multi_page_tables": False,
                    "passed_review": True,
                },
            },
        )
        assert resp.status_code == 200

        # Step 3: Mark review as complete
        resp = client.patch(
            "/api/knowledge-graph/manual-review/status",
            json={
                "document_path": "test-doc",
                "status": "SUCCESS",
                "processing_metadata": {"reviewer": "integration_test"},
            },
        )
        assert resp.status_code == 200

        # Step 4: Verify final state
        resp = client.get(
            "/api/knowledge-graph/manual-review/status",
            params={"document_path": "test-doc"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]["data"]
        assert data["pages"]["1"]["passed_review"] is True
        assert data["pages"]["2"]["passed_review"] is True
        assert data["pages"]["1"]["text"] == "Reviewed page 1"
        assert data["pages"]["2"]["text"] == "Reviewed page 2"
