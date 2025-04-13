from pathlib import Path

from fastapi import APIRouter, HTTPException

from apps.py.parliament_questions.pdf_extraction import extract_pdf_contents

from ..core.config import get_settings
from ..schemas.pdf import PDFExtractRequest, PDFExtractResponse

router = APIRouter(tags=["pdf"])


@router.post("/extract-pdf", response_model=PDFExtractResponse)
async def extract_pdf_endpoint(request: PDFExtractRequest):
    """Extract text from a PDF file using its path in the sansad directory."""
    settings = get_settings()
    base_path = Path(settings.SANSAD_BASE_PATH)
    full_path = base_path / request.file_path

    try:
        full_path = full_path.resolve()
        if not str(full_path).startswith(str(base_path.resolve())):
            raise HTTPException(status_code=400, detail="Invalid path: Must be within sansad directory")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path") from None

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not full_path.suffix == ".pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        extracted_text = await extract_pdf_contents(full_path, extractor_type=request.extractor_type)
        return {"text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from None
