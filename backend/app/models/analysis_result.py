"""
Analysis Result Model for Smart City Planning System.
Stores energy, structural, and green space analysis results.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
import enum

from app.database import Base


class AnalysisType(str, enum.Enum):
    """Enum for analysis types."""
    ENERGY = "energy"
    STRUCTURAL = "structural"
    GREEN_SPACE = "green_space"


class AnalysisResult(Base):
    """
    Model for storing analysis results.
    
    Stores comprehensive analysis data for energy efficiency,
    structural integrity, and green space optimization.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_type = Column(SQLEnum(AnalysisType), nullable=False, index=True)
    
    # Store complete analysis data as JSON
    analysis_data = Column(JSONB, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="analysis_results")

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, project_id={self.project_id}, type={self.analysis_type})>"
