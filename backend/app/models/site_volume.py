"""
Site volume model for 3D zoning envelopes and boundaries.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class VolumeType(str, enum.Enum):
    """Site volume type enum."""
    SITE_BOUNDARY = "SITE_BOUNDARY"
    ZONING_ENVELOPE = "ZONING_ENVELOPE"
    SETBACK = "SETBACK"
    HEIGHT_PLANE = "HEIGHT_PLANE"


class SiteVolume(Base):
    """Site boundary and zoning volumes model."""
    
    __tablename__ = "site_volumes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    volume_type = Column(Enum(VolumeType), nullable=False)
    geometry = Column(JSON, nullable=False)  # GeoJSON Polygon format
    
    # 3D parameters
    height_max = Column(DECIMAL(8, 2), nullable=True)  # meters
    height_min = Column(DECIMAL(8, 2), nullable=True)
    floor_area_ratio = Column(DECIMAL(5, 2), nullable=True)
    coverage_ratio = Column(DECIMAL(5, 2), nullable=True)
    
    # Additional properties
    properties = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="site_volumes")
    
    def __repr__(self):
        return f"<SiteVolume(id={self.id}, project_id={self.project_id}, type='{self.volume_type}')>"
