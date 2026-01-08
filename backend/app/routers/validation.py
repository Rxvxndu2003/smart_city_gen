"""
Validation router - UDA compliance checking endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.validation_report import ValidationReport
from app.services.validation_service import validation_service
from app.services.ml_service import ml_service
from app.services.audit_service import AuditService
from app.schemas.validation import ValidationRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/check")
async def validate_project(
    request: ValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a project against UDA regulations.
    Creates a validation report in the database.
    """
    # Get project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_authorized = is_owner or any(role in ["Admin", "Architect", "Engineer", "Regulator"] for role in user_roles)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to validate this project"
        )
    
    try:
        # Prepare project data for validation
        project_data = {
            "site_area": float(project.site_area_m2) if project.site_area_m2 else 0,
            "project_type": project.project_type,
            "district": project.location_district or "COLOMBO",
            "setback_front": 3.0,
            "setback_side": 1.5,
            "setback_rear": 3.0,
            "building_footprint": float(project.building_coverage) if project.building_coverage else 0,
            "total_floor_area": float(project.site_area_m2 * project.floor_area_ratio) if project.site_area_m2 and project.floor_area_ratio else 0,
            "building_height": float(project.building_height) if project.building_height else 0,
            "open_space_area": float(project.site_area_m2 * project.open_space_percentage / 100) if project.site_area_m2 and project.open_space_percentage else 0,
            "parking_spaces": int(project.parking_spaces) if project.parking_spaces else 0,
            "floor_count": int(project.num_floors) if project.num_floors else 1
        }
        
        # Run UDA validation
        validation_result = validation_service.validate_project(project_data)
        
        # Get ML recommendations
        ml_recommendations = ml_service.get_project_recommendations(project_data)
        
        # Save validation report
        report = ValidationReport(
            project_id=request.project_id,
            report_type="UDA_COMPLIANCE",
            is_compliant=validation_result["is_compliant"],
            compliance_score=validation_result["compliance_score"],
            rule_checks=validation_result.get("detailed_results", []),
            recommendations=ml_recommendations.get("compliance_tips", []),
            ml_predictions={"validation": validation_result, "ml_recommendations": ml_recommendations},
            generated_by=current_user.id
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # Log audit
        AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_VALIDATED",
            resource_type="ValidationReport",
            resource_id=report.id,
            details={
                "project_id": request.project_id,
                "is_compliant": validation_result["is_compliant"],
                "score": validation_result["compliance_score"]
            }
        )
        
        logger.info(f"Validation completed for project {request.project_id} by user {current_user.email}")
        
        return {
            "report_id": report.id,
            "validation_result": validation_result,
            "ml_recommendations": ml_recommendations,
            "generated_at": report.generated_at
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error validating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/reports/{project_id}")
async def get_validation_reports(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all validation reports for a project."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get reports
    reports = db.query(ValidationReport).filter(
        ValidationReport.project_id == project_id
    ).order_by(ValidationReport.created_at.desc()).all()
    
    return {
        "project_id": project_id,
        "total_reports": len(reports),
        "reports": reports
    }


@router.get("/quick-check")
async def quick_compliance_check(
    site_area: float,
    project_type: str,
    district: str = "COLOMBO",
    current_user: User = Depends(get_current_user)
):
    """
    Quick compliance check without creating a project.
    Useful for preliminary assessments.
    """
    project_data = {
        "site_area": site_area,
        "project_type": project_type,
        "district": district,
        "setback_front": 3.0,
        "setback_side": 1.5,
        "setback_rear": 3.0,
        "building_footprint": site_area * 0.5,
        "total_floor_area": site_area * 2.0,
        "building_height": 15.0,
        "open_space_area": site_area * 0.15,
        "parking_spaces": int(site_area / 50),
        "floor_count": 5
    }
    
    validation_result = validation_service.validate_project(project_data)
    ml_recommendations = ml_service.get_project_recommendations(project_data)
    
    return {
        "validation_result": validation_result,
        "ml_recommendations": ml_recommendations
    }
