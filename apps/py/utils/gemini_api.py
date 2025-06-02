import json
from typing import Any, Dict, Tuple

import google.generativeai as genai
from dotenv import load_dotenv

from apps.py.documents.models import MultiPageTableDetectionResult
from apps.py.llm_api_key.rate_limiter import RateLimiter
from apps.py.llm_api_key.usage_tracker import UsageTracker

# Load environment variables
load_dotenv()

# Module-level instance
_key_manager = None


def init_gemini() -> Any:
    """Initialize Gemini API with API key from key manager."""
    global _key_manager
    from apps.py.llm_api_key import KeyManager

    # Create key manager if it doesn't exist
    if _key_manager is None:
        _key_manager = KeyManager(service_name="gemini")

    key_name, api_key = _key_manager.get_next_key()

    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash"), key_name


def extract_text_from_pdf_page(pdf_page_path: str) -> Dict:
    """
    Extract text content from a PDF page using Gemini Vision API with key rotation.

    Args:
        pdf_page_path: Path to the PDF page file

    Returns:
        Dictionary with extracted text content in markdown format
    """
    model, key_name = init_gemini()
    tracker = UsageTracker(service_name="gemini")

    print(f"[Gemini API] Using key {key_name} for text extraction")

    try:
        # Read the PDF file directly
        with open(pdf_page_path, "rb") as f:
            pdf_data = f.read()

        # Prepare the prompt for text extraction
        prompt = """
            Analyze the provided document page comprehensively. Extract *all* content, including text paragraphs and tables, and format the entire output as Markdown. Maintain the original order and structure of the content as closely as possible.

            For regular text content:
            - Preserve paragraph breaks (use double line breaks in Markdown).
            - Attempt to identify and format basic structures like lists or headings if present, using standard Markdown syntax (`#` for headings, `*` or `-` for lists).

            For *each table* found in the document:
            1.  **First, analyze its structure:** Identify column headers (including any hierarchy/nesting), data rows, and any merged cells (cells spanning multiple rows or columns).
            2.  **Based on this analysis, generate a Markdown table representation:**
                *   Use the standard Markdown table syntax (pipes `|` and hyphens `-` for separators).
                *   **Header Handling:** If the table has hierarchical (multi-level) headers, create a **single header row** for the Markdown table. Combine parent and child header text logically to form unique, descriptive headers in that single row (e.g., concatenate with a separator like ' - ', such as 'Budget - Total', 'Budget - Rural', or choose the most specific header if appropriate).
                *   **Merged Cell Handling:** Standard Markdown tables do not support merged cells (`colspan` or `rowspan`). To handle this, **repeat** the content of the original merged cell in *each* corresponding cell of the output Markdown table row(s) that it spanned. This ensures the data is present in the correct logical columns/rows, even if the visual merge isn't replicated.
                *   Ensure data values are correctly placed under their corresponding (potentially flattened) headers.

            Integrate the formatted Markdown tables seamlessly within the extracted text content, respecting their original position in the document.

            Output *only* the final, complete Markdown content. Do not include any commentary before or after the Markdown output itself.
        """

        # Call Gemini API with PDF directly
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])

        # Record successful usage
        tracker.record_usage(key_name, success=True)

        # Process response
        extracted_text = response.text.strip()

        return {"status": "success", "content": extracted_text, "format": "markdown"}
    except Exception as e:
        # Record failed usage
        tracker.record_usage(key_name, success=False)

        print(f"Error extracting text from PDF page: {str(e)}")
        return {"status": "error", "error": str(e)}


