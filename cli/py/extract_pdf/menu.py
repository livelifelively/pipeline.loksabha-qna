import asyncio
import sys
import time
from pathlib import Path
from typing import List

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

# from cli.py.utils.paths import find_document_paths

# Add parent directory to path to import from other modules
sys.path.append(str(Path(__file__).parents[4]))

# Import but don't call directly - we'll handle async separately
from apps.py.documents.pdf_splitter import split_pdf_pages_from_file
from apps.py.parliament_questions.document_processing import (
    calculate_table_statistics,
    find_all_document_paths,
    find_document_paths,
    find_documents_with_tables,
    save_ministry_extraction_results,
)
from apps.py.parliament_questions.pdf_extraction import PDFExtractor
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


def confirm_extraction_process(all_document_paths, selected_ministries):
    """Get confirmation from the user to proceed with extraction."""
    print(
        f"\nFound {len(all_document_paths)} document paths with PDF files across {len(selected_ministries)} ministries."
    )
    return inquirer.confirm(
        message=f"Do you want to extract text from these {len(all_document_paths)} documents?", default=True
    ).execute()


def get_selection_workflow():
    """
    Common selection workflow for PDF operations.
    Returns the selected sansad, session, ministries, and document paths.

    Returns:
        tuple: (selected_sansad, selected_session, selected_ministries, all_ministry_docs, ministry_doc_counts)
        Any of these can be None if selection was cancelled
    """
    # Get the data root directory
    data_root = get_loksabha_data_root()

    # Select sansad
    selected_sansad = select_sansad(data_root)
    if not selected_sansad:
        return None, None, None, None, None

    # Select session
    selected_session = select_session(selected_sansad)
    if not selected_session:
        return None, None, None, None, None

    # Select ministries (now returns a list)
    selected_ministries = select_ministry(selected_session)
    if not selected_ministries:
        return None, None, None, None, None

    # Count documents across all ministries using the shared function
    all_ministry_docs = find_all_document_paths(selected_ministries)
    ministry_doc_counts = {}

    for ministry in selected_ministries:
        ministry_docs = find_document_paths(ministry)
        ministry_doc_counts[ministry.name] = len(ministry_docs)

    # Display selection summary with document counts
    display_selection_summary(
        selected_sansad, selected_session, selected_ministries, ministry_doc_counts, len(all_ministry_docs)
    )

    return selected_sansad, selected_session, selected_ministries


def extract_pdf_workflow():
    """Main workflow for PDF extraction."""
    # Get selections using common workflow
    selected_sansad, selected_session, selected_ministries = get_selection_workflow()

    if not selected_sansad:  # Selection was cancelled
        return

    # Use marker as the default extractor type
    extractor_type = "marker"

    # Process each ministry separately
    overall_results = {
        "total_ministries": len(selected_ministries),
        "total_processed": 0,
        "total_failed": 0,
        "ministry_results": [],
    }

    for ministry in selected_ministries:
        ministry_result = process_ministry(ministry, extractor_type, selected_session)
        if ministry_result:
            overall_results["total_processed"] += ministry_result["total_processed"]
            overall_results["total_failed"] += ministry_result["total_failed"]
            overall_results["ministry_results"].append({"ministry_name": ministry.name, "results": ministry_result})

    # Display overall summary
    print("\nOverall Extraction Results:")
    print(
        f"Total ministries processed: {len(overall_results['ministry_results'])}/{overall_results['total_ministries']}"
    )
    print(f"Total documents processed: {overall_results['total_processed']}")
    print(f"Total documents failed: {overall_results['total_failed']}")

    inquirer.text(message="Press Enter to continue...").execute()


def process_ministry(ministry, extractor_type, selected_session):
    """Process a single ministry's documents."""
    print(f"\n\nProcessing Ministry: {ministry.name}")
    print("=" * 50)

    # Find document paths for this ministry using the shared function
    document_paths = find_document_paths(ministry)

    if not document_paths:
        print(f"No PDF documents found in ministry: {ministry.name}")
        return None

    # Display information and countdown timer
    print(f"Found {len(document_paths)} document paths with PDF files in {ministry.name}.")
    print("Starting extraction in 10 seconds...")

    # Countdown timer with option to cancel
    for i in range(10, 0, -1):
        print(f"Starting in {i} seconds... (Press Ctrl+C to cancel)", end="\r")
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nExtraction cancelled for ministry: {ministry.name}")
            return None

    print("\nStarting extraction for ministry: {ministry.name}".ljust(60))

    # Execute the extraction asynchronously
    try:
        print(f"Starting extraction of {len(document_paths)} documents...")

        # Run the extraction
        results = asyncio.run(extract_documents(document_paths, extractor_type))

        # Display results for this ministry
        print(f"\nExtraction Complete for {ministry.name}!")
        print(f"Status: {results['status']}")
        print(f"Documents processed: {results['total_processed']}")
        print(f"Documents failed: {results['total_failed']}")

        # Save results for this ministry automatically using the shared function
        save_ministry_extraction_results(results, selected_session, ministry.name)

        return results

    except Exception as e:
        print(f"\nError during extraction process for {ministry.name}: {str(e)}")
        return None


