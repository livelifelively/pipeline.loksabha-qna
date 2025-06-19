from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from apps.py.documents.utils.progress_handler import ProgressHandler
from apps.py.knowledge_graph.exceptions import InvalidMetadataError, QuestionNotFoundError
from apps.py.utils.project_root import get_loksabha_data_root

from ..schemas.knowledge_graph import (
    CleanedDataUpdateRequest,
    CleanedDataUpdateResponse,
    LlmExtractionRequest,
    LlmExtractionResponse,
)

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
    - Returns the updated pages and progress status
    
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
                            "progress_status": "manual_review_complete",
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
                - document_path: The path to the question document

    Returns:
        CleanedDataUpdateResponse: Response containing:
            - status: Success status
            - data: Object containing:
                - updated_pages: List of updated page numbers
                - progress_status: Progress status (e.g., "manual_review_complete")
                - timestamp: ISO format timestamp of the update

    Raises:
        HTTPException:
            - 400: If metadata is invalid
            - 404: If question doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize progress handler for the document
        document_path = get_loksabha_data_root() / request.metadata.document_path
        handler = ProgressHandler(document_path)

        # Convert request pages to domain format (no state machine knowledge!)
        pages_data = []
        for page in request.pages:
            pages_data.append({"page_number": page.page_number, "text": page.text, "tables": page.tables})

        # Use domain method - no knowledge of states or state transitions!
        result = handler.save_cleaned_pages(pages_data)

        return CleanedDataUpdateResponse(
            status="success",
            data={
                "updated_pages": result["updated_pages"],
                "progress_status": result["progress_status"],
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
    except QuestionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidMetadataError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cleaned data: {str(e)}") from e


@router.patch(
    "/llm-extraction",
    response_model=LlmExtractionResponse,
    summary="Perform LLM extraction on a document",
    description="""
    Performs LLM extraction on the specified document. This endpoint:
    - Validates that LLM extraction is allowed for the document's current state
    - Triggers the LLM extraction process and waits for completion
    - Supports both initial extraction and retries (uses self-transition)
    - Returns the complete LLM extraction state data
    
    The endpoint handles state transitions automatically using the existing state machine.
    """,
    responses={
        200: {
            "description": "LLM extraction completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "status": "SUCCESS",
                            "processing_metadata": {"processing_time_seconds": 45.2},
                            "pages": {"1": {"has_tables": True, "num_tables": 2}},
                            "extracted_text_path": "extracted_text.json",
                            "total_tables": 2,
                            "successful_tables": 2,
                            "failed_tables": 0,
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid request or transition not allowed",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot transition to LLM_EXTRACTION: Document not in valid state"}
                }
            },
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Document not found at path: data/18/iv/ministries/health-and-family-welfare/61"
                    }
                }
            },
        },
        500: {
            "description": "LLM extraction failed",
            "content": {"application/json": {"example": {"detail": "LLM extraction failed: Connection timeout"}}},
        },
    },
)
async def perform_llm_extraction(request: LlmExtractionRequest):
    """
    Perform LLM extraction on a document.

    Args:
        request (LlmExtractionRequest): The request containing:
            - document_path: The path to the question document

    Returns:
        LlmExtractionResponse: Response containing:
            - status: Success status
            - data: Complete LLM extraction state data from question.progress.json

    Raises:
        HTTPException:
            - 400: If transition is not allowed or invalid request
            - 404: If document doesn't exist
            - 500: If LLM extraction fails
    """
    try:
        from apps.py.parliament_questions.document_processing import process_single_document_for_llm_extraction

        # Initialize document path
        document_path = get_loksabha_data_root() / request.document_path

        # Use shared function to process the document and get state data
        llm_state_data = process_single_document_for_llm_extraction(document_path)

        return LlmExtractionResponse(
            status="success",
            data=llm_state_data.model_dump() if hasattr(llm_state_data, "model_dump") else llm_state_data.__dict__,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}") from e


@router.get(
    "/cleaned-data",
    summary="Get cleaning progress for a document",
    description="Returns the current cleaning progress and statistics for a document.",
)
async def get_cleaning_progress(document_path: str):
    """
    Get cleaning progress for a document.

    Args:
        document_path: The path to the question document

    Returns:
        Dictionary containing cleaning progress information
    """
    try:
        # Initialize progress handler for the document
        full_document_path = get_loksabha_data_root() / document_path
        handler = ProgressHandler(full_document_path)

        # Use domain method - no state machine knowledge!
        progress = handler.get_cleaning_progress()

        return {"status": "success", "data": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting progress: {str(e)}") from e
