"""
Layout and GenerationJob models for 3D generated designs.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DECIMAL, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base
from app.models.project import ProjectStatus


class GenerationStatus(str, enum.Enum):
    """3D generation job status enum."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Layout(Base):
    """Generated layout/design option model."""
    
    __tablename__ = "layouts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    name = Column(String(255), nullable=True)  # e.g., 'Option A', 'Revised Layout 1'
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, index=True)
    generation_job_id = Column(String(100), nullable=True, index=True)  # UUID of generation job
    
    # Layout metrics
    building_count = Column(Integer, nullable=True)
    total_floor_area_m2 = Column(DECIMAL(12, 2), nullable=True)
    open_space_area_m2 = Column(DECIMAL(12, 2), nullable=True)
    parking_spaces = Column(Integer, nullable=True)
    max_building_height_m = Column(DECIMAL(8, 2), nullable=True)
    
    # File references
    blend_file_path = Column(String(500), nullable=True)
    glb_file_path = Column(String(500), nullable=True)
    preview_image_path = Column(String(500), nullable=True)
    
    # Generation parameters
    input_parameters = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="layouts")
    creator = relationship("User", foreign_keys=[created_by])
    validation_reports = relationship("ValidationReport", back_populates="layout", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="layout", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="layout", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="related_layout", cascade="all, delete-orphan")
    blockchain_records = relationship("BlockchainRecord", back_populates="layout", cascade="all, delete-orphan")
    generation_job = relationship("GenerationJob", back_populates="layout", uselist=False)
    approval_assignments = relationship("ApprovalAssignment", back_populates="layout", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Layout(id={self.id}, project_id={self.project_id}, version={self.version}, status='{self.status}')>"


class GenerationJob(Base):
    """3D generation job tracking model."""
    
    __tablename__ = "generation_jobs"
    
    id = Column(String(100), primary_key=True)  # UUID
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(GenerationStatus), default=GenerationStatus.QUEUED, index=True)
    progress = Column(Integer, default=0)  # 0-100
    progress_message = Column(String(500), nullable=True)
    
    # Input/output
    input_parameters = Column(JSON, nullable=False)
    output_files = Column(JSON, nullable=True)  # Array of file paths
    error_log = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="generation_jobs")
    layout = relationship("Layout", back_populates="generation_job")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<GenerationJob(id='{self.id}', status='{self.status}', progress={self.progress})>"
