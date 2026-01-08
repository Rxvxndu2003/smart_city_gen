"""
Project model for urban planning projects.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ProjectStatus(str, enum.Enum):
    """Project approval status enum."""
    DRAFT = "DRAFT"
    UNDER_ARCHITECT_REVIEW = "UNDER_ARCHITECT_REVIEW"
    UNDER_ENGINEER_REVIEW = "UNDER_ENGINEER_REVIEW"
    UNDER_REGULATOR_REVIEW = "UNDER_REGULATOR_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVISION = "NEEDS_REVISION"
    CANCELLED = "CANCELLED"


class Project(Base):
    """Main project model."""
    
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, index=True)
    project_type = Column(String(100), nullable=True)  # 'Residential', 'Commercial', 'Mixed-Use'
    
    # Location information
    location_address = Column(String(500), nullable=True)
    location_district = Column(String(100), nullable=True)  # Sri Lankan district
    location_city = Column(String(100), nullable=True)
    location_coordinates = Column(JSON, nullable=True)  # {"lat": float, "lng": float}
    
    # Site information
    site_area_m2 = Column(DECIMAL(12, 2), nullable=True)
    uda_zone = Column(String(50), nullable=True)  # UDA zoning classification
    
    # Building parameters (for validation)
    building_coverage = Column(DECIMAL(5, 2), nullable=True)  # Percentage
    floor_area_ratio = Column(DECIMAL(5, 2), nullable=True)
    num_floors = Column(Integer, nullable=True)
    building_height = Column(DECIMAL(8, 2), nullable=True)  # meters
    open_space_percentage = Column(DECIMAL(5, 2), nullable=True)  # Percentage
    parking_spaces = Column(Integer, nullable=True)
    owner_name = Column(String(255), nullable=True)
    
    # Urban Planning Parameters
    # Zoning Distribution
    residential_percentage = Column(DECIMAL(5, 2), default=60.0, nullable=True)
    commercial_percentage = Column(DECIMAL(5, 2), default=20.0, nullable=True)
    industrial_percentage = Column(DECIMAL(5, 2), default=10.0, nullable=True)
    green_space_percentage_plan = Column(DECIMAL(5, 2), default=10.0, nullable=True)  # Renamed to avoid conflict
    
    # Infrastructure
    road_network_type = Column(String(50), default='GRID', nullable=True)  # GRID, RADIAL, ORGANIC, MIXED
    main_road_width = Column(DECIMAL(5, 2), default=12.0, nullable=True)  # meters
    secondary_road_width = Column(DECIMAL(5, 2), default=8.0, nullable=True)  # meters
    pedestrian_path_width = Column(DECIMAL(5, 2), default=2.0, nullable=True)  # meters
    
    # Demographics
    target_population = Column(Integer, nullable=True)
    population_density = Column(DECIMAL(8, 2), nullable=True)  # people per hectare
    average_household_size = Column(DECIMAL(4, 2), default=3.5, nullable=True)
    
    # Environmental
    climate_zone = Column(String(50), default='TROPICAL', nullable=True)
    sustainability_rating = Column(String(20), default='BRONZE', nullable=True)  # BRONZE, SILVER, GOLD, PLATINUM
    renewable_energy_target = Column(DECIMAL(5, 2), default=0.0, nullable=True)  # percentage
    water_management_strategy = Column(String(255), nullable=True)
    
    # 3D Model
    model_url = Column(String(500), nullable=True)  # Path to generated 3D model file
    enhanced_renders_metadata = Column(JSON, nullable=True)  # AI-enhanced render paths and metadata
    
    # Compliance Prediction (saved)
    predicted_compliance = Column(Integer, nullable=True)  # 1 for compliant, 0 for non-compliant
    compliance_confidence = Column(DECIMAL(5, 4), nullable=True)  # 0.0 to 1.0
    compliance_score = Column(DECIMAL(5, 4), nullable=True)  # 0.0 to 1.0
    prediction_message = Column(Text, nullable=True)
    predicted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps and approval
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    approver = relationship("User", foreign_keys=[approved_by], back_populates="approved_projects")
    site_volumes = relationship("SiteVolume", back_populates="project", cascade="all, delete-orphan")
    layouts = relationship("Layout", back_populates="project", cascade="all, delete-orphan")
    validation_reports = relationship("ValidationReport", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="project", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="related_project", cascade="all, delete-orphan")
    blockchain_records = relationship("BlockchainRecord", back_populates="project", cascade="all, delete-orphan")
    generation_jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")
    approval_assignments = relationship("ApprovalAssignment", back_populates="project", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"
