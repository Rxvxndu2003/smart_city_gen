"""
Export model for tracking generated files (IFC, DXF, etc.).
"""
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ExportType(str, enum.Enum):
    """Export file type enum."""
    IFC = "IFC"
    DXF = "DXF"
    FBX = "FBX"
    GLB = "GLB"
    XLSX = "XLSX"
    PDF_REPORT = "PDF_REPORT"


class Export(Base):
    """Export record model."""
    
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=False, index=True)
    export_type = Column(Enum(ExportType), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    
    # Metadata
    parameters = Column(JSON, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    download_count = Column(Integer, default=0)
    
    # Relationships
    project = relationship("Project", back_populates="exports")
    layout = relationship("Layout", back_populates="exports")
    generator = relationship("User", foreign_keys=[generated_by])
    
    def __repr__(self):
        return f"<Export(id={self.id}, type='{self.export_type}', layout_id={self.layout_id})>"
