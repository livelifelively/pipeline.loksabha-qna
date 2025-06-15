"""
Report display utilities.

This module contains standalone functions for displaying and formatting
document processing reports in various formats (tables, summaries, etc.).
All functions are focused on presentation and formatting.
"""

import datetime
from pathlib import Path
from typing import Dict, List

from apps.py.types import ProcessingState, ProcessingStatus
from cli.py.utils.table import print_table

from ....apps.py.documents.utils.document_progress_analysis import get_ministry_document_counts, get_states_with_data


def display_overview_table(status_counters: Dict, total_documents: int, session_info: Dict, ministries: List[Path]):
    """Build and display the overview status table.

    Args:
        status_counters: Dictionary with structure {state: {status: count}}
        total_documents: Total number of documents processed
        session_info: Dictionary with session information (name, etc.)
        ministries: List of Path objects representing ministries
    """
    # Display ministry information prominently
    ministry_names = [ministry.name for ministry in ministries]
    if len(ministry_names) == 1:
        ministry_info = f"Ministry: {ministry_names[0]}"
    else:
        ministry_info = f"Ministries: {', '.join(ministry_names)}"

    print("\nProcessing Status Overview")
    print(f"Session: {session_info['name']}")
    print(f"{ministry_info}")
    print(f"Total Documents: {total_documents}")
    print("=" * 80)

    # Show ministry breakdown if multiple ministries selected
    if len(ministries) > 1:
        print("\nDocuments by Ministry:")
        ministry_doc_counts = get_ministry_document_counts(ministries)
        for ministry_name, doc_count in ministry_doc_counts.items():
            percentage = (doc_count / total_documents) * 100 if total_documents > 0 else 0
            print(f"  {ministry_name}: {doc_count} documents ({percentage:.1f}%)")
        print()

    # Build table data
    headers = ["State", "Success", "Failed", "Partial", "Total"]
    rows = []

    # Total counters for footer
    total_success = 0
    total_failed = 0
    total_partial = 0
    total_unprocessed = 0

    # Add regular processing states
    for state in ProcessingState:
        state_name = state.value
        success_count = status_counters[state][ProcessingStatus.SUCCESS]
        failed_count = status_counters[state][ProcessingStatus.FAILED]
        partial_count = status_counters[state][ProcessingStatus.PARTIAL]

        state_total = success_count + failed_count + partial_count

        # Only show states that have documents
        if state_total > 0:
            rows.append([state_name, str(success_count), str(failed_count), str(partial_count), str(state_total)])

            total_success += success_count
            total_failed += failed_count
            total_partial += partial_count

    # Add UNPROCESSED as a special row
    unprocessed_success = status_counters["UNPROCESSED"][ProcessingStatus.SUCCESS]
    unprocessed_failed = status_counters["UNPROCESSED"][ProcessingStatus.FAILED]
    unprocessed_partial = status_counters["UNPROCESSED"][ProcessingStatus.PARTIAL]
    unprocessed_total = unprocessed_success + unprocessed_failed + unprocessed_partial

    if unprocessed_total > 0:
        rows.append(
            [
                "UNPROCESSED",
                "-",  # No success/failed/partial distinction for unprocessed
                "-",
                "-",
                str(unprocessed_total),
            ]
        )
        total_unprocessed = unprocessed_total

    # Create footer with totals
    footer = ["TOTAL", str(total_success), str(total_failed), str(total_partial), str(total_documents)]

    # Display the table
    print_table(headers, rows, footer)

    # Additional summary information
    if total_documents > 0:
        processed_docs = total_documents - total_unprocessed
        processing_rate = (processed_docs / total_documents) * 100
        success_rate = (total_success / total_documents) * 100 if total_success > 0 else 0

        print("\nSummary:")
        print(f"  Documents processed: {processed_docs}/{total_documents} ({processing_rate:.1f}%)")
        if total_success > 0:
            print(f"  Success rate: {total_success}/{processed_docs} ({success_rate:.1f}%)")
        if total_failed > 0:
            print(f"  Failed documents: {total_failed}")
        if total_partial > 0:
            print(f"  Partially processed: {total_partial}")


