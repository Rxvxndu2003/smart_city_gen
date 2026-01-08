"""
Green Space API Router for Smart City Planning System.
Provides endpoints for green space optimization and environmental analysis.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.analysis_result import AnalysisResult, AnalysisType
from app.services.green_space_service import green_space_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/green-space", tags=["Green Space Optimization"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class GreenSpaceRequest(BaseModel):
    """Request schema for green space calculation."""
    project_id: int
    total_area: float = Field(..., gt=0, description="Total project area in m²")
    building_type: str = Field("residential", description="Development type")
    num_buildings: int = Field(1, ge=1, description="Number of buildings")
    building_footprint: float = Field(0, ge=0, description="Total building footprint in m²")


class HeatIslandRequest(BaseModel):
    """Request schema for urban heat island analysis."""
    project_id: int
    green_space_percentage: float = Field(..., ge=0, le=100)
    building_density: float = Field(..., ge=0, le=100)
    pavement_area: float = Field(..., ge=0)
    total_area: float = Field(..., gt=0)


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/calculate")
async def calculate_green_space(
    request: GreenSpaceRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Calculate green space requirements and optimization.
    
    Returns comprehensive green space analysis including:
    - UDA compliance check
    - Park placement optimization
    - Tree coverage requirements
    - Environmental benefits
    - Sustainability recommendations
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Calculate green space
        result = green_space_service.calculate_green_space_requirements(
            total_area=request.total_area,
            building_type=request.building_type,
            num_buildings=request.num_buildings,
            building_footprint=request.building_footprint
        )
        
        # Save result to database
        # Check if previous result exists and update it, or create new
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == request.project_id,
            AnalysisResult.analysis_type == AnalysisType.GREEN_SPACE
        ).first()

        if existing_result:
            existing_result.analysis_data = result
            db.commit()
            db.refresh(existing_result)
        else:
            new_result = AnalysisResult(
                project_id=request.project_id,
                analysis_type=AnalysisType.GREEN_SPACE,
                analysis_data=result
            )
            db.add(new_result)
            db.commit()
            db.refresh(new_result)
        
        logger.info(f"Green space calculated for project {request.project_id}: {result['compliance_status']}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "green_space_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Green space calculation error: {e}")
        raise HTTPException(status_code=500, detail="Green space calculation failed")


@router.post("/heat-island")
async def analyze_heat_island(
    request: HeatIslandRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze urban heat island effect and mitigation strategies.
    
    Returns heat island analysis with mitigation recommendations.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Calculate heat island effect
        result = green_space_service.calculate_urban_heat_island_effect(
            green_space_percentage=request.green_space_percentage,
            building_density=request.building_density,
            pavement_area=request.pavement_area,
            total_area=request.total_area
        )
        
        logger.info(f"Heat island analysis for project {request.project_id}: {result['severity']}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "heat_island_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Heat island analysis error: {e}")
        raise HTTPException(status_code=500, detail="Heat island analysis failed")


@router.get("/{project_id}/report")
async def get_green_space_report(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get green space report for a project.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Retrieve from database
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.analysis_type == AnalysisType.GREEN_SPACE
        ).first()

        if analysis_result:
            return {
                "success": True,
                "project_id": project_id,
                "green_space_analysis": analysis_result.analysis_data
            }
        
        # If not found
        return {
            "success": True,
            "project_id": project_id,
            "message": "Green space report - calculate green space first",
            "has_report": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get green space report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get green space report")


@router.get("/requirements/info")
async def get_requirements_info():
    """
    Get information about green space requirements and standards.
    """
    return {
        "standards": "UDA Sri Lanka + Sustainable Urban Planning Guidelines",
        "minimum_requirements": {
            "residential": "15% of total area",
            "commercial": "10% of total area",
            "mixed_use": "12.5% of total area"
        },
        "recommended": "20% for sustainable development",
        "tree_coverage": {
            "minimum": "40 trees per hectare",
            "recommended": "80 trees per hectare"
        },
        "environmental_benefits": {
            "temperature_reduction": "0.5°C per 10% green space",
            "co2_absorption": "22 kg per tree per year",
            "air_quality": "Significant improvement with adequate coverage",
            "biodiversity": "Enhanced with native species"
        },
        "park_types": {
            "community_park": "> 2000 m²",
            "neighborhood_park": "500-2000 m²",
            "pocket_park": "< 500 m²"
        }
    }
