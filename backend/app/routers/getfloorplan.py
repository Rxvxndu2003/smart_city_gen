"""
GetFloorPlan API Router

Endpoints for uploading floor plans and generating 3D renders and 360° virtual tours
using the GetFloorPlan AI API.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
import os
import tempfile
from pathlib import Path

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.services.getfloorplan_service import getfloorplan_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/getfloorplan",
    tags=["GetFloorPlan AI"],
    responses={404: {"description": "Not found"}}
)


# Pydantic Models
class FloorPlanUploadResponse(BaseModel):
    """Response after uploading a floor plan"""
    success: bool
    message: str
    plan_id: Optional[int] = Field(None, description="CRM Plan ID from GetFloorPlan API")
    estimated_time: str = Field(default="30-120 minutes", description="Estimated processing time")


class PlanStatusRequest(BaseModel):
    """Request to check plan status"""
    plan_ids: List[int] = Field(..., description="List of plan IDs to check")
    language: str = Field(default="en", description="Language for results")


class PlanAssets(BaseModel):
    """Plan assets and generated files"""
    status: int = Field(..., description="0 = not ready, 1 = ready")
    svg: List[str] = Field(default=[], description="SVG file URLs")
    jpg: List[str] = Field(default=[], description="JPG file URLs")
    widget_link: Optional[str] = Field(None, description="360° virtual tour widget link")
    neural_json: Optional[str] = Field(None, description="Neural network processing data")
    furniture_json: Optional[str] = Field(None, description="Furniture placement data")
    unreal3d: List[str] = Field(default=[], description="Unreal Engine 3D assets")
    canvas: Optional[str] = Field(None, description="Canvas data")


class PlanStatusResponse(BaseModel):
    """Response with plan status and assets"""
    success: bool
    message: str
    results: List[PlanAssets] = []


class TourUrlResponse(BaseModel):
    """Response with 360° tour URL"""
    success: bool
    message: str
    widget_link: Optional[str] = None
    plan_id: int


@router.post("/upload-plan", response_model=FloorPlanUploadResponse)
async def upload_floor_plan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Floor plan image (PNG, JPG, etc.)"),
    use_3d: bool = Form(default=True, description="Generate 3D renders and 360° tours"),
    language: str = Form(default="en", description="Language for generated content"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a floor plan to GetFloorPlan AI for processing.
    
    This endpoint:
    1. Accepts a floor plan image file
    2. Uploads it to GetFloorPlan AI API
    3. Returns a plan ID for tracking
    4. Processing happens asynchronously (30-120 minutes)
    
    Use the /check-plan-status endpoint to monitor progress.
    """
    try:
        logger.info(f"User {current_user.email} uploading floor plan: {file.filename}")
        
        # Validate file type
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Upload to GetFloorPlan API
            plan_id = await getfloorplan_service.upload_floorplan(
                file_path=temp_path,
                use_3d=use_3d,
                language=language
            )
            
            if plan_id:
                logger.info(f"Floor plan uploaded successfully. Plan ID: {plan_id}")
                
                return FloorPlanUploadResponse(
                    success=True,
                    message="Floor plan uploaded successfully. Processing will take 30-120 minutes.",
                    plan_id=plan_id,
                    estimated_time="30-120 minutes"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to upload floor plan to GetFloorPlan API"
                )
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading floor plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading floor plan: {str(e)}")


