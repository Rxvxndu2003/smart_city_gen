"""
ValidationReport model for UDA compliance and ML predictions.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DECIMAL, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ReportType(str, enum.Enum):
    """Validation report type enum."""
    UDA_COMPLIANCE = "UDA_COMPLIANCE"
    ML_PREDICTION = "ML_PREDICTION"
    FULL_VALIDATION = "FULL_VALIDATION"


class ValidationReport(Base):
    """Validation and compliance report model."""
    
    __tablename__ = "validation_reports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=True, index=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Overall result
    is_compliant = Column(Boolean, nullable=True)
    compliance_score = Column(DECIMAL(5, 2), nullable=True)  # 0-100
    
    # Detailed results (JSON)
    rule_checks = Column(JSON, nullable=True)  # Array of {rule_name, status, actual_value, required_value, message}
    ml_predictions = Column(JSON, nullable=True)  # ML model outputs
    recommendations = Column(JSON, nullable=True)  # Array of corrective actions
    
    # Model versions used
    model_versions = Column(JSON, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="validation_reports")
    layout = relationship("Layout", back_populates="validation_reports")
    generator = relationship("User", foreign_keys=[generated_by])
    
    def __repr__(self):
        return f"<ValidationReport(id={self.id}, project_id={self.project_id}, compliant={self.is_compliant})>"
