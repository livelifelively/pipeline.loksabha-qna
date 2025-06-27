from fastapi import APIRouter, HTTPException

from apps.py.documents.utils.progress_handler import DocumentProgressHandler, ProgressHandler
from apps.py.knowledge_graph.exceptions import InvalidMetadataError, QuestionNotFoundError
from apps.py.parliament_questions.document_processing import (
    process_single_document_for_llm_extraction,
    validate_single_document_for_llm_extraction,
)
from apps.py.utils.project_root import get_loksabha_data_root
from apps.py.utils.timestamps import get_current_timestamp_iso

from ..schemas.knowledge_graph import (
    CleanedDataUpdateRequest,
    CleanedDataUpdateResponse,
    LlmExtractionRequest,
    LlmExtractionResponse,
    ManualReviewBulkPagesUpdateRequest,
    ManualReviewBulkPagesUpdateResponse,
    ManualReviewPageUpdateRequest,
    ManualReviewPageUpdateResponse,
    ManualReviewStatusRequest,
    ManualReviewStatusResponse,
    ManualReviewStatusUpdateRequest,
    ManualReviewStatusUpdateResponse,
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
                "timestamp": get_current_timestamp_iso(),
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
        # Initialize document path
        document_path = get_loksabha_data_root() / request.document_path

        # Validate single document and get table pages (efficient, no ministry scanning)
        doc_info = validate_single_document_for_llm_extraction(document_path)
        table_pages = doc_info["table_pages"]

        # Use shared function with table pages (same as CLI)
        llm_state_data = process_single_document_for_llm_extraction(document_path, table_pages)

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


# ============================================================================
# MANUAL REVIEW ENDPOINTS
# ============================================================================


@router.patch(
    "/manual-review/page",
    response_model=ManualReviewPageUpdateResponse,
    summary="Update a single page in manual review",
    description="""
    Updates a single page during manual review. This endpoint:
    - Updates the specified page with new content (text, tables, flags)
    - Preserves all other pages in the current state
    - Tracks granular edit information (text_edited, tables_edited_ids)
    - Returns the complete updated state data
    
    The document must be in MANUAL_REVIEW state for this operation to succeed.
    """,
    responses={
        200: {
            "description": "Page updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "status": "IN_PROGRESS",
                            "processing_metadata": {"reviewer": "user123"},
                            "pages": {"1": {"text": "Updated content", "passed_review": False}},
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid request or not in manual review state",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot patch MANUAL_REVIEW - current state is LLM_EXTRACTION"}
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
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error updating page: Permission denied"}}},
        },
    },
)
async def update_manual_review_page(request: ManualReviewPageUpdateRequest):
    """
    Update a single page in manual review.

    Args:
        request (ManualReviewPageUpdateRequest): The request containing:
            - document_path: Path to the question document
            - page_number: Page number to update (1-based)
            - page_data: Complete page data with text, tables, flags, etc.

    Returns:
        ManualReviewPageUpdateResponse: Response containing:
            - status: Success status
            - data: Complete state data from question.progress.json

    Raises:
        HTTPException:
            - 400: If not in manual review state or invalid request
            - 404: If document doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize document progress handler
        document_path = get_loksabha_data_root() / request.document_path
        handler = DocumentProgressHandler(document_path)

        # Update the specific page
        handler.patch_manual_review_page(request.page_number, request.page_data)

        # Get the updated state data to return
        updated_data = handler.get_manual_review_data()

        return ManualReviewPageUpdateResponse(
            status="success",
            data=updated_data.model_dump() if hasattr(updated_data, "model_dump") else updated_data.__dict__,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating page: {str(e)}") from e


@router.patch(
    "/manual-review/status",
    response_model=ManualReviewStatusUpdateResponse,
    summary="Update manual review processing status",
    description="""
    Updates the processing status of the manual review state. This endpoint:
    - Changes the status (e.g., from IN_PROGRESS to SUCCESS)
    - Optionally updates processing metadata (reviewer info, completion time, etc.)
    - Triggers state transitions when status is set to SUCCESS
    - Returns the complete updated state data
    
    Setting status to SUCCESS will allow the document to progress to the next pipeline state.
    """,
    responses={
        200: {
            "description": "Status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "status": "SUCCESS",
                            "processing_metadata": {"reviewer": "user123", "completion_time": "2025-01-15T10:30:00Z"},
                            "pages": {"1": {"text": "Final content", "passed_review": True}},
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid request or not in manual review state",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot patch MANUAL_REVIEW status - current state is LLM_EXTRACTION"}
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
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error updating status: Permission denied"}}},
        },
    },
)
async def update_manual_review_status(request: ManualReviewStatusUpdateRequest):
    """
    Update manual review processing status.

    Args:
        request (ManualReviewStatusUpdateRequest): The request containing:
            - document_path: Path to the question document
            - status: New processing status (IN_PROGRESS, SUCCESS, etc.)
            - processing_metadata: Optional metadata for the status update

    Returns:
        ManualReviewStatusUpdateResponse: Response containing:
            - status: Success status
            - data: Complete state data from question.progress.json

    Raises:
        HTTPException:
            - 400: If not in manual review state or invalid request
            - 404: If document doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize document progress handler
        document_path = get_loksabha_data_root() / request.document_path
        handler = DocumentProgressHandler(document_path)

        # Update the status
        handler.patch_manual_review_status(request.status, request.processing_metadata)

        # Get the updated state data to return
        updated_data = handler.get_manual_review_data()

        return ManualReviewStatusUpdateResponse(
            status="success",
            data=updated_data.model_dump() if hasattr(updated_data, "model_dump") else updated_data.__dict__,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating status: {str(e)}") from e


@router.patch(
    "/manual-review/pages",
    response_model=ManualReviewBulkPagesUpdateResponse,
    summary="Update multiple pages in manual review",
    description="""
    Updates multiple pages during manual review in a single operation. This endpoint:
    - Updates all specified pages with new content
    - Preserves pages not included in the request
    - More efficient than multiple single-page updates
    - Returns the complete updated state data
    
    Use this endpoint when you need to update several pages at once for better performance.
    """,
    responses={
        200: {
            "description": "Pages updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "status": "IN_PROGRESS",
                            "processing_metadata": {"reviewer": "user123"},
                            "pages": {
                                "1": {"text": "Updated page 1", "passed_review": True},
                                "2": {"text": "Updated page 2", "passed_review": False},
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid request or not in manual review state",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot patch MANUAL_REVIEW - current state is LLM_EXTRACTION"}
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
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error updating pages: Permission denied"}}},
        },
    },
)
async def update_manual_review_bulk_pages(request: ManualReviewBulkPagesUpdateRequest):
    """
    Update multiple pages in manual review.

    Args:
        request (ManualReviewBulkPagesUpdateRequest): The request containing:
            - document_path: Path to the question document
            - pages_data: Dictionary mapping page numbers to page data

    Returns:
        ManualReviewBulkPagesUpdateResponse: Response containing:
            - status: Success status
            - data: Complete state data from question.progress.json

    Raises:
        HTTPException:
            - 400: If not in manual review state or invalid request
            - 404: If document doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize document progress handler
        document_path = get_loksabha_data_root() / request.document_path
        handler = DocumentProgressHandler(document_path)

        # Update multiple pages
        handler.patch_manual_review_bulk_pages(request.pages_data)

        # Get the updated state data to return
        updated_data = handler.get_manual_review_data()

        return ManualReviewBulkPagesUpdateResponse(
            status="success",
            data=updated_data.model_dump() if hasattr(updated_data, "model_dump") else updated_data.__dict__,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating pages: {str(e)}") from e


@router.get(
    "/manual-review/status",
    response_model=ManualReviewStatusResponse,
    summary="Get manual review status and data",
    description="""
    Retrieves the current manual review status and all page data. This endpoint:
    - Returns the complete manual review state data
    - Includes all pages with their current content and review status
    - Shows processing metadata and current status
    - Can be used to check progress or initialize a review interface
    
    Use this endpoint to load the current state when starting a manual review session.
    """,
    responses={
        200: {
            "description": "Status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "status": "IN_PROGRESS",
                            "processing_metadata": {"reviewer": "user123", "started_at": "2025-01-15T09:00:00Z"},
                            "pages": {
                                "1": {"text": "Page 1 content", "passed_review": True, "has_tables": False},
                                "2": {"text": "Page 2 content", "passed_review": False, "has_tables": True},
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Document not in manual review state",
            "content": {
                "application/json": {
                    "example": {"detail": "Document is not in MANUAL_REVIEW state, current state: LLM_EXTRACTION"}
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
            "description": "Internal server error",
            "content": {"application/json": {"example": {"detail": "Error retrieving status: Permission denied"}}},
        },
    },
)
async def get_manual_review_status(request: ManualReviewStatusRequest):
    """
    Get manual review status and data.

    Args:
        request (ManualReviewStatusRequest): The request containing:
            - document_path: Path to the question document

    Returns:
        ManualReviewStatusResponse: Response containing:
            - status: Success status
            - data: Complete manual review state data from question.progress.json

    Raises:
        HTTPException:
            - 400: If document is not in manual review state
            - 404: If document doesn't exist
            - 500: For other errors
    """
    try:
        # Initialize document progress handler
        document_path = get_loksabha_data_root() / request.document_path
        handler = DocumentProgressHandler(document_path)

        # Get the manual review data
        manual_review_data = handler.get_manual_review_data()

        if manual_review_data is None:
            raise ValueError("Document is not in MANUAL_REVIEW state or no manual review data available")

        return ManualReviewStatusResponse(
            status="success",
            data=manual_review_data.model_dump()
            if hasattr(manual_review_data, "model_dump")
            else manual_review_data.__dict__,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Document not found: {str(e)}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {str(e)}") from e