def extract_tables_from_pdf_page(pdf_page_path: str) -> Dict:
    """
    Extract tables from a PDF page using Gemini Vision API with key rotation.

    Args:
        pdf_page_path: Path to the PDF page file

    Returns:
        Dictionary with extracted table data in JSON format
    """
    model, key_name = init_gemini()
    tracker = UsageTracker(service_name="gemini")
    limiter = RateLimiter(requests_per_minute=10)

    # Apply rate limiting
    wait_time = limiter.wait_if_needed()
    if wait_time > 0:
        print(f"[Rate Limiter] Waiting {wait_time:.1f}s before API call")

    print(f"[Gemini API] Using key {key_name} for table extraction")

    try:
        # Read the PDF file directly
        with open(pdf_page_path, "rb") as f:
            pdf_data = f.read()

        # Prepare the prompt for table extraction with headers as keys
        prompt = """
            First, analyze the structure of the main table in the provided document. Identify:
            1.  The column headers and their hierarchy (single or multi-level).
            2.  The data rows.
            3.  Any merged cells and the rows/columns they span.

            Based on this analysis, generate a JSON array representing the table data.
            - Each object in the array should represent one data row.
            - Use the column headers as keys. For hierarchical headers, create nested JSON objects mirroring the structure found in the table.
            - Map data values to the most specific corresponding header key within the structure.
            - For merged cells, associate the value correctly with all applicable rows/columns in the resulting JSON.

            Use exact header text for keys. Output only the final JSON array.
        """

        # Call Gemini API
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])

        # Record successful usage
        tracker.record_usage(key_name, success=True)

        # Process response - handle potential JSON parsing issues carefully
        try:
            extracted_text = response.text.strip()

            # Try to parse JSON from the response
            try:
                parsed_json = json.loads(extracted_text)
                return {"status": "success", "content": parsed_json, "format": "json"}
            except json.JSONDecodeError as e:
                # Try to clean up the response if it contains fence blocks
                if "```json" in extracted_text:
                    json_content = extracted_text.split("```json")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return {"status": "success", "content": parsed_json, "format": "json"}
                elif "```" in extracted_text:
                    # Try with just code fence without language specifier
                    json_content = extracted_text.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return {"status": "success", "content": parsed_json, "format": "json"}
                else:
                    raise ValueError(f"Failed to parse JSON: {e}") from e
        except Exception as json_error:
            # Still count as a successful API call since the API responded
            return {"status": "error", "error": f"JSON parsing error: {str(json_error)}", "raw_response": response.text}

    except Exception as e:
        # Record failed usage
        tracker.record_usage(key_name, success=False)

        print(f"Error extracting tables from PDF page: {str(e)}")
        return {"status": "error", "error": str(e)}


def detect_multi_page_tables(pdf_path: str) -> MultiPageTableDetectionResult:
    """
    Detect if a PDF contains multi-page tables using Gemini Vision API.

    Args:
        pdf_path: Path to the PDF file (already split to contain only relevant pages)

    Returns:
        MultiPageTableDetectionResult containing detection results
    """
    model, key_name = init_gemini()
    tracker = UsageTracker(service_name="gemini")
    limiter = RateLimiter(requests_per_minute=10)

    # Apply rate limiting
    wait_time = limiter.wait_if_needed()
    if wait_time > 0:
        print(f"[Rate Limiter] Waiting {wait_time:.1f}s before API call")

    print(f"[Gemini API] Using key {key_name} for multi-page table detection")

    try:
        # Read the PDF data
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        # Prepare the prompt for multi-page table detection
        prompt = """
            Analyze the provided PDF pages to identify all continuous tables that span across multiple pages.
            
            Consider these factors for each table:
            1. Table structure continuity (headers, columns, formatting)
            2. Content continuity (data flows naturally across pages)
            3. Visual indicators of table continuation (e.g., "continued from previous page")
            4. Serial number continuity (e.g., row numbers continuing across pages)
            
            Respond with a JSON object containing:
            {
                "multi_page_tables": [
                    {
                        "pages": [list of page numbers that are part of this continuous table],
                        "confidence": float (0.0 to 1.0),
                        "reasoning": "brief explanation of why these pages are connected"
                    },
                    // ... more tables if found
                ]
            }
            
            Rules:
            1. Each table in the list should be a distinct continuous table
            2. A page can only be part of one table
            3. If no multi-page tables are found, return an empty list
            4. Order tables by their starting page number
            
            Output only the JSON object, no additional text.
        """

        # Call Gemini API
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])

        # Record successful usage
        tracker.record_usage(key_name, success=True)

        # Process response
        try:
            extracted_text = response.text.strip()

            # Try to parse JSON from the response
            try:
                parsed_json = json.loads(extracted_text)
                return MultiPageTableDetectionResult(
                    status="success",
                    multi_page_tables=parsed_json.get("multi_page_tables", []),
                )
            except json.JSONDecodeError as e:
                # Try to clean up the response if it contains fence blocks
                if "```json" in extracted_text:
                    json_content = extracted_text.split("```json")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return MultiPageTableDetectionResult(
                        status="success",
                        multi_page_tables=parsed_json.get("multi_page_tables", []),
                    )
                elif "```" in extracted_text:
                    json_content = extracted_text.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return MultiPageTableDetectionResult(
                        status="success",
                        multi_page_tables=parsed_json.get("multi_page_tables", []),
                    )
                else:
                    raise ValueError(f"Failed to parse JSON: {e}") from e
        except Exception as json_error:
            return MultiPageTableDetectionResult(
                status="error",
                error=f"JSON parsing error: {str(json_error)}",
            )

    except Exception as e:
        # Record failed usage
        tracker.record_usage(key_name, success=False)
        print(f"Error detecting multi-page tables: {str(e)}")
        return MultiPageTableDetectionResult(
            status="error",
            error=str(e),
        )


