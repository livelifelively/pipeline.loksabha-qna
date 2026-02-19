"""
Tests for StateTransitionValidator and VALID_TRANSITIONS —
ensures the state machine rules are correct and enforced.
"""

import pytest

from apps.py.types.models import (
    STATE_ORDER,
    VALID_TRANSITIONS,
    LocalExtractionData,
    LocalExtractionPageData,
    ProcessingMetadata,
    ProcessingState,
    ProcessingStatus,
    StateTransition,
    StateTransitionValidator,
    TransitionCondition,
)


class TestValidTransitionsDefinition:
    """Verify the VALID_TRANSITIONS list is correct."""

    def test_transitions_list_not_empty(self):
        assert len(VALID_TRANSITIONS) > 0

    def test_all_transitions_are_typed(self):
        for t in VALID_TRANSITIONS:
            assert isinstance(t, StateTransition)
            assert isinstance(t.from_state, ProcessingState)
            assert isinstance(t.to_state, ProcessingState)

    def test_not_started_to_initialized_exists(self):
        found = any(
            t.from_state == ProcessingState.NOT_STARTED and t.to_state == ProcessingState.INITIALIZED
            for t in VALID_TRANSITIONS
        )
        assert found

    def test_local_extraction_has_two_outgoing_paths(self):
        """LOCAL_EXTRACTION can go to LLM_EXTRACTION (tables) or MANUAL_REVIEW (no tables)."""
        outgoing = [t for t in VALID_TRANSITIONS if t.from_state == ProcessingState.LOCAL_EXTRACTION]
        to_states = {t.to_state for t in outgoing}
        assert ProcessingState.LLM_EXTRACTION in to_states
        assert ProcessingState.MANUAL_REVIEW in to_states

    def test_local_extraction_to_llm_requires_has_tables(self):
        t = next(
            t
            for t in VALID_TRANSITIONS
            if t.from_state == ProcessingState.LOCAL_EXTRACTION and t.to_state == ProcessingState.LLM_EXTRACTION
        )
        assert t.condition == TransitionCondition.HAS_TABLES
        assert t.required_status == ProcessingStatus.SUCCESS

    def test_local_extraction_to_manual_review_requires_no_tables(self):
        t = next(
            t
            for t in VALID_TRANSITIONS
            if t.from_state == ProcessingState.LOCAL_EXTRACTION and t.to_state == ProcessingState.MANUAL_REVIEW
        )
        assert t.condition == TransitionCondition.NO_TABLES
        assert t.required_status == ProcessingStatus.SUCCESS

    def test_llm_extraction_self_transition_exists(self):
        """LLM_EXTRACTION -> LLM_EXTRACTION (retry) should exist."""
        found = any(
            t.from_state == ProcessingState.LLM_EXTRACTION and t.to_state == ProcessingState.LLM_EXTRACTION
            for t in VALID_TRANSITIONS
        )
        assert found

    def test_manual_review_to_prepare_data(self):
        t = next(
            t
            for t in VALID_TRANSITIONS
            if t.from_state == ProcessingState.MANUAL_REVIEW and t.to_state == ProcessingState.PREPARE_DATA
        )
        assert t.required_status == ProcessingStatus.SUCCESS

    def test_prepare_data_to_chunking(self):
        t = next(
            t
            for t in VALID_TRANSITIONS
            if t.from_state == ProcessingState.PREPARE_DATA and t.to_state == ProcessingState.CHUNKING
        )
        assert t.required_status == ProcessingStatus.SUCCESS


class TestStateOrder:
    """Verify STATE_ORDER is correct."""

    def test_state_order_length(self):
        assert len(STATE_ORDER) == 7

    def test_state_order_starts_with_not_started(self):
        assert STATE_ORDER[0] == ProcessingState.NOT_STARTED

    def test_state_order_ends_with_chunking(self):
        assert STATE_ORDER[-1] == ProcessingState.CHUNKING

    def test_state_order_sequence(self):
        expected = [
            ProcessingState.NOT_STARTED,
            ProcessingState.INITIALIZED,
            ProcessingState.LOCAL_EXTRACTION,
            ProcessingState.LLM_EXTRACTION,
            ProcessingState.MANUAL_REVIEW,
            ProcessingState.PREPARE_DATA,
            ProcessingState.CHUNKING,
        ]
        assert STATE_ORDER == expected


