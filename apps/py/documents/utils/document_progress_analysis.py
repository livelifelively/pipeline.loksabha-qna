"""
Document progress analysis utilities.

This module contains standalone functions for analyzing document processing states,
extracting progress information, and performing data analysis on document collections.
All functions are pure and reusable across different contexts.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

from apps.py.types import ProcessingState, ProcessingStatus

from .progress_handler import DocumentProgressHandler


def get_document_table_info(progress_handler: DocumentProgressHandler) -> Dict[str, Union[bool, str]]:
    """Get table information for a document based on its progress state.

    Table information is only available if the document has successfully
    completed LOCAL_EXTRACTION state or is in a later state.

    Args:
        progress_handler: DocumentProgressHandler instance for the document

    Returns:
        dict: Dictionary with keys:
            - has_tables (bool): Whether document has tables
            - table_count (str): Number of tables as string, or "-" if not available
            - table_info_available (bool): Whether table info is reliable

    Example:
        >>> from apps.py.documents.utils import DocumentProgressHandler, get_document_table_info
        >>> progress_handler = DocumentProgressHandler(document_path)
        >>> table_info = get_document_table_info(progress_handler)
        >>> if table_info["has_tables"]:
        ...     print(f"Document has {table_info['table_count']} tables")
    """
    # Default values for documents without table info
    result = {"has_tables": False, "table_count": "-", "table_info_available": False}

    try:
        # Check if LOCAL_EXTRACTION state exists and was successful
        local_extraction_data = progress_handler.get_state_data(ProcessingState.LOCAL_EXTRACTION)
        if not local_extraction_data:
            return result

        # Check LOCAL_EXTRACTION status
        local_extraction_status = None
        if hasattr(local_extraction_data, "status"):
            local_extraction_status = (
                local_extraction_data.status.value
                if hasattr(local_extraction_data.status, "value")
                else str(local_extraction_data.status)
            )
        elif isinstance(local_extraction_data, dict) and "status" in local_extraction_data:
            local_extraction_status = local_extraction_data["status"]

        # Only trust table info if LOCAL_EXTRACTION was successful
        if local_extraction_status != "SUCCESS":
            return result

        # Extract table information
        result["table_info_available"] = True

        if hasattr(local_extraction_data, "has_tables"):
            result["has_tables"] = local_extraction_data.has_tables
            if hasattr(local_extraction_data, "total_tables"):
                result["table_count"] = (
                    str(local_extraction_data.total_tables) if local_extraction_data.has_tables else "0"
                )
            else:
                result["table_count"] = "0"
        elif isinstance(local_extraction_data, dict) and "has_tables" in local_extraction_data:
            result["has_tables"] = local_extraction_data["has_tables"]
            if "total_tables" in local_extraction_data:
                result["table_count"] = (
                    str(local_extraction_data["total_tables"]) if local_extraction_data["has_tables"] else "0"
                )
            else:
                result["table_count"] = "0"

        return result

    except Exception:
        # Return default values on any error
        return result


def is_document_processed_successfully(
    progress_handler: DocumentProgressHandler, min_state: ProcessingState = ProcessingState.LOCAL_EXTRACTION
) -> bool:
    """Check if a document has been processed successfully up to a minimum state.

    Args:
        progress_handler: DocumentProgressHandler instance for the document
        min_state: Minimum processing state required (default: LOCAL_EXTRACTION)

    Returns:
        bool: True if document has successfully reached the minimum state

    Example:
        >>> progress_handler = DocumentProgressHandler(document_path)
        >>> if is_document_processed_successfully(progress_handler):
        ...     print("Document has been successfully processed")
    """
    try:
        current_state = progress_handler.get_current_state()
        if not current_state:
            return False

        # Check if current state is at least the minimum required state
        from apps.py.types import STATE_ORDER

        if current_state not in STATE_ORDER or min_state not in STATE_ORDER:
            return False

        current_index = STATE_ORDER.index(current_state)
        min_index = STATE_ORDER.index(min_state)

        if current_index < min_index:
            return False

        # Check if the minimum state was successful
        state_data = progress_handler.get_state_data(min_state)
        if not state_data:
            return False

        status = None
        if hasattr(state_data, "status"):
            status = state_data.status.value if hasattr(state_data.status, "value") else str(state_data.status)
        elif isinstance(state_data, dict) and "status" in state_data:
            status = state_data["status"]

        return status == "SUCCESS"

    except Exception:
        return False


def get_state_data(progress_handler: DocumentProgressHandler, current_state: ProcessingState):
    """Get state data for a given processing state.

    Args:
        progress_handler: DocumentProgressHandler instance
        current_state: ProcessingState enum value

    Returns:
        State data object or None if not available
    """
    try:
        state_data = None
        if current_state == ProcessingState.INITIALIZED:
            state_data = progress_handler.get_initialized_data()
        elif current_state == ProcessingState.LOCAL_EXTRACTION:
            state_data = progress_handler.get_local_extraction_data()
        elif current_state == ProcessingState.LLM_EXTRACTION:
            state_data = progress_handler.get_llm_extraction_data()
        elif current_state == ProcessingState.MANUAL_REVIEW:
            state_data = progress_handler.get_manual_review_data()
        elif current_state == ProcessingState.CHUNKING:
            state_data = progress_handler.get_chunking_data()

        # Debug: Check what type of data we're getting
        if state_data is not None:
            if isinstance(state_data, dict):
                # It's a dictionary - check if it has status
                if "status" not in state_data:
                    print(f"  Debug: State data is dict but missing 'status' key. Keys: {list(state_data.keys())}")
            elif not hasattr(state_data, "status"):
                print(f"  Debug: State data is {type(state_data)} but has no 'status' attribute")

        return state_data
    except Exception as e:
        print(f"  Debug: Exception in get_state_data: {str(e)}")
        return None


def analyze_documents_status(document_paths: List[Path]) -> Dict:
    """Analyze status of all documents and return counters.

    Args:
        document_paths: List of Path objects representing document directories

    Returns:
        dict: Nested dictionary with structure {state: {status: count}}
    """
    # Initialize counters for all states
    status_counters = {}
    for state in ProcessingState:
        status_counters[state] = {
            ProcessingStatus.SUCCESS: 0,
            ProcessingStatus.FAILED: 0,
            ProcessingStatus.PARTIAL: 0,
        }

    # Add UNPROCESSED as a special case
    status_counters["UNPROCESSED"] = {
        ProcessingStatus.SUCCESS: 0,
        ProcessingStatus.FAILED: 0,
        ProcessingStatus.PARTIAL: 0,
    }

    processed_count = 0
    error_count = 0

    for doc_path in document_paths:
        try:
            processed_count += 1

            # Check if progress file exists
            progress_file = doc_path / "question.progress.json"
            if not progress_file.exists():
                # Document has never been processed
                status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS] += 1
                continue

            # Create progress handler and get current state
            progress_handler = DocumentProgressHandler(doc_path)
            current_state = progress_handler.get_current_state()

            if current_state is None:
                # Progress file exists but no valid state - treat as unprocessed
                status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS] += 1
                continue

            # Get state-specific data to extract status
            state_data = get_state_data(progress_handler, current_state)

            if state_data is None:
                # Could not get state data - treat as unprocessed
                status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS] += 1
                continue

            # Extract status from state data - handle both typed objects and dictionaries
            if hasattr(state_data, "status"):
                # Typed object with status attribute
                status = state_data.status
            elif isinstance(state_data, dict) and "status" in state_data:
                # Dictionary with status key - convert to ProcessingStatus enum
                status_str = state_data["status"]
                try:
                    status = ProcessingStatus(status_str)
                except ValueError:
                    # Invalid status value - treat as unprocessed
                    status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS] += 1
                    continue
            else:
                # No status information available - treat as unprocessed
                status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS] += 1
                continue

            status_counters[current_state][status] += 1

        except Exception as e:
            error_count += 1
            # Log error but continue processing
            print(f"  Warning: Error processing {doc_path.name}: {str(e)}")
            status_counters["UNPROCESSED"][ProcessingStatus.FAILED] += 1

    if error_count > 0:
        print(f"  Warning: {error_count} documents had processing errors")

    return status_counters


def analyze_ministry_breakdown(ministries: List[Path]) -> Dict:
    """Analyze document status breakdown by ministry.

    Args:
        ministries: List of Path objects representing ministry directories

    Returns:
        dict: Nested dictionary with structure {ministry_name: {state: {status: count}}}
    """
    from apps.py.parliament_questions.document_processing import find_document_paths

    ministry_status_data = {}

    for ministry in ministries:
        ministry_name = ministry.name
        ministry_status_data[ministry_name] = {}

        # Initialize counters for all states
        for state in ProcessingState:
            ministry_status_data[ministry_name][state] = {
                ProcessingStatus.SUCCESS: 0,
                ProcessingStatus.FAILED: 0,
                ProcessingStatus.PARTIAL: 0,
            }

        # Add UNPROCESSED as a special case
        ministry_status_data[ministry_name]["UNPROCESSED"] = {
            ProcessingStatus.SUCCESS: 0,
            ProcessingStatus.FAILED: 0,
            ProcessingStatus.PARTIAL: 0,
        }

        # Find documents for this ministry
        ministry_docs = find_document_paths(ministry)

        # Analyze each document in this ministry
        ministry_counters = analyze_documents_status(ministry_docs)

        # Copy the results to our ministry-specific structure
        for state_key, status_counts in ministry_counters.items():
            ministry_status_data[ministry_name][state_key] = status_counts.copy()

    return ministry_status_data


def analyze_document_details(ministry: Path) -> List[Dict]:
    """Analyze individual documents in a ministry for detailed reporting.

    Args:
        ministry: Path object representing the ministry directory

    Returns:
        list: List of dictionaries with detailed document information
    """
    from apps.py.parliament_questions.document_processing import find_document_paths

    document_details = []

    # Find all documents in this ministry
    ministry_docs = find_document_paths(ministry)

    for doc_path in ministry_docs:
        try:
            # Get basic document info
            pdf_files = list(doc_path.glob("*.pdf"))
            pdf_name = pdf_files[0].name if pdf_files else "Unknown PDF"

            # Initialize document info
            doc_info = {
                "name": pdf_name,
                "path": doc_path,
                "state": "UNPROCESSED",
                "status": "-",
                "tables": "-",
                "last_updated": "-",
                "error_details": "-",
                "has_tables": False,
                "question_number": "-",
            }

            # Check if progress file exists
            progress_file = doc_path / "question.progress.json"
            if not progress_file.exists():
                # Document has never been processed
                document_details.append(doc_info)
                continue

            # Get last modified time of progress file
            doc_info["last_updated"] = progress_file.stat().st_mtime

            # Create progress handler and get current state
            progress_handler = DocumentProgressHandler(doc_path)
            current_state = progress_handler.get_current_state()

            if current_state is None:
                # Progress file exists but no valid state
                document_details.append(doc_info)
                continue

            # Update state information
            doc_info["state"] = current_state.value if hasattr(current_state, "value") else str(current_state)

            # Get state-specific data
            state_data = get_state_data(progress_handler, current_state)

            if state_data is not None:
                # Extract status
                if hasattr(state_data, "status"):
                    doc_info["status"] = (
                        state_data.status.value if hasattr(state_data.status, "value") else str(state_data.status)
                    )
                elif isinstance(state_data, dict) and "status" in state_data:
                    doc_info["status"] = state_data["status"]

                # Extract error details for failed documents
                if doc_info["status"] in ["FAILED", "PARTIAL"]:
                    if hasattr(state_data, "error_message") and state_data.error_message:
                        doc_info["error_details"] = state_data.error_message
                    elif isinstance(state_data, dict) and "error_message" in state_data and state_data["error_message"]:
                        doc_info["error_details"] = state_data["error_message"]

                # Extract table information using the utility function
                table_info = get_document_table_info(progress_handler)
                doc_info["has_tables"] = table_info["has_tables"]
                doc_info["tables"] = table_info["table_count"]

                # Extract question number for INITIALIZED state
                if current_state == ProcessingState.INITIALIZED:
                    if hasattr(state_data, "question_number"):
                        doc_info["question_number"] = str(state_data.question_number)
                    elif isinstance(state_data, dict) and "question_number" in state_data:
                        doc_info["question_number"] = str(state_data["question_number"])

            document_details.append(doc_info)

        except Exception as e:
            # Handle individual document errors gracefully
            error_doc_info = {
                "name": pdf_name if "pdf_name" in locals() else doc_path.name,
                "path": doc_path,
                "state": "ERROR",
                "status": "FAILED",
                "tables": "-",
                "last_updated": "-",
                "error_details": f"Analysis error: {str(e)}",
                "has_tables": False,
                "question_number": "-",
            }
            document_details.append(error_doc_info)

    return document_details


def get_ministry_document_counts(ministries: List[Path]) -> Dict[str, int]:
    """Get document counts per ministry.

    Args:
        ministries: List of Path objects representing ministry directories

    Returns:
        dict: Dictionary with ministry names as keys and document counts as values
    """
    from apps.py.parliament_questions.document_processing import find_document_paths

    ministry_doc_counts = {}

    for ministry in ministries:
        ministry_docs = find_document_paths(ministry)
        ministry_doc_counts[ministry.name] = len(ministry_docs)

    return ministry_doc_counts


def get_states_with_data(ministry_status_data: Dict) -> List:
    """Get list of states that have documents across all ministries.

    Args:
        ministry_status_data: Dictionary with ministry status data

    Returns:
        list: List of states that have at least one document
    """
    states_with_data = []
    all_states = list(ProcessingState) + ["UNPROCESSED"]

    for state in all_states:
        has_data = False
        for ministry_data in ministry_status_data.values():
            state_counts = ministry_data.get(state, {})
            total_for_state = sum(state_counts.values())
            if total_for_state > 0:
                has_data = True
                break
        if has_data:
            states_with_data.append(state)

    return states_with_data


def apply_document_filters(
    documents: List[Dict], filter_options: List[str], selected_state: Optional[ProcessingState]
) -> List[Dict]:
    """Apply user-selected filters to the document list.

    Args:
        documents: List of document dictionaries
        filter_options: List of selected filter options
        selected_state: Selected processing state (if specific_state filter is applied)

    Returns:
        list: Filtered list of document dictionaries
    """
    filtered_docs = []

    for doc in documents:
        # Apply tables_only filter
        if "tables_only" in filter_options:
            if not doc["has_tables"]:
                continue

        # Apply failed_only filter
        if "failed_only" in filter_options:
            if doc["status"] not in ["FAILED", "PARTIAL"]:
                continue

        # Apply specific_state filter
        if "specific_state" in filter_options and selected_state:
            doc_state = doc["state"]
            filter_state = selected_state.value if hasattr(selected_state, "value") else str(selected_state)
            if doc_state != filter_state:
                continue

        filtered_docs.append(doc)

    return filtered_docs
