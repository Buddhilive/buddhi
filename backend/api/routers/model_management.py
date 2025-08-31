"""
Model Management Router - Custom endpoints for model search, download, and status.

This router provides RESTful API endpoints for:
- Searching Hugging Face models
- Downloading models and tracking progress
- Getting download status
- Listing downloaded models

All endpoints require authentication.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field
from datetime import datetime

from backend.api.deps import user_dependency, db_dependency
from backend.services.model_manager import model_manager


# Pydantic models for request/response
class ModelSearchResponse(BaseModel):
    """Response model for model search results."""
    model_config = {"protected_namespaces": ()}
    
    id: str
    author: Optional[str] = None
    downloads: int = 0
    likes: int = 0
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    tags: List[str] = []
    pipeline_tag: Optional[str] = None
    library_name: Optional[str] = None
    model_type: str = "unknown"


class ModelDownloadRequest(BaseModel):
    """Request model for model download."""
    model_config = {"protected_namespaces": ()}
    
    model_name: str = Field(..., description="Name of the model to download (e.g., 'gpt2')")


class ModelDownloadResponse(BaseModel):
    """Response model for model download status."""
    status: str
    progress: int = 0
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None


class ModelStatusResponse(BaseModel):
    """Response model for model status."""
    status: str
    progress: int = 0
    message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    local_path: Optional[str] = None
    size_bytes: Optional[int] = None
    error: Optional[str] = None


class DownloadedModelResponse(BaseModel):
    """Response model for downloaded models list."""
    id: int
    name: str
    local_path: str
    status: str
    download_date: Optional[str] = None
    size_bytes: Optional[int] = None
    model_type: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    license: Optional[str] = None
    language: Optional[str] = None
    tags: List[str] = []
    downloads: Optional[int] = None
    likes: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Create router with authentication dependency
router = APIRouter(
    prefix="/models",
    tags=["model-management"],
    dependencies=[Depends(user_dependency)]  # All endpoints require authentication
)


@router.get("/search", response_model=List[ModelSearchResponse])
async def search_models(
    q: str = Query(..., description="Search query for models"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results (1-100)"),
    model_type: Optional[str] = Query(None, description="Filter by model type (e.g., 'text-generation')"),
    language: Optional[str] = Query(None, description="Filter by language (e.g., 'en')"),
    current_user: dict = Depends(user_dependency)
):
    """
    Search Hugging Face models by query string.
    
    Returns a list of models matching the search criteria, sorted by download count.
    """
    try:
        results = await model_manager.search_models(
            query=q,
            limit=limit,
            model_type=model_type,
            language=language
        )
        
        return [ModelSearchResponse(**result) for result in results]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching models: {str(e)}"
        )


@router.post("/download", response_model=ModelDownloadResponse)
async def download_model(
    request: ModelDownloadRequest,
    background_tasks: BackgroundTasks,
    db: db_dependency,
    current_user: dict = Depends(user_dependency)
):
    """
    Download a model from Hugging Face and cache it locally.
    
    The download happens in the background. Use the status endpoint to track progress.
    After successful download, model metadata is saved to the database.
    """
    try:
        # Validate model name
        if not request.model_name or not request.model_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model name cannot be empty"
            )
        
        model_name = request.model_name.strip()
        
        # Check if download is already in progress
        current_status = model_manager.get_download_status(model_name)
        if current_status.get("status") in ["starting", "downloading"]:
            return ModelDownloadResponse(**current_status)
        
        # Start download in background
        background_tasks.add_task(model_manager.download_model, model_name)
        
        # Return initial status
        status_info = model_manager.get_download_status(model_name)
        if status_info.get("status") == "not_started":
            status_info = {
                "status": "started",
                "progress": 0,
                "message": "Download queued",
                "started_at": datetime.now().isoformat()
            }
            
        return ModelDownloadResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating model download: {str(e)}"
        )


@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status(
    model_name: str = Query(..., description="Name of the model to check status for"),
    current_user: dict = Depends(user_dependency)
):
    """
    Get the download/progress status for a specific model.
    
    Returns the current status of the model download, including progress percentage
    and any error messages if the download failed.
    """
    try:
        if not model_name or not model_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model name cannot be empty"
            )
        
        status_info = model_manager.get_download_status(model_name.strip())
        
        return ModelStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model status: {str(e)}"
        )


@router.get("/", response_model=List[DownloadedModelResponse])
async def list_downloaded_models(
    current_user: dict = Depends(user_dependency)
):
    """
    List all models that have been successfully downloaded and are available for inference.
    
    Returns model metadata including local paths, download dates, sizes, and other details
    retrieved from the database.
    """
    try:
        models = model_manager.list_downloaded_models()
        
        return [DownloadedModelResponse(**model) for model in models]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing downloaded models: {str(e)}"
        )


@router.delete("/{model_name}")
async def delete_model(
    model_name: str,
    db: db_dependency,
    current_user: dict = Depends(user_dependency)
):
    """
    Delete a downloaded model from local cache and update database status.
    
    This removes the model files from local storage and marks the model as deleted
    in the database. The model can be re-downloaded later if needed.
    """
    try:
        # Implementation for model deletion can be added here
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Model deletion not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting model: {str(e)}"
        )