def display_ministry_breakdown_table(ministry_status_data: Dict, session_info: Dict):
    """Display the ministry breakdown table as a cross-matrix.

    Args:
        ministry_status_data: Dictionary with structure {ministry_name: {state: {status: count}}}
        session_info: Dictionary with session information
    """
    # Display header information
    ministry_names = list(ministry_status_data.keys())
    print("\nMinistry Breakdown Report")
    print(f"Session: {session_info['name']}")
    print(f"Ministries: {len(ministry_names)}")
    print("=" * 100)

    # Since the full cross-matrix would be very wide, we'll create a simplified view
    # showing each state as a separate mini-table
    states_with_data = get_states_with_data(ministry_status_data)

    if not states_with_data:
        print("No processed documents found in any ministry.")
        return

    # Display summary table first
    display_ministry_summary_table(ministry_status_data)

    # Then display detailed breakdown by state
    for state in states_with_data:
        display_state_breakdown_table(ministry_status_data, state)


def display_ministry_summary_table(ministry_status_data: Dict):
    """Display a summary table with total documents per ministry.

    Args:
        ministry_status_data: Dictionary with ministry status data
    """
    print("\nMinistry Summary:")
    print("-" * 60)

    headers = ["Ministry", "Total Docs", "Processed", "Unprocessed", "Success Rate"]
    rows = []

    total_all_docs = 0
    total_processed = 0
    total_unprocessed = 0
    total_success = 0

    for ministry_name, ministry_data in ministry_status_data.items():
        # Calculate totals for this ministry
        ministry_total = 0
        ministry_success = 0
        ministry_unprocessed = ministry_data.get("UNPROCESSED", {}).get("SUCCESS", 0)

        # Count all documents across all states
        for state_key, status_counts in ministry_data.items():
            state_total = sum(status_counts.values())
            ministry_total += state_total
            if state_key != "UNPROCESSED":
                ministry_success += status_counts.get("SUCCESS", 0)

        ministry_processed = ministry_total - ministry_unprocessed
        success_rate = (ministry_success / ministry_processed * 100) if ministry_processed > 0 else 0

        rows.append(
            [
                ministry_name[:30] + "..." if len(ministry_name) > 30 else ministry_name,
                str(ministry_total),
                str(ministry_processed),
                str(ministry_unprocessed),
                f"{success_rate:.1f}%",
            ]
        )

        total_all_docs += ministry_total
        total_processed += ministry_processed
        total_unprocessed += ministry_unprocessed
        total_success += ministry_success

    # Calculate overall success rate
    overall_success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0

    footer = [
        "TOTAL",
        str(total_all_docs),
        str(total_processed),
        str(total_unprocessed),
        f"{overall_success_rate:.1f}%",
    ]

    print_table(headers, rows, footer)


def display_state_breakdown_table(ministry_status_data: Dict, state):
    """Display breakdown table for a specific processing state.

    Args:
        ministry_status_data: Dictionary with ministry status data
        state: Processing state to display
    """
    state_name = state.value if hasattr(state, "value") else str(state)

    print(f"\n{state_name} State Breakdown:")
    print("-" * 60)

    headers = ["Ministry", "Success", "Failed", "Partial", "Total"]
    rows = []

    total_success = 0
    total_failed = 0
    total_partial = 0
    total_docs = 0

    for ministry_name, ministry_data in ministry_status_data.items():
        state_data = ministry_data.get(state, {})

        success_count = state_data.get(ProcessingStatus.SUCCESS, 0)
        failed_count = state_data.get(ProcessingStatus.FAILED, 0)
        partial_count = state_data.get(ProcessingStatus.PARTIAL, 0)
        state_total = success_count + failed_count + partial_count

        # Only show ministries that have documents in this state
        if state_total > 0:
            rows.append(
                [
                    ministry_name[:30] + "..." if len(ministry_name) > 30 else ministry_name,
                    str(success_count),
                    str(failed_count),
                    str(partial_count),
                    str(state_total),
                ]
            )

            total_success += success_count
            total_failed += failed_count
            total_partial += partial_count
            total_docs += state_total

    if rows:  # Only display if there are rows to show
        if state == "UNPROCESSED":
            # For unprocessed, don't show success/failed/partial breakdown
            headers = ["Ministry", "Documents"]
            rows = [[row[0], row[4]] for row in rows]
            footer = ["TOTAL", str(total_docs)]
        else:
            footer = ["TOTAL", str(total_success), str(total_failed), str(total_partial), str(total_docs)]

        print_table(headers, rows, footer)
    else:
        print("  No documents in this state.")


