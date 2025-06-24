import json
import logging
from pathlib import Path

from apps.py.documents.extractors.orchestrator import PDFExtractionOrchestrator
from apps.py.documents.utils.progress_handler import DocumentProgressHandler, ProgressHandler
from apps.py.types import ProcessingState, ProcessingStatus
from apps.py.utils.project_root import get_loksabha_data_root

logger = logging.getLogger(__name__)


def get_status_from_state_data(state_data):
    """
    Extract status from state data, handling both dictionary and typed object formats.

    Args:
        state_data: State data object or dictionary

    Returns:
        str: Status value or None if not found
    """
    if not state_data:
        return None

    # Handle typed object with status attribute
    if hasattr(state_data, "status"):
        status = state_data.status
        return status.value if hasattr(status, "value") else str(status)

    # Handle dictionary with status key
    elif isinstance(state_data, dict) and "status" in state_data:
        return state_data["status"]

    return None


def validate_document_readiness(question_dir):
    """
    Validate that document is ready for LLM_EXTRACTION using progress handler.

    Returns:
        tuple: (handler, initialized_data, local_extraction_data) if valid, (None, None, None) if invalid
    """

    try:
        handler = DocumentProgressHandler(question_dir)

        # Check if document can transition to LLM_EXTRACTION
        progress = handler.read_progress_file()
        if not progress.can_transition_to(ProcessingState.LLM_EXTRACTION):
            return None, None, None

        # Get initialized data (could be typed object or dictionary)
        initialized_state_data = handler.get_initialized_data()
        initialized_status = get_status_from_state_data(initialized_state_data)
        if not initialized_state_data or initialized_status != ProcessingStatus.SUCCESS.value:
            return None, None, None

        # Get local extraction data (could be typed object or dictionary)
        local_extraction_state_data = handler.get_local_extraction_data()
        local_extraction_status = get_status_from_state_data(local_extraction_state_data)
        if not local_extraction_state_data or local_extraction_status != ProcessingStatus.SUCCESS.value:
            return None, None, None

        return handler, initialized_state_data, local_extraction_state_data

    except Exception as e:
        # Log the error with context about which document failed
        logger.error(f"Error validating document readiness for {question_dir}: {str(e)}", exc_info=True)
        return None, None, None


def extract_table_information(local_extraction_data):
    """
    Extract table pages and summary information from local extraction data.
    Handles both typed objects and dictionary formats.

    Returns:
        tuple: (table_pages, potential_ranges) or (None, None) if no tables
    """
    # Extract data from either typed object or dictionary
    # Check for dictionary first to avoid hasattr() issues
    if isinstance(local_extraction_data, dict):
        if "data" in local_extraction_data:
            # Dictionary format with nested "data" key
            extraction_data = local_extraction_data["data"]
        else:
            # Dictionary format where the dict itself is the data
            extraction_data = local_extraction_data
    elif hasattr(local_extraction_data, "data"):
        # Typed object with data attribute
        extraction_data = local_extraction_data.data
    else:
        return None, None

    has_tables = extraction_data.get("has_tables", False)
    if not has_tables:
        return None, None

    # Get table information from pages
    pages = extraction_data.get("pages", {})
    table_pages = []
    tables_summary = []

    # Convert pages data to tables_summary format for potential ranges
    for page_num, page_data in pages.items():
        if page_data.get("has_tables", False):
            page_num_int = int(page_num)
            table_pages.append(page_num_int)
            # Add to tables_summary for potential ranges calculation
            tables_summary.append({"page": page_num_int})

    # Find potential multi-page tables
    potential_ranges = find_potential_continuous_table_pages(tables_summary)

    return sorted(table_pages), potential_ranges


def get_document_path_from_state(initialized_state_data):
    """
    Get and normalize the document path from initialized state data.
    Handles both typed objects and dictionary formats.

    Returns:
        str: Relative path to document or None if not found
    """
    data_root = get_loksabha_data_root()

    # Extract data from either typed object or dictionary
    # Check for dictionary first to avoid hasattr() issues
    if isinstance(initialized_state_data, dict):
        if "data" in initialized_state_data:
            # Dictionary format with nested "data" key
            initialized_data = initialized_state_data["data"]
        else:
            # Dictionary format where the dict itself is the data
            initialized_data = initialized_state_data
    elif hasattr(initialized_state_data, "data"):
        # Typed object with data attribute
        initialized_data = initialized_state_data.data
    else:
        return None

    doc_path = initialized_data.get("questions_file_path_local")

    if not doc_path:
        return None

    # Convert to relative path if it's absolute
    doc_path_obj = Path(doc_path)
    if doc_path_obj.is_absolute():
        try:
            rel_path = doc_path_obj.relative_to(data_root)
            return str(rel_path)
        except ValueError:
            pass

    return doc_path


