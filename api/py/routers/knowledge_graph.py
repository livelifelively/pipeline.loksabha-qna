from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from apps.py.knowledge_graph.exceptions import InvalidMetadataError, KnowledgeGraphError, QuestionNotFoundError
from apps.py.knowledge_graph.repository import CleanedDataRepository
from apps.py.knowledge_graph.service import CleanedDataService
from apps.py.utils.project_root import get_loksabha_data_root

from ..schemas.knowledge_graph import CleanedDataUpdateRequest, CleanedDataUpdateResponse

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])


@router.patch(
    "/cleaned-data",
    response_model=CleanedDataUpdateResponse,
    summary="Update cleaned data for knowledge graph creation",
    description="""
    Updates the cleaned data for a specific question. This endpoint:
    - Can handle single or multiple page updates
    - Initializes data structure if this is the first update
    - Updates progress tracking
    - Returns the updated pages and file path
    
    The endpoint is idempotent - multiple calls with the same data produce the same result.
    """,
    responses={
        200: {
            "description": "Successfully updated cleaned data",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "updated_pages": [1, 2],
                            "cleaned_data_path": "data/18/iv/ministries/health-and-family-welfare/61/cleaned_data.json",
                            "timestamp": "2025-05-04T20:10:00.000000",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid metadata provided",
            "content": {"application/json": {"example": {"detail": "Missing required metadata fields: question_id"}}},
        },
        404: {
            "description": "Question not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Question not found at path: data/18/iv/ministries/health-and-family-welfare/61"
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error saving cleaned data: Permission denied"}}},
        },
    },
)
async def update_cleaned_data(request: CleanedDataUpdateRequest):
    """
    Update cleaned data for knowledge graph creation.

    Args:
        request (CleanedDataUpdateRequest): The request containing:
            - pages: List of pages to update, each containing:
                - page_number: The page number
                - text: The page text content
                - tables: Optional list of tables on the page
            - metadata: Question metadata containing:
                - loksabha_number: The Lok Sabha number
                - session_number: The session number
                - question_id: The question ID

    Returns:
        CleanedDataUpdateResponse: Response containing:
            - status: Success status
            - data: Object containing:
                - updated_pages: List of updated page numbers
                - cleaned_data_path: Path to the cleaned data file
                - timestamp: ISO format timestamp of the update

    Raises:
        HTTPException:
            - 400: If metadata is invalid
            - 404: If question doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize the service with repository
        repository = CleanedDataRepository(base_path=get_loksabha_data_root())
        service = CleanedDataService(repository=repository)
        result = await service.update_cleaned_data(pages=request.pages, metadata=request.metadata)

        return CleanedDataUpdateResponse(
            status="success",
            data={
                "updated_pages": result.updated_pages,
                "cleaned_data_path": result.cleaned_data_path,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
    except QuestionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidMetadataError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except KnowledgeGraphError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
