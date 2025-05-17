import json
from pathlib import Path
from typing import List, Optional

from PyPDF2 import PdfReader, PdfWriter

from apps.py.utils.gemini_api import extract_tables_from_pdf_page, extract_text_from_pdf_page
from apps.py.utils.project_root import get_loksabha_data_root


def split_pdf_pages(pdf_path: str, output_folder: Optional[str] = None) -> str:
    """
    Splits a PDF file into individual pages and saves them in the specified folder.

    Args:
        pdf_path: Path to the input PDF file
        output_folder: Folder to save individual pages (if None, creates a folder next to PDF)

    Returns:
        Path to the folder containing the split pages
    """
    pdf_path = Path(pdf_path)

    # If no output folder specified, create one next to the PDF
    if output_folder is None:
        output_folder = pdf_path.parent / "pages"

    # Create output folder if it doesn't exist
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Open the PDF file
    pdf = PdfReader(str(pdf_path))
    total_pages = len(pdf.pages)

    print(f"Processing '{pdf_path.name}' ({total_pages} pages)...")

    # Process each page
    for page_num in range(total_pages):
        # Create a writer for this page
        writer = PdfWriter()
        writer.add_page(pdf.pages[page_num])

        # Save to output file
        output_path = output_folder / f"{page_num + 1}.pdf"
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        print(f"  Saved: {output_path.name}")

    print(f"Successfully split {total_pages} pages into folder: '{output_folder}'")
    return str(output_folder)


def split_pdf_pages_with_tables(pdf_path: str, table_pages: List[int], output_folder: Optional[str] = None) -> str:
    """
    Splits specific pages with tables from a PDF file and saves them.

    Args:
        pdf_path: Path to the input PDF file
        table_pages: List of page numbers with tables (1-based indexing)
        output_folder: Folder to save pages (if None, creates a folder next to PDF)

    Returns:
        Path to the folder containing the split pages
    """
    pdf_path = Path(pdf_path)

    # If no output folder specified, create one next to the PDF
    if output_folder is None:
        output_folder = pdf_path.parent / "pages"

    # Create output folder if it doesn't exist
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    # Open the PDF file
    pdf = PdfReader(str(pdf_path))
    total_pages = len(pdf.pages)

    print(f"Processing '{pdf_path.name}' ({total_pages} pages)...")
    print(f"Extracting pages with tables: {', '.join(map(str, table_pages))}")

    # Process only the pages with tables
    for page_number in table_pages:
        # Adjust for 0-based indexing
        page_index = page_number - 1 if page_number > 0 else page_number

        # Check if page index is valid
        if page_index < 0 or page_index >= total_pages:
            print(f"  ⚠ Warning: Page {page_number} is out of range (1-{total_pages})")
            continue

        # Create a writer for this page
        writer = PdfWriter()
        writer.add_page(pdf.pages[page_index])

        # Save the page to the output directory
        output_path = output_folder / f"page_{page_number}.pdf"
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        print(f"  ✓ Saved page {page_number} to {output_path.name}")

    print(f"Successfully saved {len(table_pages)} pages with tables to folder: '{output_folder}'")
    return str(output_folder)


def split_pdf_pages_from_file(pdf_path_str: str, page_numbers: List[int], output_folder: Optional[str] = None) -> str:
    """
    Splits a PDF file into individual pages, processes specific pages, and cleans up.

    Args:
        pdf_path_str: Path to the input PDF file
        page_numbers: List of page numbers to process (1-based indexing)
        output_folder: Folder to save pages (if None, creates a folder next to PDF)

    Returns:
        Path to the folder containing the split pages
    """
    # Split the PDF pages
    pages_folder = split_pdf_pages_with_tables(pdf_path_str, page_numbers, output_folder)

    # Process the pages to extract text
    process_pages(pages_folder, page_numbers)

    return pages_folder


