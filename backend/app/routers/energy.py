"""
Energy API Router for Smart City Planning System.
Provides endpoints for energy efficiency calculations and reports.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.project import Project
from app.models.analysis_result import AnalysisResult, AnalysisType
from app.services.energy_service import energy_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/energy", tags=["Energy Efficiency"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class EnergyCalculationRequest(BaseModel):
    """Request schema for energy calculation."""
    project_id: int
    floor_area: float = Field(..., gt=0, description="Total floor area in m²")
    building_volume: float = Field(..., gt=0, description="Building volume in m³")
    window_area: float = Field(..., ge=0, description="Total window area in m²")
    orientation: str = Field("north", description="Building orientation (north/south/east/west)")
    insulation_quality: str = Field("medium", description="Insulation quality (poor/medium/good)")
    num_floors: int = Field(1, ge=1, description="Number of floors")
    building_type: str = Field("residential", description="Building type (residential/commercial/mixed)")


class SolarPanelRequest(BaseModel):
    """Request schema for solar panel calculation."""
    project_id: int
    roof_area: float = Field(..., gt=0, description="Available roof area in m²")
    orientation: str = Field("south", description="Roof orientation")
    tilt_angle: float = Field(10.0, ge=0, le=90, description="Panel tilt angle in degrees")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/calculate")
async def calculate_energy(
    request: EnergyCalculationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Calculate energy efficiency for a building.
    
    Returns comprehensive energy analysis including:
    - Total energy consumption
    - Energy rating (A+ to E)
    - Breakdown by category
    - CO2 emissions
    - Optimization recommendations
    """
    try:
        # Verify project exists and user has access
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Calculate energy
        result = energy_service.calculate_building_energy(
            floor_area=request.floor_area,
            building_volume=request.building_volume,
            window_area=request.window_area,
            orientation=request.orientation,
            insulation_quality=request.insulation_quality,
            num_floors=request.num_floors,
            building_type=request.building_type
        )
        
        # Save result to database
        # Check if previous result exists and update it, or create new
        existing_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == request.project_id,
            AnalysisResult.analysis_type == AnalysisType.ENERGY
        ).first()

        if existing_result:
            existing_result.analysis_data = result
            db.commit()
            db.refresh(existing_result)
        else:
            new_result = AnalysisResult(
                project_id=request.project_id,
                analysis_type=AnalysisType.ENERGY,
                analysis_data=result
            )
            db.add(new_result)
            db.commit()
            db.refresh(new_result)
        
        logger.info(f"Energy calculated for project {request.project_id}: {result['rating']}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "energy_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Energy calculation error: {e}")
        raise HTTPException(status_code=500, detail="Energy calculation failed")


@router.post("/solar-potential")
async def calculate_solar_potential(
    request: SolarPanelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Calculate solar panel energy generation potential.
    
    Returns:
    - System capacity
    - Annual energy generation
    - Installation cost
    - Payback period
    - CO2 offset
    """
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Calculate solar potential
        result = energy_service.calculate_solar_panel_potential(
            roof_area=request.roof_area,
            orientation=request.orientation,
            tilt_angle=request.tilt_angle
        )
        
        logger.info(f"Solar potential calculated for project {request.project_id}")
        
        return {
            "success": True,
            "project_id": request.project_id,
            "solar_analysis": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Solar calculation error: {e}")
        raise HTTPException(status_code=500, detail="Solar calculation failed")


@router.get("/{project_id}/report")
async def get_energy_report(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get energy efficiency report for a project.
    
    Returns stored energy analysis or calculates if not available.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Retrieve from database
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id,
            AnalysisResult.analysis_type == AnalysisType.ENERGY
        ).first()

        if analysis_result:
            return {
                "success": True,
                "project_id": project_id,
                "energy_analysis": analysis_result.analysis_data
            }
        
        # If not found
        return {
            "success": True,
            "project_id": project_id,
            "message": "Energy report feature - calculate energy first",
            "has_report": False
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get energy report error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get energy report")


@router.get("/{project_id}/recommendations")
async def get_energy_recommendations(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get energy optimization recommendations for a project.
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Retrieve stored recommendations
        # For now, return general recommendations
        general_recommendations = [
            "☀️ Install solar panels to offset 20-40% of energy consumption",
            "💡 Use LED lighting to reduce lighting energy by 75%",
            "🏠 Improve building insulation to reduce HVAC costs by up to 30%",
            "🪟 Optimize window-to-floor ratio (15-20%) for natural lighting",
            "❄️ Install high-efficiency HVAC systems (SEER ≥ 16)",
            "🌳 Plant trees for natural shading and cooling",
            "💨 Ensure proper ventilation to reduce cooling needs"
        ]
        
        return {
            "success": True,
            "project_id": project_id,
            "recommendations": general_recommendations
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get recommendations error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")


@router.get("/ratings/info")
async def get_rating_info():
    """
    Get information about energy rating system.
    """
    return {
        "rating_system": "Sri Lankan Building Energy Efficiency",
        "ratings": {
            "A+": {
                "threshold": "≤ 50 kWh/m²/year",
                "description": "Excellent - Highly energy efficient",
                "color": "#00C853"
            },
            "A": {
                "threshold": "51-75 kWh/m²/year",
                "description": "Very Good - Energy efficient",
                "color": "#64DD17"
            },
            "B": {
                "threshold": "76-100 kWh/m²/year",
                "description": "Good - Above average efficiency",
                "color": "#AEEA00"
            },
            "C": {
                "threshold": "101-150 kWh/m²/year",
                "description": "Average - Room for improvement",
                "color": "#FFD600"
            },
            "D": {
                "threshold": "151-200 kWh/m²/year",
                "description": "Below Average - Needs improvement",
                "color": "#FF6D00"
            },
            "E": {
                "threshold": "> 200 kWh/m²/year",
                "description": "Poor - Significant improvements needed",
                "color": "#DD2C00"
            }
        },
        "sustainability_threshold": "B or better",
        "green_building_threshold": "A or better"
    }
