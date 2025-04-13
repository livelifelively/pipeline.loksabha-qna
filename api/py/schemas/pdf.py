from pydantic import BaseModel


class PDFExtractRequest(BaseModel):
    """Request schema for PDF extraction."""

    file_path: str
    extractor_type: str = "marker"


class PDFExtractResponse(BaseModel):
    """Response schema for PDF extraction."""

    text: str
