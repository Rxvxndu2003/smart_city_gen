"""
Structural Integrity API Router for Smart City Planning System.
Provides endpoints for structural validation and safety checks.
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
from app.services.structural_service import structural_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/structural", tags=["Structural Integrity"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class StructuralValidationRequest(BaseModel):
    """Request schema for structural validation."""
    project_id: int
    building_height: float = Field(..., gt=0, description="Building height in meters")
    num_floors: int = Field(..., ge=1, description="Number of floors")
    floor_area: float = Field(..., gt=0, description="Floor area per floor in m²")
    building_type: str = Field("residential", description="Building type")
    location_zone: str = Field("low", description="Seismic/wind zone (low/medium/high)")
    foundation_type: str = Field("shallow", description="Foundation type")
    material: str = Field("concrete", description="Primary construction material")
    wall_thickness: float = Field(0.23, gt=0, description="Wall thickness in meters")


class ColumnValidationRequest(BaseModel):
    """Request schema for column validation."""
    project_id: int
    column_height: float = Field(..., gt=0, description="Column height in meters")
    axial_load: float = Field(..., gt=0, description="Axial load in kN")
    column_size: float = Field(0.3, gt=0, description="Column size in meters (square)")
    material: str = Field("concrete", description="Column material")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/validate")
async def validate_structural_integrity(
    request: StructuralValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate structural integrity of a building.
    
    Returns comprehensive structural analysis including:
    - Load calculations (dead, live, wind, seismic)
    - Safety factor
    - Foundation requirements
    - Structural recommendations
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate structure
        result = structural_service.validate_structural_integrity(
            building_height=request.building_height,
            num_floors=request.num_floors,
            floor_area=request.floor_area,
            building_type=request.building_type,
            location_zone=request.location_zone,
            foundation_type=request.foundation_type,
            material=request.material,
            wall_thickness=request.wall_thickness
        )
        
        # Save result to database
        # Check if previous result exists and update it, or create new
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == request.project_id,
            AnalysisResult.analysis_type == AnalysisType.STRUCTURAL
        ).first()

        if existing_result:
            existing_result.analysis_data = result
            db.commit()
            db.refresh(existing_result)
        else:
            new_result = AnalysisResult(
                project_id=request.project_id,
                analysis_type=AnalysisType.STRUCTURAL,
                analysis_data=result
            )
            db.add(new_result)
            db.commit()
            db.refresh(new_result)
        
        logger.info(f"Structural validation for project {request.project_id}: {result['validation_status']}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "structural_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Structural validation error: {e}")
        raise HTTPException(status_code=500, detail="Structural validation failed")


@router.post("/validate-column")
async def validate_column(
    request: ColumnValidationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate column design for axial load.
    
    Returns column safety analysis.
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate column
        result = structural_service.validate_column_design(
            column_height=request.column_height,
            axial_load=request.axial_load,
            column_size=request.column_size,
            material=request.material
        )
        
        logger.info(f"Column validation for project {request.project_id}: {result['recommendation']}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "column_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Column validation error: {e}")
        raise HTTPException(status_code=500, detail="Column validation failed")


@router.get("/{project_id}/report")
async def get_structural_report(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get structural integrity report for a project.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Retrieve from database
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.analysis_type == AnalysisType.STRUCTURAL
        ).first()

        if analysis_result:
            return {
                "success": True,
                "project_id": project_id,
                "structural_analysis": analysis_result.analysis_data
            }
        
        return {
            "success": True,
            "project_id": project_id,
            "message": "Structural report feature - validate structure first",
            "has_report": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get structural report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get structural report")


@router.get("/{project_id}/safety-factor")
async def get_safety_factor(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get safety factor for a project.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Retrieve from database
        return {
            "success": True,
            "project_id": project_id,
            "message": "Safety factor - validate structure first",
            "has_data": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get safety factor error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get safety factor")


@router.get("/standards/info")
async def get_standards_info():
    """
    Get information about structural standards and safety factors.
    """
    return {
        "standards": "Sri Lankan Building Code + International Standards",
        "safety_factors": {
            "minimum": 2.0,
            "recommended": 2.5,
            "description": "Ratio of material strength to applied load"
        },
        "load_factors": {
            "dead_load": 1.4,
            "live_load": 1.6,
            "wind_load": 1.6,
            "seismic_load": 1.5
        },
        "seismic_zones": {
            "low": "Most of Sri Lanka (PGA: 0.05g)",
            "medium": "Some coastal areas (PGA: 0.10g)",
            "high": "Specific locations (PGA: 0.15g)"
        },
        "wind_zones": {
            "low": "Inland areas (30 m/s)",
            "medium": "Most coastal areas (35 m/s)",
            "high": "Exposed coastal areas (40 m/s)"
        },
        "materials": {
            "concrete": "M25 grade (25 MPa)",
            "brick": "Standard masonry (10 MPa)",
            "steel": "Structural steel (250 MPa)"
        }
    }
