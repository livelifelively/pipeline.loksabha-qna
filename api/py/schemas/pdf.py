from pydantic import BaseModel


class PDFExtractResponse(BaseModel):
    text: str