@router.post("/check-plan-status", response_model=PlanStatusResponse)
async def check_plan_status(
    request: PlanStatusRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Check the processing status of one or more floor plans.
    
    Returns:
    - status = 0: Plan is still processing (not ready)
    - status = 1: Plan is ready with all generated assets
    
    When ready, response includes:
    - SVG and JPG rendered floor plans
    - 360° virtual tour widget link
    - 3D assets for Unreal Engine
    - Furniture placement data
    - Neural network processing data
    """
    try:
        logger.info(f"User {current_user.email} checking status for plans: {request.plan_ids}")
        
        results = await getfloorplan_service.check_plan_status(
            plan_ids=request.plan_ids,
            language=request.language
        )
        
        if results is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to check plan status"
            )
        
        # Convert results to response format
        plan_assets = []
        for result in results:
            plan_assets.append(PlanAssets(
                status=result.get('status', 0),
                svg=result.get('svg', []),
                jpg=result.get('jpg', []),
                widget_link=result.get('widgetLink'),
                neural_json=result.get('neuralJson'),
                furniture_json=result.get('furnitureJson'),
                unreal3d=result.get('unreal3d', []),
                canvas=result.get('canvas')
            ))
        
        ready_count = sum(1 for p in plan_assets if p.status == 1)
        total_count = len(plan_assets)
        
        return PlanStatusResponse(
            success=True,
            message=f"{ready_count}/{total_count} plans ready",
            results=plan_assets
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking plan status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking plan status: {str(e)}")


@router.get("/get-360-tour/{plan_id}", response_model=TourUrlResponse)
async def get_360_tour_url(
    plan_id: int,
    wait: bool = False,
    language: str = "en",
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the 360° virtual tour widget URL for a specific floor plan.
    
    Parameters:
    - plan_id: The CRM Plan ID returned from upload
    - wait: If True, waits for plan completion (up to 2 hours). If False, returns immediately.
    - language: Language for tour content (default: "en")
    
    Returns the widget link URL that can be embedded in an iframe.
    """
    try:
        logger.info(f"User {current_user.email} requesting 360° tour for plan {plan_id}")
        
        widget_link = await getfloorplan_service.get_360_tour_url(
            plan_id=plan_id,
            wait=wait,
            language=language
        )
        
        if widget_link:
            return TourUrlResponse(
                success=True,
                message="360° tour ready",
                widget_link=widget_link,
                plan_id=plan_id
            )
        else:
            # Check if plan exists but is not ready
            results = await getfloorplan_service.check_plan_status([plan_id], language)
            
            if results and len(results) > 0:
                status = results[0].get('status', 0)
                if status == 0:
                    return TourUrlResponse(
                        success=False,
                        message="Plan is still processing. Please try again later.",
                        widget_link=None,
                        plan_id=plan_id
                    )
            
            raise HTTPException(
                status_code=404,
                detail=f"360° tour not available for plan {plan_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting 360° tour URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting 360° tour: {str(e)}")


@router.get("/get-rendered-images/{plan_id}")
async def get_rendered_images(
    plan_id: int,
    wait: bool = False,
    language: str = "en",
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all rendered image URLs for a floor plan.
    
    Returns SVG, JPG, and Unreal 3D asset URLs.
    """
    try:
        logger.info(f"User {current_user.email} requesting rendered images for plan {plan_id}")
        
        images = await getfloorplan_service.get_rendered_images(
            plan_id=plan_id,
            wait=wait,
            language=language
        )
        
        if images and (images['svg'] or images['jpg'] or images['unreal3d']):
            return {
                "success": True,
                "message": "Rendered images retrieved",
                "plan_id": plan_id,
                "images": images
            }
        else:
            return {
                "success": False,
                "message": "No images available yet. Plan may still be processing.",
                "plan_id": plan_id,
                "images": {'svg': [], 'jpg': [], 'unreal3d': []}
            }
    
    except Exception as e:
        logger.error(f"Error getting rendered images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting images: {str(e)}")


@router.get("/get-full-data/{plan_id}")
async def get_full_plan_data(
    plan_id: int,
    wait: bool = False,
    language: str = "en",
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete plan data including all generated assets.
    
    Returns everything: images, 360° tour, furniture data, neural data, etc.
    """
    try:
        logger.info(f"User {current_user.email} requesting full data for plan {plan_id}")
        
        plan_data = await getfloorplan_service.get_full_plan_data(
            plan_id=plan_id,
            wait=wait,
            language=language
        )
        
        if plan_data:
            return {
                "success": True,
                "message": "Plan data retrieved",
                "plan_id": plan_id,
                "data": plan_data
            }
        else:
            return {
                "success": False,
                "message": "Plan data not available",
                "plan_id": plan_id,
                "data": None
            }
    
    except Exception as e:
        logger.error(f"Error getting full plan data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting plan data: {str(e)}")
