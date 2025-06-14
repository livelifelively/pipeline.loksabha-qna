import json
from pathlib import Path

from apps.py.utils.project_root import get_loksabha_data_root


def find_documents_with_tables(ministries):
    """
    Find documents with tables across all selected ministries.

    Args:
        ministries: List of ministry paths

    Returns:
        List of dictionaries with document paths and table page information
    """

    documents_with_tables = []
    data_root = get_loksabha_data_root()

    for ministry in ministries:
        try:
            # Find all question directories in the ministry
            question_dirs = [d for d in ministry.iterdir() if d.is_dir()]

            for question_dir in question_dirs:
                progress_file = question_dir / "question.progress.json"

                if not progress_file.exists():
                    continue

                try:
                    with open(progress_file, "r", encoding="utf-8") as f:
                        progress_data = json.load(f)

                    # Check if LOCAL_EXTRACTION state exists and was successful
                    local_extraction = progress_data.get("states", {}).get("LOCAL_EXTRACTION", {})
                    if local_extraction.get("status") != "SUCCESS":
                        continue

                    extraction_data = local_extraction.get("data", {})
                    has_tables = extraction_data.get("has_tables", False)
                    total_tables = extraction_data.get("total_tables", 0)

                    if has_tables:
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

                        # Get the document path from INITIALIZED state
                        initialized_data = progress_data.get("states", {}).get("INITIALIZED", {}).get("data", {})
                        doc_path = initialized_data.get("questions_file_path_local")

                        if doc_path:
                            # Convert to relative path if it's absolute
                            doc_path_obj = Path(doc_path)
                            if doc_path_obj.is_absolute():
                                try:
                                    rel_path = doc_path_obj.relative_to(data_root)
                                    doc_path = str(rel_path)
                                except ValueError:
                                    pass

                            documents_with_tables.append(
                                {
                                    "path": doc_path,
                                    "ministry": ministry.name,
                                    "table_pages": sorted(table_pages),
                                    "num_tables": total_tables,
                                    "potential_multi_page_ranges": potential_ranges,
                                    "has_tables": has_tables,
                                    "total_tables": total_tables,
                                }
                            )

                except Exception as e:
                    print(f"Error processing question progress file {progress_file}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error processing ministry {ministry.name}: {str(e)}")

    return documents_with_tables


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
