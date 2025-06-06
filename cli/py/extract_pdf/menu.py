import asyncio
import sys
import time
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

# from cli.py.utils.paths import find_document_paths

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[4]))

# Import but don't call directly - we'll handle async separately
from apps.py.documents.extractors.orchestrator import PDFExtractionOrchestrator
from apps.py.parliament_questions.document_processing import (
    calculate_table_statistics,
    find_all_document_paths,
    find_document_paths,
    find_documents_with_tables,
    save_ministry_extraction_results,
)
from apps.py.parliament_questions.pdf_extraction import QuestionPDFExtractor
from apps.py.utils.project_root import get_loksabha_data_root
from cli.py.utils.table import print_table  # Import the table utility


def pdf_menu():
    """Menu for PDF-related operations."""
    while True:
        # Clear the screen for better UI experience
        print("\033c", end="")

        print("PDF Tools")
        print("---------\n")

        # PDF submenu selection
        action = inquirer.select(
            message="Select an operation:",
            choices=[
                Choice(value="extract", name="Extract Text from PDF"),
                Choice(value="fix_tables", name="Fix Tables in Using AI"),
                Choice(value="back", name="Back to Main Menu"),
            ],
            default="extract",
        ).execute()

        if action == "extract":
            extract_pdf_workflow()
        elif action == "fix_tables":
            fix_tables_workflow()
        elif action == "back":
            break


class BaseWorkflow:
    """Base class for PDF workflows."""

    def __init__(self):
        """Initialize the workflow with empty state."""
        self.selected_sansad = None
        self.selected_session = None
        self.selected_ministries = None

    def display_selection_summary(self, ministry_doc_counts, total_docs):
        """Display a summary of the selected items with document counts.

        Args:
            ministry_doc_counts: Dictionary mapping ministry names to document counts
            total_docs: Total number of documents to process
        """
        print("\nSelected:")
        print(f"  Sansad: {self.selected_sansad.name}")
        print(f"  Session: {self.selected_session.name}")
        print(f"  Ministries: {', '.join(ministry.name for ministry in self.selected_ministries)}")
        print(f"  Total ministries selected: {len(self.selected_ministries)}")
        print(f"  Total documents to process: {total_docs}")

        # Show document count breakdown if there are multiple ministries
        if len(self.selected_ministries) > 1:
            print("\nDocuments per ministry:")
            for ministry_name, doc_count in ministry_doc_counts.items():
                print(f"  {ministry_name}: {doc_count} document(s)")


