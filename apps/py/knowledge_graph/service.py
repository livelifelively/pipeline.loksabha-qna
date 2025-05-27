from dataclasses import dataclass
from datetime import UTC, datetime
from typing import List

from api.py.schemas.knowledge_graph import QuestionMetadata

from .exceptions import KnowledgeGraphError
from .repository import CleanedDataRepository
from .types import CleanedData, CleanedDataMetadata, PageData


@dataclass
class UpdateResult:
    """Result of cleaned data update operation"""

    updated_pages: List[int]
    cleaned_data_path: str


class CleanedDataService:
    def __init__(self, repository: CleanedDataRepository):
        self.repository = repository

    async def update_cleaned_data(self, pages: List[PageData], metadata: QuestionMetadata) -> UpdateResult:
        """
        Update cleaned data for knowledge graph creation.

        Args:
            pages: List of pages to update
            metadata: Question metadata containing document_path

        Returns:
            UpdateResult containing updated pages and file path

        Raises:
            ValueError: If metadata is invalid
            FileNotFoundError: If question doesn't exist
        """
        try:
            # Get file path
            cleaned_data_path = self.repository.get_cleaned_data_path(metadata)

            # Check if this is first update
            existing_data = await self._get_or_initialize_data(metadata, cleaned_data_path)

            # Update pages
            updated_data = self._update_pages_data(existing_data, pages)

            # Save changes
            await self.repository.save_cleaned_data(updated_data, cleaned_data_path)
            await self.repository.update_progress(metadata, cleaned_data_path, updated_data)

            return UpdateResult(
                updated_pages=[page.page_number for page in pages], cleaned_data_path=str(cleaned_data_path)
            )
        except KnowledgeGraphError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise KnowledgeGraphError(f"Unexpected error: {str(e)}") from e

    async def _get_or_initialize_data(self, metadata: QuestionMetadata, cleaned_data_path: str) -> CleanedData:
        """
        Get existing cleaned data or initialize new data structure.

        Args:
            metadata: Question metadata
            cleaned_data_path: Path to cleaned data file

        Returns:
            CleanedData instance
        """
        try:
            return await self.repository.read_cleaned_data(cleaned_data_path)
        except FileNotFoundError:
            # Initialize new data structure using pdf_extraction step
            pdf_extraction_data = await self.repository.get_pdf_extraction_data(metadata)

            # Create empty pages structure
            pages = [
                PageData(page_number=page_num, text="", tables=[])
                for page_num in range(1, pdf_extraction_data.total_pages + 1)
            ]

            # Create initial metadata
            initial_metadata = CleanedDataMetadata(
                total_pages=pdf_extraction_data.total_pages,
                pages_with_tables=0,
                total_tables=0,
                cleaning_timestamp=datetime.now(UTC),
            )

            return CleanedData(pages=pages, metadata=initial_metadata)

    def _update_pages_data(self, existing_data: CleanedData, new_pages: List[PageData]) -> CleanedData:
        """
        Update pages in the cleaned data.

        Args:
            existing_data: Current cleaned data
            new_pages: New pages to update

        Returns:
            Updated CleanedData
        """
        # Create a map of existing pages for quick lookup
        page_map = {page.page_number: page for page in existing_data.pages}

        # Update or add new pages
        for new_page in new_pages:
            page_map[new_page.page_number] = new_page

        # Convert back to list and sort by page number
        updated_pages = sorted(page_map.values(), key=lambda x: x.page_number)

        # Update metadata
        existing_data.pages = updated_pages
        existing_data.metadata.total_pages = len(updated_pages)
        existing_data.metadata.pages_with_tables = sum(1 for page in updated_pages if page.tables)
        existing_data.metadata.total_tables = sum(len(page.tables) for page in updated_pages if page.tables)
        existing_data.metadata.cleaning_timestamp = datetime.now(UTC)

        return existing_data
