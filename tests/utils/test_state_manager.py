"""
Tests for ProgressStateManager — generic state machine with JSON persistence.
Tests initialization, reading, transitions, rollbacks, and deep merge.
"""

import json
from pathlib import Path

import pytest

from apps.py.types.models import GenericStateData, ProcessingState
from apps.py.utils.state_manager import ProgressStateManager
from apps.py.utils.timestamps import get_current_timestamp


class TestStateManagerInitialization:
    """Test ProgressStateManager initialization."""

    def test_creates_progress_file_if_missing(self, tmp_path: Path):
        """Should create a new progress file when it doesn't exist."""
        progress_file = tmp_path / "doc" / "question.progress.json"
        assert not progress_file.exists()

        mgr = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)

        assert progress_file.exists()
        with open(progress_file) as f:
            data = json.load(f)
        assert data["current_state"] == "NOT_STARTED"
        assert len(data["states"]) == 1
        assert data["states"][0]["state"] == "NOT_STARTED"
        assert data["states"][0]["meta"]["auto_generated"] is True

    def test_uses_existing_progress_file(self, tmp_document_dir: Path):
        """Should read existing file without overwriting."""
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        data = mgr.read_progress_file()
        # s-64 fixture has LOCAL_EXTRACTION as current state
        assert data["current_state"] == "LOCAL_EXTRACTION"
        assert len(data["states"]) == 3

    def test_creates_file_with_custom_initial_data(self, tmp_path: Path):
        """Should use provided initial_state_data when creating new file."""
        progress_file = tmp_path / "custom.progress.json"
        custom_data = GenericStateData(
            state="NOT_STARTED",
            status="SUCCESS",
            timestamp=get_current_timestamp(),
            data={"custom_field": "test_value"},
            meta={"source": "test"},
            errors=[],
        )

        mgr = ProgressStateManager(
            file_path=progress_file,
            initial_state=ProcessingState.NOT_STARTED,
            initial_state_data=custom_data,
        )

        data = mgr.read_progress_file()
        assert data["states"][0]["data"]["custom_field"] == "test_value"
        assert data["states"][0]["meta"]["source"] == "test"