class ExtractPDFWorkflow(BaseWorkflow):
    """Class to handle the workflow for extracting text from PDFs."""

    def __init__(self):
        """Initialize the workflow with empty state."""
        super().__init__()
        self.extractor_type = "marker"
        self.overall_results = {
            "total_ministries": 0,
            "total_processed": 0,
            "total_failed": 0,
            "ministry_results": [],
        }

    def run(self):
        """Main entry point to run the workflow."""
        # Get selections using common workflow
        self.selected_sansad, self.selected_session, self.selected_ministries = get_selection_workflow()

        if not self.selected_sansad:  # Selection was cancelled
            return

        self.overall_results["total_ministries"] = len(self.selected_ministries)
        self.process_ministries()
        self.display_overall_summary()

    def process_ministries(self):
        """Process each ministry separately."""
        for ministry in self.selected_ministries:
            ministry_result = self.process_ministry(ministry)
            if ministry_result:
                self.overall_results["total_processed"] += ministry_result["total_processed"]
                self.overall_results["total_failed"] += ministry_result["total_failed"]
                self.overall_results["ministry_results"].append(
                    {"ministry_name": ministry.name, "results": ministry_result}
                )

    def process_ministry(self, ministry):
        """Process a single ministry's documents.

        Args:
            ministry: Path object representing the ministry directory

        Returns:
            dict: Results of processing the ministry's documents
        """
        self.display_ministry_header(ministry)
        document_paths = self.get_ministry_documents(ministry)
        if not document_paths:
            return None

        if not self.wait_for_potential_rejection(ministry, len(document_paths)):
            return None

        return self.extract_documents(ministry, document_paths)

    def display_ministry_header(self, ministry):
        """Display header information for ministry processing.

        Args:
            ministry: Path object representing the ministry directory
        """
        print(f"\n\nProcessing Ministry: {ministry.name}")
        print("=" * 50)

    def get_ministry_documents(self, ministry):
        """Get document paths for a ministry.

        Args:
            ministry: Path object representing the ministry directory

        Returns:
            list: List of document paths, or empty list if none found
        """
        document_paths = find_document_paths(ministry)
        if not document_paths:
            print(f"No PDF documents found in ministry: {ministry.name}")
            return []

        print(f"Found {len(document_paths)} document paths with PDF files in {ministry.name}.")
        return document_paths

    def wait_for_potential_rejection(self, ministry, num_documents):
        """Display countdown and wait for potential user rejection.

        This function shows a countdown and allows the user to cancel the operation
        by pressing Ctrl+C. If no cancellation occurs, the operation proceeds.

        Args:
            ministry: Path object representing the ministry directory
            num_documents: Number of documents to process

        Returns:
            bool: True if operation should proceed, False if user cancelled
        """
        print("Starting extraction in 10 seconds...")
        print("(Press Ctrl+C to cancel)")

        # Countdown timer with option to cancel
        for i in range(10, 0, -1):
            print(f"Starting in {i} seconds...", end="\r")
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nExtraction cancelled for ministry: {ministry.name}")
                return False

        print("\nStarting extraction for ministry: {ministry.name}".ljust(60))
        return True

    def extract_documents(self, ministry, document_paths):
        """Extract text from ministry documents.

        Args:
            ministry: Path object representing the ministry directory
            document_paths: List of document paths to process

        Returns:
            dict: Results of the extraction process
        """
        try:
            print(f"Starting extraction of {len(document_paths)} documents...")

            # Create PDFExtractor instance
            extractor = QuestionPDFExtractor(extractor_type=self.extractor_type)
            processed_documents = []
            failed_extractions = []

            for i, doc_dir in enumerate(document_paths):
                try:
                    result = self.process_single_document(extractor, doc_dir, i, len(document_paths))
                    if result:
                        processed_documents.append(result)
                except Exception as e:
                    failed_extractions.append({"path": str(doc_dir), "error": str(e)})
                    print(f"  ✗ Extraction failed: {doc_dir.name} - {str(e)}")

            results = self.create_extraction_results(processed_documents, failed_extractions)
            self.display_extraction_results(ministry, results)
            self.save_extraction_results(results, ministry)

            return results

        except Exception as e:
            print(f"\nError during extraction process for {ministry.name}: {str(e)}")
            return None

    def process_single_document(self, extractor, doc_dir, index, total_docs):
        """Process a single document.

        Args:
            extractor: PDFExtractor instance
            doc_dir: Path to document directory
            index: Current document index
            total_docs: Total number of documents

        Returns:
            dict: Document processing result, or None if failed
        """
        # Find PDF file in the document directory
        pdf_files = list(doc_dir.glob("*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF file found in directory: {doc_dir}")

        pdf_path = pdf_files[0]  # Take the first PDF if multiple exist

        # Show progress
        print(f"Processing [{index + 1}/{total_docs}]: {pdf_path.name}")

        # Extract contents using the extractor instance
        result = asyncio.run(extractor.extract_contents(pdf_path))
        print(f"  ✓ Extraction successful: {pdf_path.name}")

        # Convert to relative path
        relative_path = extractor._get_relative_path(pdf_path)
        return {"path": relative_path, "result": result}

    def create_extraction_results(self, processed_documents, failed_extractions):
        """Create the final extraction results dictionary.

        Args:
            processed_documents: List of successfully processed documents
            failed_extractions: List of failed extractions

        Returns:
            dict: Complete extraction results
        """
        status = "SUCCESS" if not failed_extractions else "PARTIAL"
        return {
            "status": status,
            "total_processed": len(processed_documents),
            "total_failed": len(failed_extractions),
            "extracted_documents": processed_documents,
            "failed_extractions": failed_extractions,
        }

    def display_extraction_results(self, ministry, results):
        """Display extraction results for a ministry.

        Args:
            ministry: Path object representing the ministry directory
            results: Dictionary containing extraction results
        """
        print(f"\nExtraction Complete for {ministry.name}!")
        print(f"Status: {results['status']}")
        print(f"Documents processed: {results['total_processed']}")
        print(f"Documents failed: {results['total_failed']}")

    def save_extraction_results(self, results, ministry):
        """Save extraction results for a ministry.

        Args:
            results: Dictionary containing extraction results
            ministry: Path object representing the ministry directory
        """
        if not self.selected_session:
            print("Warning: No session selected, cannot save results")
            return

        save_ministry_extraction_results(results, str(self.selected_session), ministry.name)

    def display_overall_summary(self):
        """Display overall summary of the extraction process."""
        print("\nOverall Extraction Results:")
        print(
            f"Total ministries processed: {len(self.overall_results['ministry_results'])}/{self.overall_results['total_ministries']}"
        )
        print(f"Total documents processed: {self.overall_results['total_processed']}")
        print(f"Total documents failed: {self.overall_results['total_failed']}")

        inquirer.text(message="Press Enter to continue...").execute()


def extract_pdf_workflow():
    """Entry point for the PDF extraction workflow."""
    workflow = ExtractPDFWorkflow()
    workflow.run()


class SelectionWorkflow:
    """Class to handle the selection workflow for PDF operations."""

    def __init__(self):
        """Initialize the workflow with empty state."""
        self.data_root = get_loksabha_data_root()
        self.selected_sansad = None
        self.selected_session = None
        self.selected_ministries = None
        self.ministry_doc_counts = {}
        self.all_ministry_docs = []

    def run(self):
        """Run the selection workflow.

        Returns:
            tuple: (selected_sansad, selected_session, selected_ministries)
            Any of these can be None if selection was cancelled
        """
        self.select_sansad()
        if not self.selected_sansad:
            return None, None, None

        self.select_session()
        if not self.selected_session:
            return None, None, None

        self.select_ministries()
        if not self.selected_ministries:
            return None, None, None

        self.count_documents()
        self.display_summary()

        return self.selected_sansad, self.selected_session, self.selected_ministries

    def select_sansad(self):
        """Select a sansad from the data root directory."""
        # Get a list of all sansad directories and sort them
        sansad_dirs = sorted([d for d in self.data_root.iterdir() if d.is_dir()], key=lambda x: x.name)

        if not sansad_dirs:
            print("\nNo sansad directories found in data root.")
            inquirer.text(message="Press Enter to continue...").execute()
            return

        # Create choices for the sansad selection
        sansad_choices = [Choice(value=str(d), name=d.name) for d in sansad_dirs]

        # Ask user to select a sansad
        selected_sansad_path = inquirer.select(
            message="Select a Sansad/Loksabha:",
            choices=sansad_choices,
        ).execute()

        self.selected_sansad = Path(selected_sansad_path)

    def select_session(self):
        """Select a session from the given sansad."""
        # Get all session directories for the selected sansad and sort them
        session_dirs = sorted([d for d in self.selected_sansad.iterdir() if d.is_dir()], key=lambda x: x.name)

        if not session_dirs:
            print(f"\nNo session directories found in {self.selected_sansad.name}.")
            inquirer.text(message="Press Enter to continue...").execute()
            return

        # Create choices for the session selection
        session_choices = [Choice(value=str(d), name=d.name) for d in session_dirs]

        # Ask user to select a session
        selected_session_path = inquirer.select(
            message=f"Select a Session from {self.selected_sansad.name}:",
            choices=session_choices,
        ).execute()

        self.selected_session = Path(selected_session_path)

    def select_ministries(self):
        """Select one or more ministries from the given session."""
        # Check if ministries directory exists
        ministries_dir = self.selected_session / "ministries"

        if not ministries_dir.exists() or not ministries_dir.is_dir():
            print(f"\nMinistries directory not found in {self.selected_session.name}.")
            inquirer.text(message="Press Enter to continue...").execute()
            return

        # Get ministries and sort them alphabetically by name
        ministry_dirs = sorted([d for d in ministries_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

        if not ministry_dirs:
            print(f"\nNo ministry directories found in {ministries_dir}.")
            inquirer.text(message="Press Enter to continue...").execute()
            return

        # Create choices for the ministry selection
        ministry_choices = [Choice(value=str(d), name=d.name) for d in ministry_dirs]

        # Ask user to select multiple ministries using checkbox
        selected_ministry_paths = inquirer.checkbox(
            message=f"Select Ministry/Ministries from {self.selected_session.name}:",
            choices=ministry_choices,
            instruction="(Use space to select, enter to confirm)",
            validate=lambda result: len(result) >= 1 or "Please select at least one ministry",
        ).execute()

        # Convert string paths to Path objects
        self.selected_ministries = [Path(path) for path in selected_ministry_paths]

    def count_documents(self):
        """Count documents across all selected ministries."""
        # Count documents across all ministries using the shared function
        self.all_ministry_docs = find_all_document_paths(self.selected_ministries)

        for ministry in self.selected_ministries:
            ministry_docs = find_document_paths(ministry)
            self.ministry_doc_counts[ministry.name] = len(ministry_docs)

    def display_summary(self):
        """Display a summary of the selected items with document counts."""
        print("\nSelected:")
        print(f"  Sansad: {self.selected_sansad.name}")
        print(f"  Session: {self.selected_session.name}")
        print(f"  Ministries: {', '.join(ministry.name for ministry in self.selected_ministries)}")
        print(f"  Total ministries selected: {len(self.selected_ministries)}")
        print(f"  Total documents to process: {len(self.all_ministry_docs)}")

        # Show document count breakdown if there are multiple ministries
        if len(self.selected_ministries) > 1:
            print("\nDocuments per ministry:")
            for ministry_name, doc_count in self.ministry_doc_counts.items():
                print(f"  {ministry_name}: {doc_count} document(s)")


def get_selection_workflow():
    """
    Common selection workflow for PDF operations.
    Returns the selected sansad, session, ministries, and document paths.

    Returns:
        tuple: (selected_sansad, selected_session, selected_ministries)
        Any of these can be None if selection was cancelled
    """
    workflow = SelectionWorkflow()
    return workflow.run()


class FixTablesWorkflow(BaseWorkflow):
    """Class to handle the workflow for fixing tables in PDFs."""

    def __init__(self):
        """Initialize the workflow with empty state."""
        super().__init__()
        self.documents_with_tables = []
        self.stats = None
        self.ministry_table_stats = None
        self.total_docs = 0

    def run(self):
        """Main entry point to run the workflow."""
        # Get selections using common workflow
        self.selected_sansad, _, self.selected_ministries = get_selection_workflow()

        if not self.selected_sansad:  # Selection was cancelled
            return

        self.display_header()
        self.find_documents_with_tables()
        self.process_documents()

    def display_header(self):
        """Display the header for the fix tables workflow."""
        print("\nFix Tables Workflow")
        print("------------------")
        print("Searching for documents with tables...")

    def find_documents_with_tables(self):
        """Find and process documents with tables."""
        # Find documents with tables using the shared function
        self.documents_with_tables = find_documents_with_tables(self.selected_ministries)

        if not self.documents_with_tables:
            print("No documents with tables found in the selected ministries.")
            return False

        self.stats = self.display_table_statistics()
        self.ministry_table_stats = self.stats["by_ministry"]
        self.total_docs = self.stats["totals"]["documents"]
        return True

    def display_table_statistics(self):
        """Display statistics about tables found in documents.

        Returns:
            dict: Statistics about tables including ministry stats and totals
        """
        # Calculate statistics using the shared function
        stats = calculate_table_statistics(self.documents_with_tables)
        ministry_table_stats = stats["by_ministry"]
        total_docs = stats["totals"]["documents"]
        total_tables = stats["totals"]["tables"]
        total_pages = stats["totals"]["pages"]

        # Create table data for display
        print(f"\nSummary of Tables ({stats['totals']['ministries']} ministries):")

        # Define headers and prepare rows
        headers = ["Ministry", "Documents", "Tables", "Pages"]
        rows = []
        for ministry, ministry_stats in ministry_table_stats.items():
            rows.append(
                [ministry, ministry_stats["doc_count"], ministry_stats["table_count"], ministry_stats["page_count"]]
            )

        # Define footer with totals
        footer = ["TOTAL", total_docs, total_tables, total_pages]

        # Print the table using our generic function
        print_table(headers, rows, footer)

        return stats

    def inquire_processing_mode_and_filter_documents(self):
        """Let user select how to process documents with tables.

        Returns:
            list: Selected documents to process
        """
        # Let user select document processing mode
        processing_mode = inquirer.select(
            message="Select processing mode:",
            choices=[
                Choice(value="all", name="Process all documents"),
                Choice(value="ministry", name="Select ministry first"),
                Choice(value="document", name="Select specific document"),
            ],
        ).execute()

        documents_to_process = []

        if processing_mode == "all":
            documents_to_process = self.documents_with_tables

        elif processing_mode == "ministry":
            # Let user select ministry
            ministry_choices = [Choice(value=m, name=m) for m in self.ministry_table_stats.keys()]
            selected_ministry = inquirer.select(
                message="Select ministry to process:",
                choices=ministry_choices,
            ).execute()

            # Filter documents for selected ministry
            documents_to_process = [doc for doc in self.documents_with_tables if doc["ministry"] == selected_ministry]

            print(f"\nSelected {len(documents_to_process)} documents from ministry: {selected_ministry}")

        elif processing_mode == "document":
            # Create a list of documents with identifiers
            doc_choices = []
            for i, doc in enumerate(self.documents_with_tables):
                doc_path = Path(doc["path"])
                doc_choices.append(
                    Choice(
                        value=i,
                        name=f"{doc['ministry']} - {doc_path.name} ({doc['num_tables']} tables)",
                    )
                )

            # Let user select document
            selected_doc_idx = inquirer.select(
                message="Select document to process:",
                choices=doc_choices,
            ).execute()

            documents_to_process = [self.documents_with_tables[selected_doc_idx]]

        return documents_to_process

    def display_document_details(self):
        """Display detailed information about documents with tables."""
        print(f"\nFound {len(self.documents_with_tables)} documents with tables:")
        for i, doc in enumerate(self.documents_with_tables, 1):
            print(f"\n{i}. Ministry: {doc['ministry']}")
            print(f"   Document: {Path(doc['path']).name}")
            print(f"   Tables: {doc['num_tables']}")
            print(f"   Pages with tables: {', '.join(map(str, doc['table_pages']))}")

    def process_documents(self):
        """Process the found documents based on user choices."""
        if not self.documents_with_tables:
            return

        # Ask user if they want to process documents with tables
        process_docs = inquirer.confirm(message="Do you want to process documents with tables?", default=True).execute()

        if process_docs:
            documents_to_process = self.inquire_processing_mode_and_filter_documents()
            self.process_documents_with_tables(documents_to_process)
        # User doesn't want to process, just show details if requested
        elif inquirer.confirm(
            message=f"Do you want to see details of all {self.total_docs} documents with tables?", default=False
        ).execute():
            self.display_document_details()

        # Wait for user input before returning to menu
        inquirer.text(message="Press Enter to continue...").execute()

    def process_documents_with_tables(self, documents):
        """
        Process documents with tables by splitting PDFs at page level and extracting text.

        Args:
            documents: List of document dictionaries with table information
        """
        total_documents = len(documents)
        data_root = get_loksabha_data_root()

        print(f"\nProcessing {total_documents} documents with tables...")

        # If processing multiple documents, ask for batch confirmation
        if total_documents > 1:
            batch_process = inquirer.confirm(
                message=f"Do you want to process all {total_documents} documents without individual confirmation?",
                default=True,
            ).execute()
        else:
            batch_process = False

        # Initialize the PDF extractor

        for i, doc in enumerate(documents, 1):
            doc_path_str = doc["path"]
            table_pages = doc["table_pages"]

            # Convert relative path to absolute path using data root
            doc_path = Path(doc_path_str)
            if not doc_path.is_absolute():
                doc_path = data_root / doc_path

            pdf_extractor = PDFExtractionOrchestrator(doc_path)

            print(f"\n[{i}/{total_documents}] Processing document: {doc_path.name}")
            print(f"  Pages with tables: {', '.join(map(str, table_pages))}")

            # Only ask for confirmation if not in batch mode
            proceed = True
            if not batch_process:
                proceed = inquirer.confirm(message="Process this document?", default=True).execute()

            if proceed:
                try:
                    # Make sure PDF exists
                    if not doc_path.exists():
                        raise FileNotFoundError(f"PDF file not found at: {doc_path}")

                    # Call PDF extractor to process the pages
                    print("  Splitting PDF and processing pages with tables...")
                    pdf_extractor.extract_and_save_content(str(doc_path), table_pages)

                    print("  ✓ Successfully processed pages with tables")
                except Exception as e:
                    print(f"  ✗ Error processing document: {str(e)}")
            else:
                print("  Skipped document")

        print("\nDocument processing complete!")


def fix_tables_workflow():
    """Entry point for the fix tables workflow."""
    workflow = FixTablesWorkflow()
    workflow.run()
