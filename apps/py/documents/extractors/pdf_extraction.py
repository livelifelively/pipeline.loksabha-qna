import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import camelot

from ...utils.pdf_extractors import get_pdf_extractor
from ..models import (
    LocalExtractionData,
    LocalExtractionPageData,
    ProcessingMetadata,
    ProcessingStatus,
    TableMetadata,
)
from ..utils.progress_handler import DocumentProgressHandler

"""
PDF Extraction Module

Function Hierarchy:
------------------
extract_contents (main entry point)
├── _extract_text_from_pdf
├── _extract_table_metadata_from_pdf
├── _save_file_safely
├── _process_extracted_text
├── _build_local_extraction_data
└── _calculate_processing_metadata

Usage Statistics:
----------------
- extract_contents: Called from cli/py/extract_pdf/menu.py
- Transitions document to LOCAL_EXTRACTION state with typed data

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
        self.progress_handler = None

    def _setup_paths(self, pdf_path: Path) -> None:
        """Setup paths for extraction outputs."""
        self.pdf_path = pdf_path
        self.text_path = pdf_path.parent / "extracted_text.md"
        self.progress_handler = DocumentProgressHandler(pdf_path.parent)

    def _validate_pdf_file(self) -> None:
        """Validate if the given path is a valid PDF file."""
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {self.pdf_path}")

    async def _save_file_safely(self, content: str, file_path: Path) -> None:
        """Safely save text content to a file using a temporary file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(content)

        shutil.move(temp_file.name, file_path)

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

    def _create_failure_extraction_data(
        self, error: Exception, pages_data: Dict[int, LocalExtractionPageData] = None
    ) -> LocalExtractionData:
        """Create LocalExtractionData for failure case."""
        if pages_data is None:
            pages_data = {}

        # Create minimal ProcessingMetadata for failure case
        processing_metadata = ProcessingMetadata(
            processing_time_seconds=0.0,
            pages_processed=len(pages_data),
            pages_failed=len(pages_data),  # All processed pages are considered failed
            llm_model_used=None,
            reviewer=None,
        )

        return LocalExtractionData(
            status=ProcessingStatus.FAILED,
            timestamp=datetime.now(UTC),
            processing_metadata=processing_metadata,
            pages=pages_data,
            extracted_text_path=str(self.text_path.name) if self.text_path else "",
            extracted_tables_path=None,  # We don't save table data
            table_metadata=[],  # Empty list for failed case
            error_message=str(error),
        )

    async def _extract_text_from_pdf(self) -> str:
        """Extract text from PDF using the specified extractor."""
        try:
            extractor = get_pdf_extractor(self.extractor_type)
            return await extractor.extract_text(self.pdf_path)
        except Exception as e:
            error_msg = f"Error extracting text from PDF: {str(e)}"
            print(error_msg)
            return f"[{error_msg}]"

    async def _extract_table_metadata_from_pdf(self) -> List[TableMetadata]:
        """Extract table metadata from PDF without saving unreliable table data."""
        try:
            tables = camelot.read_pdf(str(self.pdf_path), pages="all", flavor="lattice")
            table_metadata = []

            for i, table in enumerate(tables):
                df = table.df
                metadata = TableMetadata(
                    table_number=i + 1,
                    page=table.page,
                    accuracy=table.accuracy,
                    num_columns=len(df.columns),
                    num_rows=len(df.index) - 1,  # Subtract header row
                )
                table_metadata.append(metadata)

            return table_metadata

        except Exception as e:
            print(f"Warning: Failed to extract table metadata: {str(e)}")
            return []

    def _create_extraction_step(self, table_metadata: List[TableMetadata]) -> LocalExtractionData:
        """Create extraction step data as LocalExtractionData object."""
        # Process the extracted text file to get raw page data
        raw_pages_data = self._process_extracted_text()

        # Build typed LocalExtractionPageData for each page
        typed_pages = {}
        for page_num_str, page_info in raw_pages_data.items():
            page_num = int(page_num_str)

            # Find tables on this page from metadata
            tables_on_page = [t for t in table_metadata if t.page == page_num]

            # Create typed LocalExtractionPageData
            page_data = LocalExtractionPageData(
                has_tables=len(tables_on_page) > 0,
                num_tables=len(tables_on_page),
                text=page_info.get("text", ""),
                errors=[],  # No errors in successful case
            )

            typed_pages[page_num] = page_data

        # Create ProcessingMetadata
        processing_metadata = ProcessingMetadata(
            processing_time_seconds=0.0,  # TODO: Calculate actual time
            pages_processed=len(typed_pages),
            pages_failed=0,
            llm_model_used=None,
            reviewer=None,
        )

        # Return typed LocalExtractionData object
        return LocalExtractionData(
            status=ProcessingStatus.SUCCESS,
            timestamp=datetime.now(UTC),
            processing_metadata=processing_metadata,
            pages=typed_pages,
            extracted_text_path=str(self.text_path.name),
            extracted_tables_path=None,  # We don't save unreliable table data
            table_metadata=table_metadata,
            error_message=None,
        )

    async def extract_contents(self, pdf_path: Path) -> Dict[str, Any]:
        """Main method to extract PDF contents."""
        self._setup_paths(pdf_path)
        self._validate_pdf_file()

        try:
            # Extract and save text
            extracted_text = await self._extract_text_from_pdf()
            await self._save_file_safely(extracted_text, self.text_path)

            # Extract table metadata only (don't save unreliable table data)
            table_metadata = await self._extract_table_metadata_from_pdf()

            # Create LocalExtractionData and transition to LOCAL_EXTRACTION state
            local_extraction_data = self._create_extraction_step(table_metadata)
            self.progress_handler.transition_to_local_extraction(local_extraction_data)

            # Return the updated progress data for CLI compatibility
            return self.progress_handler.read_progress_file().model_dump()

        except Exception as e:
            # Create LocalExtractionData for failure case and transition state
            print(f"Critical error during extraction: {str(e)}")

            try:
                # Try to create failure data even if extraction failed
                failure_data = self._create_failure_extraction_data(e)
                self.progress_handler.transition_to_local_extraction(failure_data)
                print("Successfully transitioned to LOCAL_EXTRACTION state with FAILED status")
            except Exception as progress_error:
                print(f"Warning: Failed to update progress file: {progress_error}")

            raise
