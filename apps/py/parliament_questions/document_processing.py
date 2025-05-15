import json
from pathlib import Path

from apps.py.documents.pdf_splitter import split_pdf_pages_from_file
from apps.py.utils.project_root import get_loksabha_data_root


def find_documents_with_tables(ministries):
    """
    Find documents with tables across all selected ministries.

    Args:
        ministries: List of ministry paths

    Returns:
        List of dictionaries with document paths and table page information
    """
    from apps.py.utils.project_root import get_loksabha_data_root

    documents_with_tables = []
    data_root = get_loksabha_data_root()

    for ministry in ministries:
        results_file = ministry / "extraction_results.json"

        if not results_file.exists():
            print(f"No extraction results found for ministry: {ministry.name}")
            continue

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                results = json.load(f)

            for doc in results.get("extracted_documents", []):
                doc_path = doc.get("path")

                # Convert to relative path if it's absolute
                if doc_path:
                    doc_path_obj = Path(doc_path)
                    if doc_path_obj.is_absolute():
                        try:
                            # Try to make the path relative to data root
                            rel_path = doc_path_obj.relative_to(data_root)
                            doc_path = str(rel_path)
                        except ValueError:
                            # Keep as is if not under data root
                            pass

                result = doc.get("result", {})

                # Check for tables in the extraction steps
                for step in result.get("steps", []):
                    if step.get("step") == "pdf_extraction" and step.get("status") == "success":
                        data = step.get("data", {})
                        has_tables = data.get("has_tables", False)

                        if has_tables:
                            # Get table information
                            tables_data = data.get("tables_data", {})
                            tables_summary = tables_data.get("tables_summary", [])

                            # Collect page numbers with tables
                            table_pages = []
                            for table in tables_summary:
                                page_num = table.get("page")
                                if page_num and page_num not in table_pages:
                                    table_pages.append(page_num)

                            documents_with_tables.append(
                                {
                                    "path": doc_path,
                                    "ministry": ministry.name,
                                    "table_pages": sorted(table_pages),
                                    "num_tables": data.get("num_tables", 0),
                                }
                            )

        except Exception as e:
            print(f"Error processing results for ministry {ministry.name}: {str(e)}")

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


def process_documents_with_tables(documents):
    """
    Process documents with tables by splitting PDFs at page level and extracting text.

    Args:
        documents: List of document dictionaries with table information
    """
    total_documents = len(documents)
    data_root = get_loksabha_data_root()

    print(f"\nProcessing {total_documents} documents with tables...")

    for i, doc in enumerate(documents, 1):
        doc_path_str = doc["path"]
        table_pages = doc["table_pages"]

        # Convert relative path to absolute path using data root if needed
        doc_path = Path(doc_path_str)
        if not doc_path.is_absolute():
            doc_path = data_root / doc_path

        print(f"\n[{i}/{total_documents}] Processing document: {doc_path.name}")
        print(f"  Pages with tables: {', '.join(map(str, table_pages))}")

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

    print("\nDocument processing complete!")


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


def save_ministry_extraction_results(results, session_path, ministry_name, filename="extraction_results.json"):
    """
    Save extraction results for a ministry to a file.

    Args:
        results: Extraction results to save
        session_path: Path to the session directory
        ministry_name: Name of the ministry
        filename: Name of the output file (default: extraction_results.json)

    Returns:
        Path to the saved file
    """
    try:
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


def save_extraction_results_summary(results, session_path, ministries, add_timestamp=True):
    """
    Save extraction results summary to a file.

    Args:
        results: Extraction results to save
        session_path: Path to the session directory
        ministries: List of ministries or ministry names
        add_timestamp: Whether to add a timestamp to the filename (default: True)

    Returns:
        Path to the saved file
    """
    try:
        # Create filename with ministry information
        if isinstance(ministries, list) and len(ministries) > 0:
            # Extract ministry names if we have Path objects
            ministry_names = []
            for ministry in ministries:
                if hasattr(ministry, "name"):
                    ministry_names.append(ministry.name)
                else:
                    ministry_names.append(str(ministry))

            if len(ministry_names) == 1:
                ministry_name_for_file = ministry_names[0]
            else:
                ministry_name_for_file = f"{ministry_names[0]}_and_{len(ministry_names) - 1}_more"
        else:
            ministry_name_for_file = "all_ministries"

        # Add timestamp if requested
        if add_timestamp:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_results_{ministry_name_for_file}_{timestamp}.json"
        else:
            filename = f"extraction_results_{ministry_name_for_file}.json"

        # Save in the session directory
        results_file = session_path / filename

        # Ensure the directory exists
        results_file.parent.mkdir(parents=True, exist_ok=True)

        # Save the results
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {results_file}")
        return str(results_file)
    except Exception as e:
        print(f"Error saving extraction results summary: {str(e)}")
        return None
