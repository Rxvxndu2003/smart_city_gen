"""
Projects router - Project management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=dict)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all projects accessible to the current user.
    Admins see all, others see only their own projects.
    Excludes cancelled projects by default.
    """
    # Exclude cancelled projects by default
    query = db.query(Project).filter(Project.status != ProjectStatus.CANCELLED)
    
    # Get user roles - access role.name from the role relationship
    user_roles = [user_role.role.name for user_role in current_user.user_roles]
    
    # Filter by ownership unless admin
    if "Admin" not in user_roles and "Regulator" not in user_roles:
        query = query.filter(Project.owner_id == current_user.id)
    
    # Filter by status if provided
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.offset(skip).limit(limit).all()
    
    # Convert to dict and add district field as alias
    result = []
    for project in projects:
        project_dict = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "district": project.location_district,
            "status": project.status.value if hasattr(project.status, 'value') else project.status,
            "site_area": float(project.site_area_m2) if project.site_area_m2 else 0,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "owner_name": project.owner_name
        }
        result.append(project_dict)
    
    return {"projects": result}


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project.
    Available to ProjectOwner, Architect, and Admin roles.
    """
    # Check if user has permission to create projects
    user_roles = [ur.role.name for ur in current_user.user_roles]
    allowed_roles = ["Admin", "ProjectOwner", "Architect"]
    
    if not any(role in allowed_roles for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create projects"
        )
    
    try:
        # Create project instance
        project = Project(
            name=project_data.name,
            description=project_data.description,
            project_type=project_data.project_type,
            location_address=project_data.location_address,
            location_district=project_data.district or project_data.location_district,
            location_city=project_data.location_city,
            location_coordinates=project_data.location_coordinates,
            site_area_m2=project_data.site_area or project_data.site_area_m2,
            uda_zone=project_data.uda_zone,
            building_coverage=project_data.building_coverage,
            floor_area_ratio=project_data.floor_area_ratio,
            num_floors=project_data.num_floors,
            building_height=project_data.building_height,
            open_space_percentage=project_data.open_space_percentage,
            parking_spaces=project_data.parking_spaces,
            owner_name=project_data.owner_name,
            # Urban Planning Parameters
            residential_percentage=project_data.residential_percentage,
            commercial_percentage=project_data.commercial_percentage,
            industrial_percentage=project_data.industrial_percentage,
            green_space_percentage_plan=project_data.green_space_percentage,
            road_network_type=project_data.road_network_type,
            main_road_width=project_data.main_road_width,
            secondary_road_width=project_data.secondary_road_width,
            pedestrian_path_width=project_data.pedestrian_path_width,
            target_population=project_data.target_population,
            population_density=project_data.population_density,
            average_household_size=project_data.average_household_size,
            climate_zone=project_data.climate_zone,
            sustainability_rating=project_data.sustainability_rating,
            renewable_energy_target=project_data.renewable_energy_target,
            water_management_strategy=project_data.water_management_strategy,
            owner_id=current_user.id,
            status=ProjectStatus.DRAFT
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        # Log audit
        AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_CREATED",
            resource_type="Project",
            resource_id=project.id,
            details={"name": project.name, "project_type": project.project_type}
        )
        
        logger.info(f"Project created: {project.id} by user {current_user.email}")
        return project
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/statistics")
async def get_project_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project statistics and analytics."""
    try:
        # Get user roles
        user_roles = [user_role.role.name for user_role in current_user.user_roles]
        is_admin = "Admin" in user_roles or "Regulator" in user_roles
        
        # Base query - filter by user if not admin, exclude CANCELLED projects
        query = db.query(Project).filter(Project.status != ProjectStatus.CANCELLED)
        if not is_admin:
            query = query.filter(Project.owner_id == current_user.id)
        
        # Total projects (excluding cancelled)
        total_projects = query.count()
        
        # Projects by status (excluding cancelled)
        status_filter = Project.status != ProjectStatus.CANCELLED
        if not is_admin:
            status_filter = (status_filter) & (Project.owner_id == current_user.id)
        
        status_counts = db.query(
            Project.status, func.count(Project.id)
        ).filter(status_filter).group_by(Project.status).all()
        
        # Convert enum to string for JSON serialization
        projects_by_status = {status.value if hasattr(status, 'value') else str(status): count for status, count in status_counts}
        
        # Projects by type (excluding cancelled)
        type_filter = Project.status != ProjectStatus.CANCELLED
        if not is_admin:
            type_filter = (type_filter) & (Project.owner_id == current_user.id)
        
        type_counts = db.query(
            Project.project_type, func.count(Project.id)
        ).filter(type_filter).group_by(Project.project_type).all()
        
        projects_by_type = [
            {"type": ptype or "Unknown", "count": count, "fill": _get_color_for_type(ptype)}
            for ptype, count in type_counts
        ]
        
        # Projects by district (excluding cancelled)
        district_filter = Project.status != ProjectStatus.CANCELLED
        if not is_admin:
            district_filter = (district_filter) & (Project.owner_id == current_user.id)
        
        district_counts = db.query(
            Project.location_district, func.count(Project.id)
        ).filter(district_filter).group_by(Project.location_district).all()
        
        projects_by_district = [
            {"district": district or "Unknown", "count": count}
            for district, count in district_counts
        ]
        
        # Projects over time (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        projects_over_time = []
        
        for i in range(6):
            month_start = six_months_ago + timedelta(days=30 * i)
            month_end = month_start + timedelta(days=30)
            count = query.filter(
                Project.created_at >= month_start,
                Project.created_at < month_end
            ).count()
            projects_over_time.append({
                "month": month_start.strftime("%b"),
                "projects": count
            })
        
        # Calculate actual compliance metrics from ML predictions
        # Count projects that are predicted as compliant
        compliant_filter = (Project.status != ProjectStatus.CANCELLED)
        if not is_admin:
            compliant_filter = compliant_filter & (Project.owner_id == current_user.id)
        
        compliant_count = db.query(Project).filter(
            compliant_filter,
            Project.predicted_compliance == 1
        ).count()
        
        # Calculate average compliance score from all projects with predictions
        avg_score_result = db.query(
            func.avg(Project.compliance_score)
        ).filter(
            compliant_filter,
            Project.compliance_score.isnot(None)
        ).scalar()
        
        # Convert to percentage (compliance_score is 0.0-1.0, we want 0-100)
        avg_compliance_score = round(float(avg_score_result or 0) * 100, 1)
        
        # Compliance rate: percentage of projects that are compliant
        compliance_rate = (compliant_count / total_projects * 100) if total_projects > 0 else 0
        
        return {
            "total_projects": total_projects,
            "projects_by_status": projects_by_status,
            "projects_by_type": projects_by_type,
            "projects_by_district": projects_by_district,
            "projects_over_time": projects_over_time,
            "compliant_projects": compliant_count,
            "compliance_rate": round(compliance_rate, 1),
            "avg_compliance_score": avg_compliance_score,
            "pending_approvals": projects_by_status.get("UNDER_ARCHITECT_REVIEW", 0) + projects_by_status.get("UNDER_ENGINEER_REVIEW", 0),
        }
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_admin_or_regulator = "Admin" in user_roles or "Regulator" in user_roles
    
    if not (is_owner or is_admin_or_regulator):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this project"
        )
    
    # Create response with backward compatibility aliases
    response_data = ProjectResponse.model_validate(project)
    response_dict = response_data.model_dump()
    response_dict['district'] = project.location_district
    response_dict['site_area'] = project.site_area_m2
    
    return response_dict


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project details."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions - only owner or admin can update
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_admin = "Admin" in user_roles
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project"
        )
    
    try:
        # Update fields
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        # Log audit
        AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_UPDATED",
            resource_type="Project",
            resource_id=project.id,
            details={"updated_fields": list(update_data.keys())}
        )
        
        logger.info(f"Project updated: {project.id} by user {current_user.email}")
        return project
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.patch("/{project_id}/status")
async def update_project_status(
    project_id: int,
    new_status: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update project status. 
    Owner can submit for review (DRAFT -> UNDER_ARCHITECT_REVIEW).
    Admins can set any status.
    Automatically logs to blockchain on SUBMISSION.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_admin = "Admin" in user_roles
    
    # Validate status value
    try:
        status_enum = ProjectStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {[s.value for s in ProjectStatus]}"
        )
    
    # Permission logic
    if is_owner:
        # Owners can submit for review from DRAFT or REJECTED status
        if (project.status == ProjectStatus.DRAFT and status_enum == ProjectStatus.UNDER_ARCHITECT_REVIEW) or \
           (project.status == ProjectStatus.REJECTED and status_enum == ProjectStatus.UNDER_ARCHITECT_REVIEW):
            project.status = status_enum
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only submit DRAFT or REJECTED projects for review"
            )
    elif is_admin:
        # Admins can set any status
        project.status = status_enum
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this project's status"
        )
    
    try:
        # Update status
        old_status = project.status
        project.status = status_enum
        
        db.commit()
        db.refresh(project)
        
        # Log audit
        AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_STATUS_UPDATED",
            resource_type="Project",
            resource_id=project.id,
            details={"new_status": new_status}
        )

        # AUTO-LOG: If submitting for review, log to blockchain
        if new_status == "UNDER_ARCHITECT_REVIEW":
            from app.utils.blockchain_utils import store_project_record_background
            
            # Prepare data snapshot
            project_data = {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "project_type": project.project_type,
                "status": new_status,
                "location_address": project.location_address,
                "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else 0,
                "owner": project.owner_name,
                "submitted_at": datetime.utcnow().isoformat()
            }
            
            background_tasks.add_task(
                store_project_record_background,
                project_data=project_data,
                record_type="SUBMISSION_HASH",
                user_id=current_user.id,
                metadata={"action": "SUBMIT_FOR_REVIEW", "previous_status": old_status.value}
            )
        
        return {
            "project_id": project.id,
            "status": project.status.value,
            "message": "Project status updated successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating project status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating status: {str(e)}"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project (soft delete by setting status to CANCELLED)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions - only owner or admin can delete
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_admin = "Admin" in user_roles
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this project"
        )
    
    try:
        # Soft delete - set status to CANCELLED
        project.status = ProjectStatus.CANCELLED
        db.commit()
        
        # Log audit
        AuditService.log_action(
            db=db,
            user_id=current_user.id,
            action="PROJECT_DELETED",
            resource_type="Project",
            resource_id=project.id,
            details={"name": project.name}
        )
        
        logger.info(f"Project deleted: {project.id} by user {current_user.email}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


def _get_color_for_type(project_type: str) -> str:
    """Get color for project type in charts."""
    colors = {
        "RESIDENTIAL": "#3b82f6",
        "COMMERCIAL": "#10b981",
        "MIXED_USE": "#f59e0b",
        "INDUSTRIAL": "#ef4444",
        "INSTITUTIONAL": "#8b5cf6",
    }
    return colors.get(project_type, "#6b7280")