def create_document_entry(doc_path, ministry_name, table_pages, total_tables, potential_ranges, has_tables):
    """
    Create a document entry for the results list.

    Returns:
        dict: Document information dictionary
    """
    return {
        "path": doc_path,
        "ministry": ministry_name,
        "table_pages": table_pages,
        "num_tables": total_tables,
        "potential_multi_page_ranges": potential_ranges,
        "has_tables": has_tables,
        "total_tables": total_tables,
    }


def validate_single_document_for_llm_extraction(document_path):
    """
    Validate that a single document is ready for LLM extraction.
    Efficient single-document validation without ministry-wide scanning.

    Args:
        document_path: Path to the document directory

    Returns:
        dict: Document information with table_pages in same format as find_documents_ready_for_llm_extraction

    Raises:
        ValueError: If document is not ready for LLM_EXTRACTION
        FileNotFoundError: If document doesn't exist
    """
    data_root = get_loksabha_data_root()

    # Convert to absolute path and validate existence
    doc_path = data_root / document_path
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found at path: {document_path}")

    # Extract ministry name from path
    ministry_name = doc_path.parent.name

    # Validate document readiness using shared helper
    handler, initialized_state_data, local_extraction_state_data = validate_document_readiness(doc_path)
    if not handler or not initialized_state_data or not local_extraction_state_data:
        raise ValueError(f"Document not ready for LLM extraction: {document_path}")

    # Extract table information using shared helper
    table_pages, potential_ranges = extract_table_information(local_extraction_state_data)
    if not table_pages:
        raise ValueError(f"Document has no tables for LLM extraction: {document_path}")

    # Get document path using shared helper
    doc_path_str = get_document_path_from_state(initialized_state_data)
    if not doc_path_str:
        raise ValueError(f"Cannot determine document path from state: {document_path}")

    # Extract additional info for document entry
    if isinstance(local_extraction_state_data, dict):
        if "data" in local_extraction_state_data:
            extraction_data = local_extraction_state_data["data"]
        else:
            extraction_data = local_extraction_state_data
    elif hasattr(local_extraction_state_data, "data"):
        extraction_data = local_extraction_state_data.data
    else:
        extraction_data = {}

    has_tables = extraction_data.get("has_tables", False)
    total_tables = extraction_data.get("total_tables", 0)

    # Create document entry using shared helper
    return create_document_entry(doc_path_str, ministry_name, table_pages, total_tables, potential_ranges, has_tables)


def find_documents_ready_for_llm_extraction(ministries):
    """
    Find documents that are ready for LLM_EXTRACTION transition.
    Uses DocumentProgressHandler for proper state management and validation.

    Args:
        ministries: List of ministry paths

    Returns:
        List of dictionaries with document paths and table page information
    """
    data_root = get_loksabha_data_root()

    def process_question_directory(question_dir, ministry_name):
        """
        Process a single question directory and return document info if ready for LLM extraction.

        Returns:
            dict or None: Document information if valid and ready for LLM extraction, None otherwise
        """
        # Validate document readiness using progress handler
        handler, initialized_state_data, local_extraction_state_data = validate_document_readiness(question_dir)
        if not handler or not initialized_state_data or not local_extraction_state_data:
            return None

        # Extract table information from typed data
        table_pages, potential_ranges = extract_table_information(local_extraction_state_data)
        if not table_pages:
            return None

        # Get document path from typed data
        doc_path = get_document_path_from_state(initialized_state_data)
        if not doc_path:
            return None

        # Create document entry - extract data handling both formats
        if isinstance(local_extraction_state_data, dict):
            if "data" in local_extraction_state_data:
                # Dictionary format with nested "data" key
                extraction_data = local_extraction_state_data["data"]
            else:
                # Dictionary format where the dict itself is the data
                extraction_data = local_extraction_state_data
        elif hasattr(local_extraction_state_data, "data"):
            extraction_data = local_extraction_state_data.data
        else:
            extraction_data = {}

        has_tables = extraction_data.get("has_tables", False)
        total_tables = extraction_data.get("total_tables", 0)

        return create_document_entry(doc_path, ministry_name, table_pages, total_tables, potential_ranges, has_tables)

    # Main processing logic
    documents_ready_for_llm_extraction = []

    for ministry in ministries:
        try:
            # Find all question directories in the ministry
            question_dirs = [d for d in ministry.iterdir() if d.is_dir()]

            for question_dir in question_dirs:
                document_info = process_question_directory(question_dir, ministry.name)
                if document_info:
                    documents_ready_for_llm_extraction.append(document_info)

        except Exception as e:
            print(f"Error processing ministry {ministry.name}: {str(e)}")

    # Sort documents by filename for consistent ordering
    documents_ready_for_llm_extraction.sort(key=lambda doc: Path(doc["path"]).name)

    return documents_ready_for_llm_extraction


