from fastapi import FastAPI

from .routers import pdf

app = FastAPI(title="Parliament Questions API")
app.include_router(pdf.router, prefix="/api")
