import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import camelot

from ..utils.pdf_extractors import get_pdf_extractor

"""
PDF Extraction Module

Function Hierarchy:
------------------
extract_pdf_contents (main entry point)
├── extract_text_from_pdf
├── extract_tables_from_pdf
├── save_file_safely
├── create_extraction_step
│   └── create_table_summary
├── update_progress_step
└── create_failure_step

Usage Statistics:
----------------
- extract_pdf_contents: Called from cli/py/extract_pdf/menu.py
- save_file_safely: Called 4 times in extract_pdf_contents
- Other functions: Called once in extract_pdf_contents

Each function's purpose and dependencies are documented in its docstring.
"""


class PDFExtractor:
    def __init__(self, extractor_type: str = "marker"):
        self.extractor_type = extractor_type
        self.pdf_path = None
        self.progress_path = None
        self.text_path = None
        self.tables_path = None
        self.progress_data = None

    def _validate_pdf_file(self) -> None:
        """Validate if the given path is a valid PDF file."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {self.pdf_path}")

    async def _load_progress_data(self) -> None:
        """Load progress data from the progress.json file."""
        with open(self.progress_path, "r", encoding="utf-8") as f:
            self.progress_data = json.load(f)

    async def _save_file_safely(self, content: Any, file_path: Path, is_json: bool = False) -> None:
        """Safely save content to a file using a temporary file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            if is_json:
                json.dump(content, temp_file, indent=2, ensure_ascii=False)
            else:
                temp_file.write(content)

        shutil.move(temp_file.name, file_path)

    def _create_table_summary(self, tables: List[Dict]) -> Dict[str, Any]:
        """Create summary of extracted tables."""
        return {
            "has_tables": len(tables) > 0,
            "num_tables": len(tables),
            "tables_data": {
                "tables_summary": [
                    {
                        "table_number": table["table_number"],
                        "page": table["page"],
                        "accuracy": table["accuracy"],
                        "num_rows": len(table["rows"]),
                        "num_columns": len(table["headers"]),
                    }
                    for table in tables
                ]
                if tables
                else []
            },
        }

    def _update_progress_step(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update progress data with new step information."""
        if "steps" not in self.progress_data:
            self.progress_data["steps"] = []

        # Remove existing step if present
        self.progress_data["steps"] = [
            step for step in self.progress_data["steps"] if step.get("step") != "pdf_extraction"
        ]

        # Add new step
        self.progress_data["steps"].append(step_data)
        return self.progress_data

    def _setup_paths(self, pdf_path: Path) -> None:
        """Setup all required file paths for PDF extraction."""
        self.pdf_path = pdf_path
        self.progress_path = pdf_path.parent / "progress.json"
        self.text_path = pdf_path.parent / "extracted_text.md"
        self.tables_path = pdf_path.parent / "extracted_tables.json"

    def _create_extraction_step(self, tables: List[Dict]) -> Dict[str, Any]:
        """Create extraction step data."""
        return {
            "step": "pdf_extraction",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "data": {
                "extracted_text_path": str(self.text_path.name),
                "tables_path": str(self.tables_path.name),
                **self._create_table_summary(tables),
            },
        }

    def _create_failure_step(self, error: Exception) -> Dict[str, Any]:
        """Create failure step data."""
        return {
            "step": "pdf_extraction",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "failed",
            "error": str(error),
        }

    async def _extract_tables_from_pdf(self) -> List[Dict]:
        """Extract tables from PDF using Camelot with lattice method."""
        try:
            tables = camelot.read_pdf(str(self.pdf_path), pages="all", flavor="lattice")
            extracted_tables = []

            for i, table in enumerate(tables):
                df = table.df
                headers = df.iloc[0].tolist()
                rows = [dict(zip(headers, row.tolist())) for _, row in df.iloc[1:].iterrows()]

                table_data = {
                    "table_number": i + 1,
                    "page": table.page,
                    "headers": headers,
                    "rows": rows,
                    "accuracy": table.accuracy,
                    **table.parsing_report,
                }
                extracted_tables.append(table_data)

            return extracted_tables

        except Exception as e:
            raise Exception(f"Failed to extract tables from PDF: {str(e)}") from e

    async def _extract_text_from_pdf(self) -> str:
        """Extract text from PDF using the specified extractor."""
        try:
            extractor = get_pdf_extractor(self.extractor_type)
            return await extractor.extract_text(self.pdf_path)
        except Exception as e:
            error_msg = f"Error extracting text from PDF: {str(e)}"
            print(error_msg)
            return f"[{error_msg}]"

    async def extract_contents(self, pdf_path: Path) -> str:
        """Main method to extract PDF contents."""
        self._setup_paths(pdf_path)
        self._validate_pdf_file()

        try:
            await self._load_progress_data()

            # Extract and save text
            extracted_text = await self._extract_text_from_pdf()
            await self._save_file_safely(extracted_text, self.text_path)

            # Extract and save tables
            tables = await self._extract_tables_from_pdf()
            await self._save_file_safely(tables, self.tables_path, is_json=True)

            # Update and save progress
            step_data = self._create_extraction_step(tables)
            updated_progress = self._update_progress_step(step_data)
            await self._save_file_safely(updated_progress, self.progress_path, is_json=True)

            return updated_progress

        except Exception as e:
            try:
                step_data = self._create_failure_step(e)
                updated_progress = self._update_progress_step(step_data)
                await self._save_file_safely(updated_progress, self.progress_path, is_json=True)
            except (IOError, json.JSONDecodeError):
                pass

            raise Exception(f"Failed to extract PDF contents: {str(e)}") from e