def calculate_table_statistics(documents_with_tables):
    """
    Calculate statistics about tables in documents.

    Args:
        documents_with_tables: List of documents with table information

    Returns:
        Dictionary with statistics by ministry and overall totals
    """
    ministry_table_stats = {}
    total_docs = 0
    total_tables = 0
    total_pages = 0

    for doc in documents_with_tables:
        ministry_name = doc["ministry"]
        if ministry_name not in ministry_table_stats:
            ministry_table_stats[ministry_name] = {"doc_count": 0, "table_count": 0, "page_count": 0}
        ministry_table_stats[ministry_name]["doc_count"] += 1
        ministry_table_stats[ministry_name]["table_count"] += doc["num_tables"]
        ministry_table_stats[ministry_name]["page_count"] += len(doc["table_pages"])

        # Update overall totals
        total_docs += 1
        total_tables += doc["num_tables"]
        total_pages += len(doc["table_pages"])

    return {
        "by_ministry": ministry_table_stats,
        "totals": {
            "ministries": len(ministry_table_stats),
            "documents": total_docs,
            "tables": total_tables,
            "pages": total_pages,
        },
    }


def find_document_paths(ministry_path):
    """
    Find all document paths within the ministry directory.

    Args:
        ministry_path: Path to the ministry directory

    Returns:
        List of paths to directories containing PDF files
    """
    try:
        # Each subfolder in the ministry directory may contain a PDF file
        document_dirs = [d for d in ministry_path.iterdir() if d.is_dir()]

        if not document_dirs:
            return []

        # Find directories containing PDF files
        pdf_dirs = []
        for doc_dir in document_dirs:
            pdf_files = list(doc_dir.glob("*.pdf"))
            if pdf_files:
                pdf_dirs.append(doc_dir)

        return pdf_dirs
    except Exception as e:
        print(f"Error finding document paths: {str(e)}")
        return []


def find_documents_needing_extraction(ministry_path):
    """
    Find document paths that need LOCAL_EXTRACTION processing.
    Filters out documents that have already been successfully extracted.

    Args:
        ministry_path: Path to the ministry directory

    Returns:
        List of paths to directories containing PDF files that need extraction
    """
    try:
        # First get all document directories with PDFs
        all_document_dirs = find_document_paths(ministry_path)
        
        if not all_document_dirs:
            return []

        documents_needing_extraction = []
        
        for doc_dir in all_document_dirs:
            if _document_needs_extraction(doc_dir):
                documents_needing_extraction.append(doc_dir)
        
        return documents_needing_extraction
        
    except Exception as e:
        print(f"Error finding documents needing extraction: {str(e)}")
        return []


def _document_needs_extraction(document_dir):
    """
    Check if a document needs LOCAL_EXTRACTION processing.
    
    Args:
        document_dir: Path to the document directory
        
    Returns:
        bool: True if document needs extraction, False if already processed successfully
    """
    try:
        from apps.py.documents.utils.progress_handler import DocumentProgressHandler
        
        # Check if progress file exists
        progress_file = document_dir / "question.progress.json"
        if not progress_file.exists():
            # No progress file means document hasn't been processed yet
            return True
        
        # Use DocumentProgressHandler to check status
        handler = DocumentProgressHandler(document_dir)
        
        # Get current state
        current_state = handler.get_current_state()
        
        # If state is LOCAL_EXTRACTION, check if it was successful
        if current_state == ProcessingState.LOCAL_EXTRACTION:
            local_extraction_data = handler.get_local_extraction_data()
            status = get_status_from_state_data(local_extraction_data)
            
            # If LOCAL_EXTRACTION was successful, skip this document
            if status == ProcessingStatus.SUCCESS.value:
                return False
        
        # For all other cases (no state, different state, or failed LOCAL_EXTRACTION), include document
        return True
        
    except Exception as e:
        # If there's any error reading the progress file, include the document for safety
        # This ensures corrupted progress files don't prevent processing
        print(f"Warning: Error checking extraction status for {document_dir.name}: {str(e)}")
        return True


