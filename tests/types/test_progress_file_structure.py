"""
Tests for ProgressFileStructure — parsing real progress.json files,
validation rules, and state consistency checks.
"""

import copy
from datetime import datetime, timezone

import pytest

from apps.py.types.models import (
    ProcessingState,
    ProcessingStatus,
    ProgressFileStructure,
    QuestionProcessingProgressStateData,
)


class TestProgressFileStructureParsing:
    """Test parsing real progress.json data into ProgressFileStructure."""

    def test_parse_real_s64_progress(self, sample_progress_json: dict):
        """Parse the real s-64 question.progress.json without errors."""
        progress = ProgressFileStructure(**sample_progress_json)

        assert progress.current_state == ProcessingState.LOCAL_EXTRACTION
        assert len(progress.states) == 3
        assert isinstance(progress.created_at, datetime)
        assert isinstance(progress.updated_at, datetime)

    def test_states_are_typed(self, sample_progress_json: dict):
        """Each state entry should be a QuestionProcessingProgressStateData."""
        progress = ProgressFileStructure(**sample_progress_json)

        for state_entry in progress.states:
            assert isinstance(state_entry, QuestionProcessingProgressStateData)

    def test_state_enum_values(self, sample_progress_json: dict):
        """State fields should be converted to ProcessingState enums."""
        progress = ProgressFileStructure(**sample_progress_json)

        expected_states = [
            ProcessingState.NOT_STARTED,
            ProcessingState.INITIALIZED,
            ProcessingState.LOCAL_EXTRACTION,
        ]
        actual_states = [s.state for s in progress.states]
        assert actual_states == expected_states

    def test_initialized_data_fields(self, sample_progress_json: dict):
        """INITIALIZED state should carry question metadata in its data dict."""
        progress = ProgressFileStructure(**sample_progress_json)

        init_state = progress.states[1]
        assert init_state.state == ProcessingState.INITIALIZED
        assert init_state.data["question_number"] == 64
        assert init_state.data["ministry"] == "HEALTH AND FAMILY WELFARE"
        assert init_state.data["type"] == "STARRED"
        assert "Smt. Geniben Nagaji Thakor" in init_state.data["member"]

    def test_local_extraction_data_fields(self, sample_progress_json: dict):
        """LOCAL_EXTRACTION state should carry page data and metadata."""
        progress = ProgressFileStructure(**sample_progress_json)

        extract_state = progress.states[2]
        assert extract_state.state == ProcessingState.LOCAL_EXTRACTION
        assert extract_state.data["processing_metadata"]["pages_processed"] == 2
        assert "1" in extract_state.data["pages"]
        assert "2" in extract_state.data["pages"]
        assert extract_state.data["has_tables"] is False

    def test_timestamps_are_parsed(self, sample_progress_json: dict):
        """Timestamps in state entries should be parsed as datetime objects."""
        progress = ProgressFileStructure(**sample_progress_json)

        for state_entry in progress.states:
            assert isinstance(state_entry.timestamp, datetime)

    def test_minimal_progress(self, minimal_progress_json: dict):
        """Minimal progress JSON (just NOT_STARTED) should parse correctly."""
        progress = ProgressFileStructure(**minimal_progress_json)

        assert progress.current_state == ProcessingState.NOT_STARTED
        assert len(progress.states) == 1
        assert progress.states[0].state == ProcessingState.NOT_STARTED


