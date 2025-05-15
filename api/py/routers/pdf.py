from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from apps.py.parliament_questions.document_processing import (
    calculate_table_statistics,
    find_documents_with_tables,
)
from apps.py.parliament_questions.pdf_extraction import extract_pdf_contents
from apps.py.utils.paths import PathValidationError, validate_and_get_ministry_paths, validate_document_path
from apps.py.utils.project_root import get_loksabha_data_root

from ..schemas.pdf import PDFExtractRequest, PDFExtractResponse

router = APIRouter(tags=["pdf"])


@router.post("/extract-pdf", response_model=PDFExtractResponse)
async def extract_pdf_endpoint(request: PDFExtractRequest):
    """Extract text from a PDF file using its path in the sansad directory."""
    full_path = get_loksabha_data_root() / request.file_path

    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(get_loksabha_data_root().resolve())):
            raise HTTPException(status_code=400, detail="Invalid path: Must be within project directory")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path") from None

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.suffix == ".pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        extracted_data = await extract_pdf_contents(full_path, extractor_type=request.extractor_type)
        return extracted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None


# New schemas for table-related endpoints
class MinistryPath(BaseModel):
    """Model for ministry path input."""

    path: str
    name: Optional[str] = None


class DocumentWithTables(BaseModel):
    """Model for document with tables."""

    path: str
    ministry: str
    table_pages: List[int]
    num_tables: int


class TableStatistics(BaseModel):
    """Model for table statistics."""

    by_ministry: dict
    totals: dict


class FindTablesRequest(BaseModel):
    """Request model for finding tables."""

    sansad: str
    session: str
    ministries: List[str]


class ProcessTableRequest(BaseModel):
    """Request model for processing tables in a document."""

    document_path: str
    table_pages: List[int]
    output_folder: Optional[str] = None


# New endpoints for table functionality
@router.post("/tables/find")
async def find_tables_endpoint(request: FindTablesRequest):
    """Find documents with tables in the specified ministries."""
    try:
        # Validate and get ministry paths using shared utility
        try:
            _, _, ministry_paths = validate_and_get_ministry_paths(request.sansad, request.session, request.ministries)
        except PathValidationError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

        # Find documents with tables
        documents = find_documents_with_tables(ministry_paths)

        # Calculate statistics
        stats = calculate_table_statistics(documents)

        return {"status": "success", "documents": documents, "statistics": stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding tables: {str(e)}") from e


@router.get("/tables/ministries")
async def list_ministries_endpoint(
    sansad: str = Query(..., description="Sansad name"), session: str = Query(..., description="Session name")
):
    """List available ministries for a given sansad and session."""
    try:
        # Validate session path
        _, ministries_dir, _ = validate_and_get_ministry_paths(sansad, session, [])

        # List all ministry directories
        ministries = [d.name for d in ministries_dir.iterdir() if d.is_dir()]

        return {"sansad": sansad, "session": session, "ministries": ministries}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing ministries: {str(e)}") from e


@router.post("/tables/process")
async def process_tables_endpoint(request: ProcessTableRequest):
    """Process a document to extract tables."""
    try:
        # Validate document path using shared utility
        try:
            doc_path = validate_document_path(request.document_path)
        except PathValidationError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)

        # Define output folder if not provided
        output_folder = request.output_folder
        if not output_folder:
            output_folder = str(doc_path.parent / "pages")

        # Process the document
        from apps.py.documents.pdf_splitter import split_pdf_pages_from_file

        results_folder = split_pdf_pages_from_file(str(doc_path), request.table_pages, output_folder)

        # Read the results
        results_file = Path(results_folder) / "extraction_results.json"
        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                import json

                results = json.load(f)
        else:
            results = {"status": "completed", "message": "Processing completed but no results file found"}

        return {
            "status": "success",
            "document": str(doc_path),
            "pages_processed": len(request.table_pages),
            "output_folder": results_folder,
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}") from e


@router.post("/tables/process-batch")
async def process_tables_batch_endpoint(documents: List[DocumentWithTables]):
    """Process multiple documents to extract tables."""
    try:
        # Convert to the format expected by the processing function
        docs_to_process = [doc.dict() for doc in documents]

        # Use a non-interactive version of the processing function
        # We'll create a custom implementation here to avoid CLI-specific output
        data_root = get_loksabha_data_root()
        results = []

        for doc in docs_to_process:
            doc_path_str = doc["path"]
            table_pages = doc["table_pages"]

            # Convert relative path to absolute path using data root if needed
            doc_path = Path(doc_path_str)
            if not doc_path.is_absolute():
                doc_path = data_root / doc_path

            try:
                # Make sure PDF exists
                if not doc_path.exists():
                    results.append({"status": "error", "document": str(doc_path), "error": "File not found"})
                    continue

                # Define output folder in the document directory
                output_folder = doc_path.parent / "pages"

                # Process the document
                from apps.py.documents.pdf_splitter import split_pdf_pages_from_file

                results_folder = split_pdf_pages_from_file(str(doc_path), table_pages, str(output_folder))

                # Read the results
                results_file = Path(results_folder) / "extraction_results.json"
                if results_file.exists():
                    with open(results_file, "r", encoding="utf-8") as f:
                        import json

                        extraction_results = json.load(f)
                else:
                    extraction_results = {
                        "status": "completed",
                        "message": "Processing completed but no results file found",
                    }

                results.append(
                    {
                        "status": "success",
                        "document": str(doc_path),
                        "pages_processed": len(table_pages),
                        "output_folder": results_folder,
                        "results": extraction_results,
                    }
                )
            except Exception as e:
                results.append({"status": "error", "document": str(doc_path), "error": str(e)})

        return {
            "total_documents": len(documents),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "error"),
            "document_results": results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing documents: {str(e)}") from e