def display_document_details_table(
    documents: List[Dict], ministry: Path, filter_options: List[str], session_info: Dict
):
    """Display the document details table.

    Args:
        documents: List of filtered document dictionaries
        ministry: Selected ministry Path object
        filter_options: List of applied filter options
        session_info: Dictionary with session information
    """
    # Display header information
    print("\nDocument Details Report")
    print(f"Session: {session_info['name']}")
    print(f"Ministry: {ministry.name}")

    if filter_options:
        filter_names = {
            "tables_only": "Documents with tables only",
            "failed_only": "Failed documents only",
            "specific_state": "Specific processing state",
        }
        applied_filters = [filter_names[f] for f in filter_options if f in filter_names]
        print(f"Filters: {', '.join(applied_filters)}")

    print("=" * 120)

    if not documents:
        print("No documents match the selected filters.")
        return

    # Sort documents by state, then by name
    sorted_docs = sorted(documents, key=lambda x: (x["state"], x["name"]))

    # Build table
    headers = ["Document Name", "State", "Status", "Tables", "Last Updated", "Error Details"]
    rows = []

    for doc in sorted_docs:
        # Format document name (truncate if too long)
        doc_name = doc["name"]
        if len(doc_name) > 25:
            doc_name = doc_name[:22] + "..."

        # Format last updated time
        last_updated = doc["last_updated"]
        if last_updated != "-" and isinstance(last_updated, (int, float)):
            try:
                dt = datetime.datetime.fromtimestamp(last_updated)
                last_updated = dt.strftime("%Y-%m-%d %H:%M")
            except:
                last_updated = "Invalid date"

        # Format error details (truncate if extremely long but keep readable)
        error_details = doc["error_details"]
        if error_details != "-" and len(error_details) > 50:
            # Keep full error but break it nicely if it's very long
            if len(error_details) > 200:
                error_details = error_details[:197] + "..."

        rows.append([doc_name, doc["state"], doc["status"], doc["tables"], last_updated, error_details])

    # Display table
    print_table(headers, rows)

    # Display summary statistics
    display_document_summary_stats(sorted_docs, filter_options)


def display_document_summary_stats(documents: List[Dict], filter_options: List[str]):
    """Display summary statistics for the document details report.

    Args:
        documents: List of document dictionaries
        filter_options: List of applied filter options
    """
    total_docs = len(documents)

    if total_docs == 0:
        return

    # Count by status
    status_counts = {}
    state_counts = {}

    for doc in documents:
        status = doc["status"]
        state = doc["state"]

        status_counts[status] = status_counts.get(status, 0) + 1
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nSummary:")
    print(f"  Total documents shown: {total_docs}")

    # Show status breakdown
    if len(status_counts) > 1:
        status_parts = []
        for status, count in sorted(status_counts.items()):
            if status != "-":
                status_parts.append(f"{status}: {count}")
        if status_parts:
            print(f"  Status breakdown: {', '.join(status_parts)}")

    # Show state breakdown if not filtered by specific state
    if "specific_state" not in filter_options and len(state_counts) > 1:
        state_parts = []
        for state, count in sorted(state_counts.items()):
            state_parts.append(f"{state}: {count}")
        print(f"  State breakdown: {', '.join(state_parts)}")

    # Show documents with tables count if not filtered by tables_only
    if "tables_only" not in filter_options:
        docs_with_tables = sum(1 for doc in documents if doc["has_tables"])
        if docs_with_tables > 0:
            print(f"  Documents with tables: {docs_with_tables}/{total_docs}")


def display_report_header(report_type: str, session_info: Dict, ministries: List[Path] = None):
    """Display a standardized report header.

    Args:
        report_type: Type of report being displayed
        session_info: Dictionary with session information
        ministries: Optional list of ministries for ministry-specific reports
    """
    print("\n" + "=" * 60)
    print(report_type.upper())
    print("=" * 60)
    print(f"Session: {session_info['name']}")

    if ministries:
        if len(ministries) == 1:
            print(f"Ministry: {ministries[0].name}")
        else:
            print(f"Ministries: {len(ministries)} selected")

    print()


def display_processing_summary(total_documents: int, ministry_counts: Dict[str, int] = None):
    """Display a summary of documents being processed.

    Args:
        total_documents: Total number of documents
        ministry_counts: Optional dictionary of ministry document counts
    """
    print(f"Total Documents: {total_documents}")

    if ministry_counts and len(ministry_counts) > 1:
        print("\nDocuments by Ministry:")
        for ministry_name, count in ministry_counts.items():
            percentage = (count / total_documents) * 100 if total_documents > 0 else 0
            print(f"  {ministry_name}: {count} documents ({percentage:.1f}%)")

    print("-" * 60)