class TestProgressFileStructureValidation:
    """Test validation rules in ProgressFileStructure."""

    def test_invalid_current_state_string(self):
        """Should reject invalid current_state strings."""
        with pytest.raises(ValueError, match="Invalid current_state"):
            ProgressFileStructure(
                current_state="BOGUS_STATE",
                states=[
                    {
                        "state": "NOT_STARTED",
                        "status": "SUCCESS",
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "data": {},
                        "meta": {},
                        "errors": [],
                    }
                ],
                created_at="2025-01-01T00:00:00+00:00",
                updated_at="2025-01-01T00:00:00+00:00",
            )

    def test_current_state_must_exist_in_states(self):
        """current_state must be present in the states array."""
        with pytest.raises(ValueError, match="not found in states"):
            ProgressFileStructure(
                current_state="INITIALIZED",
                states=[
                    {
                        "state": "NOT_STARTED",
                        "status": "SUCCESS",
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "data": {},
                        "meta": {},
                        "errors": [],
                    }
                ],
                created_at="2025-01-01T00:00:00+00:00",
                updated_at="2025-01-01T00:00:00+00:00",
            )

    def test_rejects_future_states_in_normal_progression(self):
        """In normal progression (no rollback), future states should be rejected."""
        with pytest.raises(ValueError, match="Future state"):
            ProgressFileStructure(
                current_state="NOT_STARTED",
                states=[
                    {
                        "state": "NOT_STARTED",
                        "status": "SUCCESS",
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "data": {},
                        "meta": {},
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
                ],
                created_at="2025-01-01T00:00:00+00:00",
                updated_at="2025-01-01T00:01:00+00:00",
            )

    def test_allows_rollback_states(self):
        """When rollback entries exist, all states should be allowed."""
        progress = ProgressFileStructure(
            current_state="INITIALIZED",
            states=[
                {
                    "state": "NOT_STARTED",
                    "status": "SUCCESS",
                    "timestamp": "2025-01-01T00:00:00+00:00",
                    "data": {},
                    "meta": {},
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
                    "meta": {"rollback_target": "INITIALIZED"},  # This marks a rollback
                    "errors": [],
                },
            ],
            created_at="2025-01-01T00:00:00+00:00",
            updated_at="2025-01-01T00:02:00+00:00",
        )
        assert progress.current_state == ProcessingState.INITIALIZED
        assert len(progress.states) == 3

    def test_invalid_state_in_states_array(self):
        """Invalid state strings in the states array should be rejected."""
        with pytest.raises(ValueError):
            ProgressFileStructure(
                current_state="NOT_STARTED",
                states=[
                    {
                        "state": "NOT_STARTED",
                        "status": "SUCCESS",
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "data": {},
                        "meta": {},
                        "errors": [],
                    },
                    {
                        "state": "FAKE_STATE",
                        "status": "SUCCESS",
                        "timestamp": "2025-01-01T00:00:00+00:00",
                        "data": {},
                        "meta": {},
                        "errors": [],
                    },
                ],
                created_at="2025-01-01T00:00:00+00:00",
                updated_at="2025-01-01T00:00:00+00:00",
            )


class TestProgressFileStructureCanTransition:
    """Test the can_transition_to() method on ProgressFileStructure."""

    def test_not_started_can_transition_to_initialized(self, minimal_progress_json: dict):
        """NOT_STARTED -> INITIALIZED is valid."""
        progress = ProgressFileStructure(**minimal_progress_json)
        assert progress.can_transition_to(ProcessingState.INITIALIZED) is True

    def test_not_started_cannot_skip_to_local_extraction(self, minimal_progress_json: dict):
        """NOT_STARTED -> LOCAL_EXTRACTION is NOT valid (must go through INITIALIZED)."""
        progress = ProgressFileStructure(**minimal_progress_json)
        assert progress.can_transition_to(ProcessingState.LOCAL_EXTRACTION) is False

    def test_local_extraction_can_go_to_manual_review(self, sample_progress_json: dict):
        """LOCAL_EXTRACTION -> MANUAL_REVIEW is valid (no tables path)."""
        progress = ProgressFileStructure(**sample_progress_json)
        # Without state_data, condition checks are skipped, so the transition
        # based purely on rule existence should be True
        assert progress.can_transition_to(ProcessingState.MANUAL_REVIEW) is True

    def test_local_extraction_can_go_to_llm_extraction(self, sample_progress_json: dict):
        """LOCAL_EXTRACTION -> LLM_EXTRACTION is valid (tables path)."""
        progress = ProgressFileStructure(**sample_progress_json)
        assert progress.can_transition_to(ProcessingState.LLM_EXTRACTION) is True

    def test_cannot_transition_backwards(self, sample_progress_json: dict):
        """LOCAL_EXTRACTION -> NOT_STARTED is NOT valid."""
        progress = ProgressFileStructure(**sample_progress_json)
        assert progress.can_transition_to(ProcessingState.NOT_STARTED) is False

    def test_cannot_skip_ahead(self, sample_progress_json: dict):
        """LOCAL_EXTRACTION -> CHUNKING is NOT valid."""
        progress = ProgressFileStructure(**sample_progress_json)
        assert progress.can_transition_to(ProcessingState.CHUNKING) is False