def find_all_document_paths(ministries):
    """
    Find document paths across all selected ministries.

    Args:
        ministries: List of ministry paths

    Returns:
        List of paths to directories containing PDF files
    """
    all_document_paths = []
    for ministry in ministries:
        ministry_docs = find_document_paths(ministry)
        all_document_paths.extend(ministry_docs)

    return all_document_paths


def save_ministry_extraction_results(results, session_path, ministry_name, filename="ministry.progress.json"):
    """
    Save extraction results for a ministry to a file.

    Args:
        results: Extraction results to save
        session_path: Path to the session directory
        ministry_name: Name of the ministry
        filename: Name of the output file (default: ministry.progress.json)

    Returns:
        Path to the saved file
    """
    try:
        # Convert session_path to Path object if it's a string
        session_path = Path(session_path)

        # Save in the session directory
        results_file = session_path / "ministries" / ministry_name / filename

        # Ensure the directory exists
        results_file.parent.mkdir(parents=True, exist_ok=True)

        # Save the results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {results_file}")
        return str(results_file)
    except Exception as e:
        print(f"Error saving ministry extraction results: {str(e)}")
        return None


def find_potential_continuous_table_pages(tables_summary: list) -> list[tuple[int, int]]:
    """
    Find continuous page ranges that might contain potential multi-page tables.
    Only includes ranges where start and end pages are different.

    Args:
        tables_summary: List of table information dictionaries containing 'page' field

    Returns:
        List of tuples containing (start_page, end_page) for continuous table ranges
        where start_page != end_page, indicating potential multi-page tables
    """
    if not tables_summary:
        return []

    # Sort tables by page number
    sorted_tables = sorted(tables_summary, key=lambda x: x["page"])

    potential_ranges = []
    start_page = sorted_tables[0]["page"]
    prev_page = start_page

    for table in sorted_tables[1:]:
        current_page = table["page"]

        # If pages are not continuous, save the range and start a new one
        if current_page - prev_page > 1:
            # Only add range if start and end pages are different
            if start_page != prev_page:
                potential_ranges.append((start_page, prev_page))
            start_page = current_page

        prev_page = current_page

    # Add the last range only if start and end pages are different
    if start_page != prev_page:
        potential_ranges.append((start_page, prev_page))

    return potential_ranges


def find_documents_with_potential_multi_page_tables(documents_with_tables: list) -> list[dict]:
    """
    Find documents that have tables on continuous pages, potentially indicating multi-page tables.

    Args:
        documents_with_tables: List of documents with their table information

    Returns:
        List of documents that have tables on continuous pages, indicating potential multi-page tables
    """
    documents_with_potential_multi_page_tables = []

    for doc in documents_with_tables:
        tables_data = doc.get("tables_data", {})
        tables_summary = tables_data.get("tables_summary", [])

        # Find continuous page ranges
        potential_ranges = find_potential_continuous_table_pages(tables_summary)

        # If we found any continuous ranges, add the document to our results
        if potential_ranges:
            documents_with_potential_multi_page_tables.append(
                {
                    "path": doc["path"],
                    "ministry": doc["ministry"],
                    "potential_multi_page_table_ranges": potential_ranges,
                    "num_tables": doc["num_tables"],
                    "tables_summary": tables_summary,
                }
            )

    return documents_with_potential_multi_page_tables


def process_single_document_for_llm_extraction(document_path, table_pages):
    """
    Process a single document for LLM extraction using the PDFExtractionOrchestrator.

    This function follows the same logic as process_documents_with_tables:
    - Converts path to absolute
    - Checks if document exists
    - Calls orchestrator with table pages
    - Returns LLM extraction state data

    Args:
        document_path: Path to the document directory (relative or absolute)
        table_pages: List of page numbers that have tables

    Returns:
        StateData: The LLM extraction state data after successful processing

    Raises:
        FileNotFoundError: If document not found
        Exception: If orchestrator processing fails
    """
    # Convert relative path to absolute path using data root (same as CLI)
    data_root = get_loksabha_data_root()
    doc_path = Path(document_path)
    if not doc_path.is_absolute():
        doc_path = data_root / doc_path

    # Make sure document exists (same as CLI)
    if not doc_path.exists():
        raise FileNotFoundError(f"Document not found at: {doc_path}")

    # Call PDF extractor to process the pages (same as CLI)
    pdf_extractor = PDFExtractionOrchestrator()
    pdf_extractor.extract_and_save_content(str(doc_path), table_pages)

    # Get and return the updated state data after processing
    handler = ProgressHandler(doc_path)
    llm_state_data = handler.get_llm_extraction_data()
    if not llm_state_data:
        raise Exception("LLM extraction completed but no state data found")

    return llm_state_data