class TestStateTransitionValidatorWithoutData:
    """Test validate_transition() without state data (condition checks skipped)."""

    def test_valid_forward_transition(self):
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.NOT_STARTED,
                ProcessingState.INITIALIZED,
            )
            is True
        )

    def test_invalid_skip_transition(self):
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.NOT_STARTED,
                ProcessingState.LOCAL_EXTRACTION,
            )
            is False
        )

    def test_invalid_backward_transition(self):
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.MANUAL_REVIEW,
                ProcessingState.NOT_STARTED,
            )
            is False
        )

    def test_llm_self_transition(self):
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LLM_EXTRACTION,
                ProcessingState.LLM_EXTRACTION,
            )
            is True
        )

    def test_all_valid_transitions_pass(self):
        """Every defined transition should pass validate_transition (without data)."""
        for t in VALID_TRANSITIONS:
            result = StateTransitionValidator.validate_transition(t.from_state, t.to_state)
            assert result is True, f"Expected {t.from_state} -> {t.to_state} to be valid"


class TestStateTransitionValidatorWithData:
    """Test validate_transition() WITH state data (conditions checked)."""

    def _make_local_extraction_data(self, has_tables: bool) -> LocalExtractionData:
        """Helper to create LocalExtractionData with/without tables."""
        pages = {
            1: LocalExtractionPageData(
                has_tables=has_tables,
                num_tables=1 if has_tables else 0,
                text="Sample text",
            )
        }
        return LocalExtractionData(
            status=ProcessingStatus.SUCCESS,
            processing_metadata=ProcessingMetadata(
                processing_time_seconds=1.0,
                pages_processed=1,
                pages_failed=0,
            ),
            pages=pages,
            extracted_text_path="extracted_text.md",
        )

    def test_local_extraction_with_tables_goes_to_llm(self):
        data = self._make_local_extraction_data(has_tables=True)
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LOCAL_EXTRACTION,
                ProcessingState.LLM_EXTRACTION,
                data,
            )
            is True
        )

    def test_local_extraction_with_tables_blocked_from_manual_review(self):
        data = self._make_local_extraction_data(has_tables=True)
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LOCAL_EXTRACTION,
                ProcessingState.MANUAL_REVIEW,
                data,
            )
            is False
        )

    def test_local_extraction_no_tables_goes_to_manual_review(self):
        data = self._make_local_extraction_data(has_tables=False)
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LOCAL_EXTRACTION,
                ProcessingState.MANUAL_REVIEW,
                data,
            )
            is True
        )

    def test_local_extraction_no_tables_blocked_from_llm(self):
        data = self._make_local_extraction_data(has_tables=False)
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LOCAL_EXTRACTION,
                ProcessingState.LLM_EXTRACTION,
                data,
            )
            is False
        )

    def test_local_extraction_failed_status_blocks_transition(self):
        data = self._make_local_extraction_data(has_tables=False)
        data.status = ProcessingStatus.FAILED
        # Should fail because required_status is SUCCESS but data has FAILED
        assert (
            StateTransitionValidator.validate_transition(
                ProcessingState.LOCAL_EXTRACTION,
                ProcessingState.MANUAL_REVIEW,
                data,
            )
            is False
        )


class TestGetValidationDetails:
    """Test get_validation_details() for debugging info."""

    def test_valid_transition_details(self):
        details = StateTransitionValidator.get_validation_details(
            ProcessingState.NOT_STARTED,
            ProcessingState.INITIALIZED,
        )
        assert details["is_valid"] is True
        assert details["error"] is None
        assert details["current_state"] == "NOT_STARTED"
        assert details["target_state"] == "INITIALIZED"

    def test_invalid_transition_details(self):
        details = StateTransitionValidator.get_validation_details(
            ProcessingState.NOT_STARTED,
            ProcessingState.CHUNKING,
        )
        assert details["is_valid"] is False
        assert details["error"] is not None
        assert details["details"]["transition_exists"] is False

    def test_details_include_condition_info(self):
        details = StateTransitionValidator.get_validation_details(
            ProcessingState.LOCAL_EXTRACTION,
            ProcessingState.LLM_EXTRACTION,
        )
        # Without data, condition can't be checked
        assert "condition_check" in details["details"]
        assert details["details"]["condition"] == "has_tables"