class TestStateManagerRead:
    """Test read operations."""

    def test_read_progress_file(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        data = mgr.read_progress_file()
        assert "current_state" in data
        assert "states" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_current_state(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        state = mgr.get_current_state()
        assert state == "LOCAL_EXTRACTION"

    def test_get_state_data_found(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        state_data = mgr.get_state_data(ProcessingState.LOCAL_EXTRACTION)
        assert state_data is not None
        assert isinstance(state_data, GenericStateData)
        assert state_data.state == "LOCAL_EXTRACTION"
        assert state_data.status == "SUCCESS"

    def test_get_state_data_not_found(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        # MANUAL_REVIEW doesn't exist in s-64 fixture
        state_data = mgr.get_state_data(ProcessingState.MANUAL_REVIEW)
        assert state_data is None

    def test_get_state_data_returns_most_recent(self, tmp_path: Path):
        """When multiple entries exist for a state, should return the latest."""
        progress_file = tmp_path / "multi.progress.json"
        with open(progress_file, "w") as f:
            json.dump(
                {
                    "current_state": "INITIALIZED",
                    "states": [
                        {
                            "state": "NOT_STARTED",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:00:00+00:00",
                            "data": {"version": 1},
                            "meta": {},
                            "errors": [],
                        },
                        {
                            "state": "INITIALIZED",
                            "status": "FAILED",
                            "timestamp": "2025-01-01T00:01:00+00:00",
                            "data": {"version": 2},
                            "meta": {},
                            "errors": ["first attempt failed"],
                        },
                        {
                            "state": "INITIALIZED",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:02:00+00:00",
                            "data": {"version": 3},
                            "meta": {},
                            "errors": [],
                        },
                    ],
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:02:00+00:00",
                },
                f,
            )

        mgr = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)
        state_data = mgr.get_state_data("INITIALIZED")
        assert state_data.data["version"] == 3
        assert state_data.status == "SUCCESS"

    def test_read_missing_file_raises(self, tmp_path: Path):
        """Should raise FileNotFoundError when file is deleted after init."""
        progress_file = tmp_path / "doc" / "question.progress.json"
        mgr = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)

        # Delete the file after initialization
        progress_file.unlink()

        with pytest.raises(FileNotFoundError):
            mgr.read_progress_file()


class TestStateManagerTransition:
    """Test state transitions."""

    def test_transition_appends_to_states(self, tmp_minimal_doc_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_minimal_doc_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        new_state_data = GenericStateData(
            state="INITIALIZED",
            status="SUCCESS",
            timestamp=get_current_timestamp(),
            data={"question_number": 99},
            meta={},
            errors=[],
        )

        mgr.transition_to_state(ProcessingState.INITIALIZED, new_state_data)

        data = mgr.read_progress_file()
        assert data["current_state"] == "INITIALIZED"
        assert len(data["states"]) == 2
        assert data["states"][1]["state"] == "INITIALIZED"
        assert data["states"][1]["data"]["question_number"] == 99

    def test_transition_updates_timestamps(self, tmp_minimal_doc_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_minimal_doc_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        before = mgr.read_progress_file()
        old_updated = before["updated_at"]

        new_state_data = GenericStateData(
            state="INITIALIZED",
            status="SUCCESS",
            timestamp=get_current_timestamp(),
            data={},
            meta={},
            errors=[],
        )
        mgr.transition_to_state(ProcessingState.INITIALIZED, new_state_data)

        after = mgr.read_progress_file()
        assert after["updated_at"] != old_updated


class TestStateManagerUpdateStateData:
    """Test partial state data updates (deep merge)."""

    def test_update_merges_data(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        # LOCAL_EXTRACTION exists in fixture with pages data
        mgr.update_state_data(ProcessingState.LOCAL_EXTRACTION, {"new_field": "new_value"})

        state_data = mgr.get_state_data(ProcessingState.LOCAL_EXTRACTION)
        assert state_data.data["new_field"] == "new_value"
        # Original data preserved
        assert "pages" in state_data.data

    def test_update_deep_merges_nested(self, tmp_document_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_document_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        # Update a single page within existing pages dict
        mgr.update_state_data(
            ProcessingState.LOCAL_EXTRACTION,
            {"pages": {"1": {"text_edited": True}}},
        )

        state_data = mgr.get_state_data(ProcessingState.LOCAL_EXTRACTION)
        page1 = state_data.data["pages"]["1"]
        # New field added
        assert page1["text_edited"] is True
        # Original fields preserved by deep merge
        assert "text" in page1

    def test_update_nonexistent_state_raises(self, tmp_minimal_doc_dir: Path):
        mgr = ProgressStateManager(
            file_path=tmp_minimal_doc_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        with pytest.raises(ValueError, match="No existing entry found"):
            mgr.update_state_data(ProcessingState.MANUAL_REVIEW, {"foo": "bar"})


class TestStateManagerRollback:
    """Test rollback functionality."""

    def _build_three_state_file(self, tmp_path: Path) -> Path:
        """Create a progress file at MANUAL_REVIEW with full history."""
        from apps.py.types.models import STATE_ORDER

        progress_file = tmp_path / "rollback-doc" / "question.progress.json"
        progress_file.parent.mkdir(parents=True)
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
                        {
                            "state": "MANUAL_REVIEW",
                            "status": "SUCCESS",
                            "timestamp": "2025-01-01T00:03:00+00:00",
                            "data": {},
                            "meta": {},
                            "errors": [],
                        },
                    ],
                    "created_at": "2025-01-01T00:00:00+00:00",
                    "updated_at": "2025-01-01T00:03:00+00:00",
                },
                f,
            )
        return progress_file

    def test_rollback_changes_current_state(self, tmp_path: Path):
        from apps.py.types.models import STATE_ORDER

        progress_file = self._build_three_state_file(tmp_path)
        mgr = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)

        mgr.rollback_to_state(ProcessingState.LOCAL_EXTRACTION, STATE_ORDER)

        data = mgr.read_progress_file()
        assert data["current_state"] == "LOCAL_EXTRACTION"

    def test_rollback_adds_audit_trail_entries(self, tmp_path: Path):
        from apps.py.types.models import STATE_ORDER

        progress_file = self._build_three_state_file(tmp_path)
        mgr = ProgressStateManager(file_path=progress_file, initial_state=ProcessingState.NOT_STARTED)

        mgr.rollback_to_state(ProcessingState.LOCAL_EXTRACTION, STATE_ORDER)

        data = mgr.read_progress_file()
        # Original 4 entries + rollback entry for MANUAL_REVIEW
        assert len(data["states"]) == 5
        rollback_entry = data["states"][-1]
        assert rollback_entry["meta"]["rollback_target"] == "LOCAL_EXTRACTION"
        assert rollback_entry["meta"]["rollback_from"] == "MANUAL_REVIEW"

    def test_rollback_to_future_state_raises(self, tmp_minimal_doc_dir: Path):
        from apps.py.types.models import STATE_ORDER

        mgr = ProgressStateManager(
            file_path=tmp_minimal_doc_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        with pytest.raises(ValueError, match="Cannot rollback to future state"):
            mgr.rollback_to_state(ProcessingState.MANUAL_REVIEW, STATE_ORDER)

    def test_rollback_to_invalid_state_raises(self, tmp_minimal_doc_dir: Path):
        from apps.py.types.models import STATE_ORDER

        mgr = ProgressStateManager(
            file_path=tmp_minimal_doc_dir / "question.progress.json",
            initial_state=ProcessingState.NOT_STARTED,
        )

        with pytest.raises(ValueError, match="Invalid target state"):
            mgr.rollback_to_state("FAKE_STATE", STATE_ORDER)


class TestDeepMerge:
    """Test the _deep_merge_dicts utility."""

    def test_simple_merge(self, tmp_path: Path):
        mgr = ProgressStateManager(
            file_path=tmp_path / "tmp.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        result = mgr._deep_merge_dicts({"a": 1, "b": 2}, {"b": 3, "c": 4})
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self, tmp_path: Path):
        mgr = ProgressStateManager(
            file_path=tmp_path / "tmp.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        base = {"pages": {"1": {"text": "hello", "has_tables": False}}}
        update = {"pages": {"1": {"text_edited": True}}}
        result = mgr._deep_merge_dicts(base, update)
        assert result["pages"]["1"]["text"] == "hello"
        assert result["pages"]["1"]["has_tables"] is False
        assert result["pages"]["1"]["text_edited"] is True

    def test_deep_merge_does_not_mutate_original(self, tmp_path: Path):
        mgr = ProgressStateManager(
            file_path=tmp_path / "tmp.json",
            initial_state=ProcessingState.NOT_STARTED,
        )
        base = {"a": {"b": 1}}
        update = {"a": {"c": 2}}
        result = mgr._deep_merge_dicts(base, update)
        assert "c" not in base["a"]  # original not mutated
        assert result["a"] == {"b": 1, "c": 2}
