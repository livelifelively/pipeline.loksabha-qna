import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import camelot

from ..documents.utils.progress_handler import ProgressHandler
from ..utils.pdf_extractors import get_pdf_extractor
from ..utils.project_root import get_loksabha_data_root

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


class QuestionPDFExtractor:
    def __init__(self, extractor_type: str = "marker"):
        """Initialize the PDF extractor.

        Args:
            extractor_type: Type of extractor to use ('marker')
        """
        self.extractor_type = extractor_type
        self.pdf_path = None
        self.text_path = None
        self.tables_path = None
        self.data_root = get_loksabha_data_root()
        self.progress_handler = None

    def _setup_paths(self, pdf_path: Path) -> None:
        """Setup paths for extraction outputs."""
        self.pdf_path = pdf_path
        self.text_path = pdf_path.parent / "extracted_text.md"
        self.tables_path = pdf_path.parent / "extracted_tables.json"
        self.progress_handler = ProgressHandler(pdf_path.parent)

    def _get_relative_path(self, path: Path) -> str:
        """Convert path to relative path from data root."""
        try:
            return str(path.relative_to(self.data_root))
        except ValueError:
            return str(path)

    def _validate_pdf_file(self) -> None:
        """Validate if the given path is a valid PDF file."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {self.pdf_path}")

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

    def _process_extracted_text(self) -> Dict[str, Dict[str, Any]]:
        """Process the extracted text file and split it by pages."""
        pages = {}
        try:
            with open(self.text_path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"Processing extracted text content length: {len(content)}")
            if not content.strip():
                print("Warning: Extracted text content is empty")
                return pages

            import re

            # Split using lookahead regex to match page markers
            page_parts = re.split(r"(?=\{[\d]+\}------------------------------------------------)", content)
            page_parts = [part for part in page_parts if part.strip()]
            print(f"Found {len(page_parts)} page parts after splitting")

            for index, part in enumerate(page_parts):
                try:
                    # Remove the page marker header and clean the text
                    text_content = re.sub(
                        r"^\{[\d]+\}------------------------------------------------\n?", "", part.strip()
                    )

                    # Use 1-based page numbers (index + 1)
                    page_num = str(index + 1)

                    pages[page_num] = {"status": "success", "text": text_content, "length": len(text_content)}
                except Exception as page_error:
                    print(f"Warning: Error processing page {index + 1}: {page_error}")
                    continue

            print(f"Successfully processed {len(pages)} pages")

        except Exception as e:
            print(f"Warning: Error processing extracted text: {str(e)}")
            import traceback

            print(f"Stack trace: {traceback.format_exc()}")

        return pages

    def _create_extraction_step(self, tables: List[Dict]) -> Dict[str, Any]:
        """Create extraction step data."""
        # Process the extracted text file to get page-level data
        pages_data = self._process_extracted_text()

        return {
            "step": "pdf_extraction",
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "success",
            "data": {
                "extracted_text_path": str(self.text_path.name),
                "tables_path": str(self.tables_path.name),
                "pages": pages_data,
                **self._create_table_summary(tables),
            },
        }

    def _create_failure_step(self, error: Exception) -> Dict[str, Any]:
        """Create failure step data."""
        return {
            "step": "pdf_extraction",
            "timestamp": datetime.now(UTC).isoformat(),
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

    async def extract_contents(self, pdf_path: Path) -> Dict[str, Any]:
        """Main method to extract PDF contents."""
        self._setup_paths(pdf_path)
        self._validate_pdf_file()

        try:
            # Extract and save text
            extracted_text = await self._extract_text_from_pdf()
            await self._save_file_safely(extracted_text, self.text_path)

            # Extract and save tables
            tables = await self._extract_tables_from_pdf()
            await self._save_file_safely(tables, self.tables_path, is_json=True)

            # Create and append success step
            step_data = self._create_extraction_step(tables)
            self.progress_handler.append_step(step_data)

            # Return the updated progress data
            return self.progress_handler.read_progress_file()

        except Exception as e:
            # Create and append failure step
            step_data = self._create_failure_step(e)
            try:
                self.progress_handler.append_step(step_data)
            except Exception as progress_error:
                print(f"Warning: Failed to update progress file: {progress_error}")
            raise
