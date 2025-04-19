from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import pdf

app = FastAPI(title="Parliament Questions API")

# Add CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],  # You can specify specific methods like ["GET", "POST"]
    allow_headers=["*"],
)

app.include_router(pdf.router, prefix="/api")
