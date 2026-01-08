"""
Approval workflow service - Manages project approvals.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.models.approval import Approval, ApprovalAssignment, ApprovalAssignmentStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for managing approval workflows."""
    
    def create_approval_assignment(
        self,
        project_id: int,
        assigned_to_id: int,
        assigned_role: str,
        assigned_by_id: int,
        db: Session,
        layout_id: Optional[int] = None
    ) -> ApprovalAssignment:
        """Create a new approval assignment."""
        assignment = ApprovalAssignment(
            project_id=project_id,
            layout_id=layout_id,
            assigned_to=assigned_to_id,
            assigned_role=assigned_role,
            status=ApprovalAssignmentStatus.PENDING,
            assigned_at=datetime.utcnow(),
            assigned_by=assigned_by_id
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        logger.info(f"Created approval assignment {assignment.id} for project {project_id}")
        return assignment
    
    def complete_approval_assignment(
        self,
        assignment_id: int,
        db: Session
    ) -> ApprovalAssignment:
        """Mark an approval assignment as completed."""
        assignment = db.query(ApprovalAssignment).filter(
            ApprovalAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            raise ValueError(f"Assignment {assignment_id} not found")
        
        assignment.status = ApprovalAssignmentStatus.COMPLETED
        assignment.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(assignment)
        
        logger.info(f"Completed approval assignment {assignment_id}")
        return assignment
    
    def get_pending_assignments(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get pending approval assignments for a user."""
        assignments = db.query(ApprovalAssignment).join(Project).filter(
            ApprovalAssignment.assigned_to == user_id,
            ApprovalAssignment.status == ApprovalAssignmentStatus.PENDING
        ).all()
        
        result = []
        for assignment in assignments:
            result.append({
                "assignment_id": assignment.id,
                "project_id": assignment.project_id,
                "project_name": assignment.project.name if assignment.project else "Unknown",
                "project_type": assignment.project.project_type if assignment.project else None,
                "assigned_role": assignment.assigned_role,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
                "assigned_by_name": assignment.assigner.full_name if assignment.assigner else "System",
            })
        
        return result
    
    def create_approval_record(
        self,
        project_id: int,
        user_id: int,
        user_role: str,
        status_from: Optional[ProjectStatus],
        status_to: ProjectStatus,
        comment: Optional[str],
        db: Session,
        layout_id: Optional[int] = None,
        is_admin_override: bool = False
    ) -> Approval:
        """Create an approval/status change record."""
        approval = Approval(
            project_id=project_id,
            layout_id=layout_id,
            status_from=status_from,
            status_to=status_to,
            user_id=user_id,
            user_role=user_role,
            comment=comment,
            is_admin_override=is_admin_override,
            timestamp=datetime.utcnow()
        )
        db.add(approval)
        
        # Update project status
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = status_to
        
        db.commit()
        db.refresh(approval)
        
        logger.info(f"Created approval record {approval.id}: {status_from} -> {status_to}")
        return approval
    
    def get_project_approvals(
        self,
        project_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get approval history for a project."""
        approvals = db.query(Approval).filter(
            Approval.project_id == project_id
        ).order_by(Approval.timestamp.desc()).all()
        
        result = []
        for approval in approvals:
            result.append({
                "approval_id": approval.id,
                "status_from": approval.status_from.value if approval.status_from else None,
                "status_to": approval.status_to.value if approval.status_to else None,
                "user_name": approval.user.full_name if approval.user else "Unknown",
                "user_role": approval.user_role,
                "timestamp": approval.timestamp.isoformat() if approval.timestamp else None,
                "comment": approval.comment,
                "is_admin_override": approval.is_admin_override
            })
        
        return result
    
    def get_stats(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, int]:
        """Get approval statistics for a user."""
        pending = db.query(ApprovalAssignment).filter(
            ApprovalAssignment.assigned_to == user_id,
            ApprovalAssignment.status == ApprovalAssignmentStatus.PENDING
        ).count()
        
        completed = db.query(ApprovalAssignment).filter(
            ApprovalAssignment.assigned_to == user_id,
            ApprovalAssignment.status == ApprovalAssignmentStatus.COMPLETED
        ).count()
        
        # Count approvals made by this user
        approved = db.query(Approval).filter(
            Approval.user_id == user_id,
            Approval.status_to == ProjectStatus.APPROVED
        ).count()
        
        rejected = db.query(Approval).filter(
            Approval.user_id == user_id,
            Approval.status_to == ProjectStatus.REJECTED
        ).count()
        
        return {
            "pending": pending,
            "completed": completed,
            "approved": approved,
            "rejected": rejected,
            "total_reviewed": approved + rejected
        }


# Global instance
approval_service = ApprovalService()
