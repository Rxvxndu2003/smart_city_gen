"""
Approvals router - Project approval workflow endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.services.approval_service import approval_service
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()
audit_service = AuditService()


class ApprovalActionRequest(BaseModel):
    """Request to approve or reject a project."""
    project_id: int
    action: str  # "approve" or "reject"
    comment: Optional[str] = None


class AssignmentRequest(BaseModel):
    """Request to assign a project for review."""
    project_id: int
    assigned_to_id: int
    assigned_role: str


@router.post("/approve")
async def approve_project(
    request: ApprovalActionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a project.
    Creates approval record and updates project status.
    Automatically logs to blockchain on APPROVAL/REJECTION.
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
    is_authorized = any(role in ["Admin", "Architect", "Engineer", "Regulator"] for role in user_roles)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to approve/reject projects"
        )
    
    try:
        # Determine target status
        status_from = project.status
        if request.action.lower() == "approve":
            status_to = ProjectStatus.APPROVED
            record_type = "APPROVAL_HASH"
        elif request.action.lower() == "reject":
            status_to = ProjectStatus.REJECTED
            record_type = "REJECTION_HASH"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'"
            )
        
        # Get user's primary role
        user_role = user_roles[0] if user_roles else "Unknown"
        
        # Create approval record
        approval = approval_service.create_approval_record(
            project_id=request.project_id,
            user_id=current_user.id,
            user_role=user_role,
            status_from=status_from,
            status_to=status_to,
            comment=request.comment,
            db=db,
            is_admin_override="Admin" in user_roles
        )
        
        # Audit log
        audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action=f"PROJECT_{request.action.upper()}",
            resource_type="project",
            resource_id=request.project_id,
            details={"approval_id": approval.id, "comment": request.comment}
        )

        # AUTO-LOG: Log to blockchain in background
        from app.utils.blockchain_utils import store_project_record_background
        from datetime import datetime
        
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "status": status_to.value,
            "location_address": project.location_address,
            "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else 0,
            "approved_by": current_user.full_name,
            "approved_at": datetime.utcnow().isoformat(),
            "approval_comment": request.comment or ""
        }
        
        background_tasks.add_task(
            store_project_record_background,
            project_data=project_data,
            record_type=record_type,
            user_id=current_user.id,
            metadata={
                "action": f"PROJECT_{request.action.upper()}", 
                "approved_by_role": user_role,
                "approval_id": approval.id
            }
        )
        
        return {
            "approval_id": approval.id,
            "project_id": project.id,
            "status": status_to.value,
            "message": f"Project {request.action}d successfully"
        }
    
    except Exception as e:
        logger.error(f"Error processing approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing approval: {str(e)}"
        )


@router.post("/assign")
async def assign_for_review(
    request: AssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a project to a user for review.
    Only admins and regulators can assign reviews.
    """
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_authorized = any(role in ["Admin", "Regulator"] for role in user_roles)
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and regulators can assign reviews"
        )
    
    try:
        assignment = approval_service.create_approval_assignment(
            project_id=request.project_id,
            assigned_to_id=request.assigned_to_id,
            assigned_role=request.assigned_role,
            assigned_by_id=current_user.id,
            db=db
        )
        
        return {
            "assignment_id": assignment.id,
            "project_id": request.project_id,
            "assigned_to": request.assigned_to_id,
            "message": "Review assignment created successfully"
        }
    
    except Exception as e:
        logger.error(f"Error creating assignment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating assignment: {str(e)}"
        )


@router.get("/pending")
async def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all projects pending approval based on user role.
    Shows assigned projects OR all projects needing review if user is a reviewer.
    """
    try:
        user_roles = [ur.role.name for ur in current_user.user_roles]
        
        # First get assigned projects
        assigned = approval_service.get_pending_assignments(
            user_id=current_user.id,
            db=db
        )
        
        # If user is a reviewer, also get unassigned projects that need review
        unassigned = []
        if any(role in ["Admin", "Architect", "Engineer", "Regulator"] for role in user_roles):
            # Get projects that are under review but not yet approved/rejected
            review_statuses = [
                ProjectStatus.UNDER_ARCHITECT_REVIEW,
                ProjectStatus.UNDER_ENGINEER_REVIEW,
                ProjectStatus.UNDER_REGULATOR_REVIEW
            ]
            
            projects_needing_review = db.query(Project).filter(
                Project.status.in_(review_statuses)
            ).all()
            
            # Convert to format matching assignments
            for project in projects_needing_review:
                # Check if already assigned
                is_assigned = any(a['project_id'] == project.id for a in assigned)
                if not is_assigned:
                    unassigned.append({
                        "assignment_id": None,  # Not assigned yet
                        "project_id": project.id,
                        "project_name": project.name,
                        "project_type": project.project_type,
                        "district": project.location_district,
                        "assigned_role": None,
                        "assigned_at": None,
                        "assigned_by_name": None,
                        "status": project.status.value,
                        "created_at": project.created_at.isoformat() if project.created_at else None
                    })
        
        # Combine assigned and unassigned
        all_pending = assigned + unassigned
        
        return {
            "total": len(all_pending),
            "assignments": assigned,  # Keep original name for compatibility
            "pending_approvals": all_pending  # Include both assigned and unassigned
        }
    
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching pending approvals: {str(e)}"
        )


@router.get("/project/{project_id}/history")
async def get_approval_history(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get approval history for a project.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_authorized = is_owner or any(
        role in ["Admin", "Architect", "Engineer", "Regulator"] 
        for role in user_roles
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this project's approval history"
        )
    
    try:
        history = approval_service.get_project_approvals(
            project_id=project_id,
            db=db
        )
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "total_approvals": len(history),
            "approval_history": history
        }
    
    except Exception as e:
        logger.error(f"Error fetching approval history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching approval history: {str(e)}"
        )


@router.get("/stats")
async def get_approval_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get approval statistics for the current user.
    """
    user_roles = [ur.role.name for ur in current_user.user_roles]
    
    if not any(role in ["Admin", "Architect", "Engineer", "Regulator"] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers can view approval statistics"
        )
    
    try:
        stats = approval_service.get_stats(
            user_id=current_user.id,
            db=db
        )
        
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching approval stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching approval stats: {str(e)}"
        )