def extract_multi_page_table(pdf_path: str, page_range: Tuple[int, int]) -> Dict:
    """
    Extract a table that spans across multiple pages using Gemini Vision API.

    Args:
        pdf_path: Path to the PDF file (already split to contain only relevant pages)
        page_range: Tuple of (start_page, end_page) numbers

    Returns:
        Dictionary with extraction results:
        {
            "status": "success" | "error",
            "content": List[Dict] | None,  # Table data in JSON format
            "error": str | None  # Only present if status is "error"
        }
    """
    model, key_name = init_gemini()
    tracker = UsageTracker(service_name="gemini")
    limiter = RateLimiter(requests_per_minute=10)

    # Apply rate limiting
    wait_time = limiter.wait_if_needed()
    if wait_time > 0:
        print(f"[Rate Limiter] Waiting {wait_time:.1f}s before API call")

    print(f"[Gemini API] Using key {key_name} for multi-page table extraction")

    try:
        # Read the PDF data
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()

        # Prepare the prompt for multi-page table extraction
        prompt = """
            Extract the continuous table that spans across these pages. The table may have:
            1. Headers that repeat on each page
            2. Data that continues across page breaks
            3. Merged cells that span multiple pages
            4. Serial numbers or other indicators of continuity

            Generate a JSON array representing the complete table data:
            - Each object in the array should represent one data row
            - Use the column headers as keys
            - For hierarchical headers, create nested JSON objects
            - Handle merged cells by associating values with all applicable rows
            - Maintain the correct order of rows across pages
            - Preserve any serial numbers or identifiers

            Output only the final JSON array, no additional text.
        """

        # Call Gemini API
        response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_data}])

        # Record successful usage
        tracker.record_usage(key_name, success=True)

        # Process response - handle potential JSON parsing issues carefully
        try:
            extracted_text = response.text.strip()

            # Try to parse JSON from the response
            try:
                parsed_json = json.loads(extracted_text)
                return {"status": "success", "content": parsed_json}
            except json.JSONDecodeError as e:
                # Try to clean up the response if it contains fence blocks
                if "```json" in extracted_text:
                    json_content = extracted_text.split("```json")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return {"status": "success", "content": parsed_json}
                elif "```" in extracted_text:
                    json_content = extracted_text.split("```")[1].split("```")[0].strip()
                    parsed_json = json.loads(json_content)
                    return {"status": "success", "content": parsed_json}
                else:
                    raise ValueError(f"Failed to parse JSON: {e}") from e
        except Exception as json_error:
            return {"status": "error", "error": f"JSON parsing error: {str(json_error)}", "raw_response": response.text}

    except Exception as e:
        # Record failed usage
        tracker.record_usage(key_name, success=False)
        print(f"Error extracting multi-page table: {str(e)}")
        return {"status": "error", "error": str(e)}