def select_sansad(data_root):
    """Select a sansad from the data root directory."""
    # Get a list of all sansad directories and sort them
    sansad_dirs = sorted([d for d in data_root.iterdir() if d.is_dir()], key=lambda x: x.name)

    if not sansad_dirs:
        print("\nNo sansad directories found in data root.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None

    # Create choices for the sansad selection
    sansad_choices = [Choice(value=str(d), name=d.name) for d in sansad_dirs]

    # Ask user to select a sansad
    selected_sansad_path = inquirer.select(
        message="Select a Sansad/Loksabha:",
        choices=sansad_choices,
    ).execute()

    return Path(selected_sansad_path)


def select_session(sansad_path):
    """Select a session from the given sansad."""
    # Get all session directories for the selected sansad and sort them
    session_dirs = sorted([d for d in sansad_path.iterdir() if d.is_dir()], key=lambda x: x.name)

    if not session_dirs:
        print(f"\nNo session directories found in {sansad_path.name}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None

    # Create choices for the session selection
    session_choices = [Choice(value=str(d), name=d.name) for d in session_dirs]

    # Ask user to select a session
    selected_session_path = inquirer.select(
        message=f"Select a Session from {sansad_path.name}:",
        choices=session_choices,
    ).execute()

    return Path(selected_session_path)


def select_ministry(session_path):
    """Select one or more ministries from the given session."""
    # Check if ministries directory exists
    ministries_dir = session_path / "ministries"

    if not ministries_dir.exists() or not ministries_dir.is_dir():
        print(f"\nMinistries directory not found in {session_path.name}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None

    # Get ministries and sort them alphabetically by name
    ministry_dirs = sorted([d for d in ministries_dir.iterdir() if d.is_dir()], key=lambda x: x.name)

    if not ministry_dirs:
        print(f"\nNo ministry directories found in {ministries_dir}.")
        inquirer.text(message="Press Enter to continue...").execute()
        return None

    # Create choices for the ministry selection
    ministry_choices = [Choice(value=str(d), name=d.name) for d in ministry_dirs]

    # Ask user to select multiple ministries using checkbox
    selected_ministry_paths = inquirer.checkbox(
        message=f"Select Ministry/Ministries from {session_path.name}:",
        choices=ministry_choices,
        instruction="(Use space to select, enter to confirm)",
        validate=lambda result: len(result) >= 1 or "Please select at least one ministry",
    ).execute()

    # Convert string paths to Path objects
    selected_ministries = [Path(path) for path in selected_ministry_paths]

    return selected_ministries


def display_selection_summary(sansad, session, ministries, ministry_doc_counts, total_docs):
    """Display a summary of the selected items with document counts."""
    print("\nSelected:")
    print(f"  Sansad: {sansad.name}")
    print(f"  Session: {session.name}")
    print(f"  Ministries: {', '.join(ministry.name for ministry in ministries)}")
    print(f"  Total ministries selected: {len(ministries)}")
    print(f"  Total documents to process: {total_docs}")

    # Show document count breakdown if there are multiple ministries
    if len(ministries) > 1:
        print("\nDocuments per ministry:")
        for ministry_name, doc_count in ministry_doc_counts.items():
            print(f"  {ministry_name}: {doc_count} document(s)")


# Add new extraction function for CLI
async def extract_documents(document_paths: List[Path], extractor_type: str = "marker"):
    """
    Process PDFs for all documents selected in the CLI.

    Args:
        document_paths: List of paths to document directories
        extractor_type: Type of PDF extractor to use

    Returns:
        Dict containing extraction results
    """
    total_documents = len(document_paths)
    processed_documents = []
    failed_extractions = []

    print(f"\nStarting extraction of {total_documents} documents...")

    # Create PDFExtractor instance
    extractor = PDFExtractor(extractor_type=extractor_type)

    for i, doc_dir in enumerate(document_paths):
        try:
            # Find PDF file in the document directory
            pdf_files = list(doc_dir.glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError(f"No PDF file found in directory: {doc_dir}")

            pdf_path = pdf_files[0]  # Take the first PDF if multiple exist

            # Show progress
            print(f"Processing [{i + 1}/{total_documents}]: {pdf_path.name}")

            # Extract contents using the extractor instance
            result = await extractor.extract_contents(pdf_path)
            processed_documents.append({"path": str(pdf_path), "result": result})

            print(f"  ✓ Extraction successful: {pdf_path.name}")

        except Exception as e:
            failed_extractions.append({"path": str(doc_dir), "error": str(e)})
            print(f"  ✗ Extraction failed: {doc_dir.name} - {str(e)}")

    status = "SUCCESS" if not failed_extractions else "PARTIAL"

    result_summary = {
        "status": status,
        "total_processed": len(processed_documents),
        "total_failed": len(failed_extractions),
        "extracted_documents": processed_documents,
        "failed_extractions": failed_extractions,
    }

    return result_summary


def fix_tables_workflow():
    """Workflow for fixing tables in PDFs."""
    # Get selections using common workflow
    selected_sansad, selected_ministries = get_selection_workflow()

    if not selected_sansad:  # Selection was cancelled
        return

    print("\nFix Tables Workflow")
    print("------------------")
    print("Searching for documents with tables...")

    # Find documents with tables using the shared function
    documents_with_tables = find_documents_with_tables(selected_ministries)

    if not documents_with_tables:
        print("No documents with tables found in the selected ministries.")
    else:
        # Calculate statistics using the shared function
        stats = calculate_table_statistics(documents_with_tables)
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

        # Ask user if they want to process documents with tables
        process_docs = inquirer.confirm(message="Do you want to process documents with tables?", default=True).execute()

        if process_docs:
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
                documents_to_process = documents_with_tables

            elif processing_mode == "ministry":
                # Let user select ministry
                ministry_choices = [Choice(value=m, name=m) for m in ministry_table_stats.keys()]
                selected_ministry = inquirer.select(
                    message="Select ministry to process:",
                    choices=ministry_choices,
                ).execute()

                # Filter documents for selected ministry
                documents_to_process = [doc for doc in documents_with_tables if doc["ministry"] == selected_ministry]

                print(f"\nSelected {len(documents_to_process)} documents from ministry: {selected_ministry}")

            elif processing_mode == "document":
                # Create a list of documents with identifiers
                doc_choices = []
                for i, doc in enumerate(documents_with_tables):
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

                documents_to_process = [documents_with_tables[selected_doc_idx]]

            # Process selected documents
            process_documents_with_tables(documents_to_process)

        # User doesn't want to process, just show details if requested
        elif inquirer.confirm(
            message=f"Do you want to see details of all {total_docs} documents with tables?", default=False
        ).execute():
            print(f"\nFound {len(documents_with_tables)} documents with tables:")
            for i, doc in enumerate(documents_with_tables, 1):
                print(f"\n{i}. Ministry: {doc['ministry']}")
                print(f"   Document: {Path(doc['path']).name}")
                print(f"   Tables: {doc['num_tables']}")
                print(f"   Pages with tables: {', '.join(map(str, doc['table_pages']))}")

    # Wait for user input before returning to menu
    inquirer.text(message="Press Enter to continue...").execute()


def process_documents_with_tables(documents):
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

    for i, doc in enumerate(documents, 1):
        doc_path_str = doc["path"]
        table_pages = doc["table_pages"]

        # Convert relative path to absolute path using data root
        doc_path = Path(doc_path_str)
        if not doc_path.is_absolute():
            doc_path = data_root / doc_path

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

                # Define output folder in the document directory
                output_folder = doc_path.parent / "pages"

                # Call PDF splitter function with absolute path
                print("  Splitting PDF and processing pages with tables...")
                split_pdf_pages_from_file(str(doc_path), table_pages, str(output_folder))

                print("  ✓ Successfully processed pages with tables")
            except Exception as e:
                print(f"  ✗ Error processing document: {str(e)}")
        else:
            print("  Skipped document")

    print("\nDocument processing complete!")
