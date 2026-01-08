"""
Approval and ApprovalAssignment models for workflow management.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.project import ProjectStatus


class ApprovalAssignmentStatus(str, enum.Enum):
    """Approval assignment status enum."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Approval(Base):
    """Approval/status change log model."""
    
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # State transition
    status_from = Column(Enum(ProjectStatus), nullable=True)
    status_to = Column(Enum(ProjectStatus), nullable=False)
    
    # Who & when
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)  # Role at time of action
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Details
    comment = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)  # Array of file paths
    is_admin_override = Column(Boolean, default=False)
    
    # Relationships
    project = relationship("Project", back_populates="approvals")
    layout = relationship("Layout", back_populates="approvals")
    user = relationship("User", back_populates="approvals")
    
    def __repr__(self):
        return f"<Approval(id={self.id}, {self.status_from} -> {self.status_to}, by user {self.user_id})>"


class ApprovalAssignment(Base):
    """Pending approval assignment model."""
    
    __tablename__ = "approval_assignments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_role = Column(String(50), nullable=False)
    status = Column(Enum(ApprovalAssignmentStatus), default=ApprovalAssignmentStatus.PENDING)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="approval_assignments")
    layout = relationship("Layout", back_populates="approval_assignments")
    assignee = relationship("User", foreign_keys=[assigned_to])
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<ApprovalAssignment(id={self.id}, assigned_to={self.assigned_to}, status='{self.status}')>"