def process_pages(pages_folder: str, page_numbers: List[int]):
    """
    Process split PDF pages to extract text content and tables.

    Args:
        pages_folder: Path to folder containing split PDF pages
        page_numbers: List of page numbers to process

    Returns:
        Dictionary with results for each processed page
    """

    pages_folder = Path(pages_folder)
    data_root = get_loksabha_data_root()

    print(f"Processing pages in folder: {pages_folder}")
    results = {}

    for page_num in page_numbers:
        # First check for specific page number format
        page_file = pages_folder / f"page_{page_num}.pdf"
        if not page_file.exists():
            # Try alternative format
            page_file = pages_folder / f"{page_num}.pdf"
            if not page_file.exists():
                print(f"  ⚠ Warning: Page file for page {page_num} not found")
                continue

        page_results = {"page_number": page_num, "text_extraction": None, "table_extraction": None}

        # Check if extraction has already been done for this page
        existing_extraction = check_existing_extraction(pages_folder, page_num)

        try:
            print(f"  Processing page {page_num} from file: {page_file.name}")

            # 1. Extract text using Gemini API (if not already done)
            if existing_extraction["text_extraction"]["exists"]:
                print(
                    f"    ✓ Text already extracted, using existing file: {Path(existing_extraction['text_extraction']['path']).name}"
                )

                # Use the existing extraction
                try:
                    rel_path = Path(existing_extraction["text_extraction"]["path"]).relative_to(data_root)
                    relative_path = str(rel_path)
                except ValueError:
                    relative_path = existing_extraction["text_extraction"]["path"]

                page_results["text_extraction"] = {
                    "status": "success",
                    "output_file": relative_path,
                    "reused_existing": True,
                }
            else:
                print("    Extracting text content...")
                text_result = extract_text_from_pdf_page(str(page_file))

                if text_result["status"] == "success":
                    # Save extracted text to a markdown file
                    output_md = pages_folder / f"page_{page_num}.md"
                    with open(output_md, "w", encoding="utf-8") as f:
                        f.write(text_result["content"])

                    # Store relative path instead of absolute path
                    try:
                        rel_path = output_md.relative_to(data_root)
                        relative_path = str(rel_path)
                    except ValueError:
                        # If the path is not relative to data_root, use the full path as fallback
                        relative_path = str(output_md)

                    print(f"    ✓ Extracted text saved to {output_md.name}")
                    page_results["text_extraction"] = {"status": "success", "output_file": relative_path}
                else:
                    print(f"    ✗ Failed to extract text: {text_result.get('error', 'Unknown error')}")
                    page_results["text_extraction"] = {
                        "status": "error",
                        "error": text_result.get("error", "Unknown error"),
                    }

            # 2. Extract tables using Gemini API (if not already done)
            if existing_extraction["table_extraction"]["exists"]:
                print(
                    f"    ✓ Tables already extracted, using existing file: {Path(existing_extraction['table_extraction']['path']).name}"
                )

                # Use the existing extraction
                try:
                    rel_path = Path(existing_extraction["table_extraction"]["path"]).relative_to(data_root)
                    relative_path = str(rel_path)
                except ValueError:
                    relative_path = existing_extraction["table_extraction"]["path"]

                tables_count = existing_extraction["table_extraction"].get("tables_count", 0)

                page_results["table_extraction"] = {
                    "status": "success",
                    "output_file": relative_path,
                    "tables_count": tables_count,
                    "reused_existing": True,
                }
            else:
                print("    Extracting tables...")
                try:
                    table_result = extract_tables_from_pdf_page(str(page_file))

                    if table_result["status"] == "success":
                        # Save extracted tables to a JSON file
                        output_json = pages_folder / f"page_{page_num}_tables.json"

                        # Fix: Check the content type and wrap in proper structure if needed
                        content = table_result["content"]
                        if isinstance(content, list):
                            # If content is a list, wrap it in a dictionary with a tables key
                            formatted_content = {"tables": content}
                        else:
                            # If it's already a dictionary, use it as is
                            formatted_content = content

                        with open(output_json, "w", encoding="utf-8") as f:
                            json.dump(formatted_content, f, indent=2)

                        # Store relative path instead of absolute path
                        try:
                            rel_path = output_json.relative_to(data_root)
                            relative_path = str(rel_path)
                        except ValueError:
                            # If the path is not relative to data_root, use the full path as fallback
                            relative_path = str(output_json)

                        # Check if tables were found - handle both list and dict formats
                        if isinstance(content, list):
                            tables_count = len(content)
                        else:
                            tables_count = len(content.get("tables", []))

                        if tables_count > 0:
                            print(f"    ✓ Extracted {tables_count} tables saved to {output_json.name}")
                        else:
                            print("    ✓ No tables found on this page")

                        page_results["table_extraction"] = {
                            "status": "success",
                            "output_file": relative_path,
                            "tables_count": tables_count,
                        }
                    else:
                        print(f"    ✗ Failed to extract tables: {table_result.get('error', 'Unknown error')}")
                        page_results["table_extraction"] = {
                            "status": "error",
                            "error": table_result.get("error", "Unknown error"),
                        }
                except Exception as table_error:
                    print(f"    ✗ Exception in table extraction: {str(table_error)}")
                    page_results["table_extraction"] = {"status": "error", "error": str(table_error)}

        except Exception as e:
            print(f"  Error processing page {page_num}: {str(e)}")
            if "text_extraction" not in page_results:
                page_results["text_extraction"] = {"status": "error", "error": str(e)}
            if "table_extraction" not in page_results:
                page_results["table_extraction"] = {"status": "error", "error": str(e)}

        results[page_num] = page_results

    # Save overall results
    results_file = pages_folder / "extraction_results.json"

    # Make results paths relative
    try:
        rel_results_path = results_file.relative_to(data_root)
        relative_results_path = str(rel_results_path)
    except ValueError:
        relative_results_path = str(results_file)

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(
            {"pages_processed": len(page_numbers), "results": results, "results_path": relative_results_path},
            f,
            indent=2,
        )

    print(f"Processing complete. Results saved to {results_file}")
    return results


def check_existing_extraction(pages_folder: Path, page_num: int) -> dict:
    """
    Check if extraction has already been done for a page.

    Args:
        pages_folder: Path to the folder containing pages
        page_num: Page number to check

    Returns:
        Dictionary with text and table extraction status
    """
    result = {"text_extraction": {"exists": False, "path": None}, "table_extraction": {"exists": False, "path": None}}

    # Check for text extraction (markdown file)
    md_file = pages_folder / f"page_{page_num}.md"
    if md_file.exists() and md_file.stat().st_size > 0:
        result["text_extraction"]["exists"] = True
        result["text_extraction"]["path"] = str(md_file)

    # Check for table extraction (JSON file)
    json_file = pages_folder / f"page_{page_num}_tables.json"
    if json_file.exists() and json_file.stat().st_size > 0:
        result["table_extraction"]["exists"] = True
        result["table_extraction"]["path"] = str(json_file)

        # Optionally load the JSON to check if it's valid
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                import json

                tables_data = json.load(f)

                # Check if the table data has content
                if isinstance(tables_data, dict) and "tables" in tables_data:
                    result["table_extraction"]["tables_count"] = len(tables_data["tables"])
                elif isinstance(tables_data, list):
                    result["table_extraction"]["tables_count"] = len(tables_data)
        except:
            # If there's an error loading the JSON, mark as not existing
            result["table_extraction"]["exists"] = False
            result["table_extraction"]["path"] = None

    return result
