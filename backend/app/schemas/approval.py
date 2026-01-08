"""
Approval workflow schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# Approval Schemas
class ApprovalBase(BaseModel):
    """Base approval schema."""
    comment: Optional[str] = None
    attachments: Optional[List[str]] = None  # Array of file paths


class ApprovalSubmitRequest(ApprovalBase):
    """Request to submit for approval (change status)."""
    layout_id: Optional[int] = None
    target_status: str = Field(..., description="Target status to transition to")


class ApprovalActionRequest(ApprovalBase):
    """Request for approval action (approve/reject/request changes)."""
    layout_id: Optional[int] = None


class ApprovalResponse(BaseModel):
    """Approval response schema."""
    id: int
    project_id: int
    layout_id: Optional[int] = None
    status_from: Optional[str] = None
    status_to: str
    user_id: int
    user_role: str
    timestamp: datetime
    comment: Optional[str] = None
    attachments: Optional[List[str]] = None
    is_admin_override: bool
    user_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ApprovalTimelineResponse(BaseModel):
    """Approval timeline/history response."""
    project_id: int
    layout_id: Optional[int] = None
    approvals: List[ApprovalResponse]


# Approval Assignment Schemas
class ApprovalAssignmentCreate(BaseModel):
    """Schema for creating an approval assignment."""
    project_id: int
    layout_id: Optional[int] = None
    assigned_to: int
    assigned_role: str


class ApprovalAssignmentUpdate(BaseModel):
    """Schema for updating an approval assignment."""
    status: str = Field(..., description="PENDING, IN_PROGRESS, COMPLETED")


class ApprovalAssignmentResponse(BaseModel):
    """Approval assignment response schema."""
    id: int
    project_id: int
    layout_id: Optional[int] = None
    assigned_to: int
    assigned_role: str
    status: str
    assigned_at: datetime
    assigned_by: Optional[int] = None
    completed_at: Optional[datetime] = None
    assignee_name: Optional[str] = None
    project_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class PendingApprovalsResponse(BaseModel):
    """Response for pending approvals."""
    total: int
    assignments: List[ApprovalAssignmentResponse]


class ApprovalDashboardStats(BaseModel):
    """Approval dashboard statistics."""
    pending_architect_review: int
    pending_engineer_review: int
    pending_regulator_review: int
    total_pending: int
    approved_this_month: int
    rejected_this_month: int
