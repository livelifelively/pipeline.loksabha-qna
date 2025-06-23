import sys
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[4]))

# Import analysis functions from utils
from apps.py.documents.utils import (
    analyze_document_details,
    analyze_documents_status,
    analyze_ministry_breakdown,
    apply_document_filters,
)
from apps.py.parliament_questions.document_processing import find_all_document_paths
from apps.py.types import ProcessingState
from cli.py.extract_pdf.report_display import (
    display_document_details_table,
    display_ministry_breakdown_table,
    display_overview_table,
)


class BaseWorkflow:
    """Base class for workflows."""

    def __init__(self):
        """Initialize the workflow with empty state."""
        self.selected_sansad = None
        self.selected_session = None
        self.selected_ministries = None


class DocumentProcessingReports(BaseWorkflow):
    """Class to handle document processing status reports."""

    def __init__(self):
        """Initialize the reports workflow."""
        super().__init__()

    def run_overview_report(self):
        """Generate overview report across all selected ministries."""
        # Get selections using common workflow
        from .menu import get_selection_workflow  # Import here to avoid circular import

        sansad, session, ministries = get_selection_workflow()

        if not sansad:  # Selection was cancelled
            return

        # Find all document paths in selected ministries
        all_document_paths = find_all_document_paths(ministries)

        if not all_document_paths:
            print("No documents found in the selected ministries.")
            inquirer.text(message="\nPress Enter to continue...").execute()
            return

        # Analyze status of all documents (using standalone function)
        status_counters = analyze_documents_status(all_document_paths)

        # Display the overview table (using standalone function)
        session_info = {"name": session.name}
        display_overview_table(status_counters, len(all_document_paths), session_info, ministries)

        inquirer.text(message="\nPress Enter to continue...").execute()

    def run_ministry_breakdown_report(self):
        """Generate ministry-wise breakdown report."""
        # Get selections using common workflow
        from .menu import get_selection_workflow  # Import here to avoid circular import

        sansad, session, ministries = get_selection_workflow()

        if not sansad:  # Selection was cancelled
            return

        # Find all document paths in selected ministries
        all_document_paths = find_all_document_paths(ministries)

        if not all_document_paths:
            print("No documents found in the selected ministries.")
            inquirer.text(message="\nPress Enter to continue...").execute()
            return

        # Analyze status by ministry (using standalone function)
        ministry_status_data = analyze_ministry_breakdown(ministries)

        # Display the ministry breakdown table (using standalone function)
        session_info = {"name": session.name}
        display_ministry_breakdown_table(ministry_status_data, session_info)

        inquirer.text(message="\nPress Enter to continue...").execute()

    def run_document_details_report(self):
        """Generate document-level detailed report."""
        # Get selections using common workflow
        from .menu import get_selection_workflow  # Import here to avoid circular import

        sansad, session, ministries = get_selection_workflow()

        if not sansad:  # Selection was cancelled
            return

        # Ask for filtering options
        filter_options = inquirer.checkbox(
            message="Select filter options (optional):",
            choices=[
                Choice(value="tables_only", name="Show only documents with tables"),
                Choice(value="failed_only", name="Show only failed documents"),
                Choice(value="specific_state", name="Show only specific processing state"),
            ],
            instruction="(Use space to select, enter to confirm)",
        ).execute()

        # Handle specific state filter
        selected_state = None
        if "specific_state" in filter_options:
            state_choices = [Choice(value=state, name=state.value) for state in ProcessingState]
            state_choices.append(Choice(value="UNPROCESSED", name="UNPROCESSED"))

            selected_state = inquirer.select(
                message="Select processing state to filter by:",
                choices=state_choices,
            ).execute()

        # Select ministry if multiple are chosen
        selected_ministry = None
        if len(ministries) > 1:
            ministry_choices = [Choice(value=ministry, name=ministry.name) for ministry in ministries]
            selected_ministry = inquirer.select(
                message="Select ministry for document details:",
                choices=ministry_choices,
            ).execute()
        else:
            selected_ministry = ministries[0]

        # Analyze documents in the selected ministry (using standalone function)
        document_details = analyze_document_details(selected_ministry)

        # Apply filters (using standalone function)
        filtered_documents = apply_document_filters(document_details, filter_options, selected_state)

        # Display results (using standalone function)
        session_info = {"name": session.name}
        display_document_details_table(filtered_documents, selected_ministry, filter_options, session_info)

        inquirer.text(message="\nPress Enter to continue...").execute()


def overview_report_workflow():
    """Entry point for the overview report workflow."""
    workflow = DocumentProcessingReports()
    workflow.run_overview_report()


def ministry_breakdown_workflow():
    """Entry point for the ministry breakdown workflow."""
    workflow = DocumentProcessingReports()
    workflow.run_ministry_breakdown_report()


def document_details_workflow():
    """Entry point for the document details workflow."""
    workflow = DocumentProcessingReports()
    workflow.run_document_details_report()
