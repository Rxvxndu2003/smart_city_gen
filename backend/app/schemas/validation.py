"""
Validation and ML prediction schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# Rule Check Schema
class RuleCheck(BaseModel):
    """Individual rule check result."""
    rule_name: str
    rule_description: str
    status: str = Field(..., description="PASS, FAIL, WARNING, N/A")
    actual_value: Optional[Any] = None
    required_value: Optional[Any] = None
    message: str
    severity: str = Field(default="INFO", description="INFO, WARNING, ERROR, CRITICAL")


class MLPrediction(BaseModel):
    """ML model prediction result."""
    model_name: str
    model_version: str
    prediction: Any
    confidence: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None


class Recommendation(BaseModel):
    """Corrective action recommendation."""
    title: str
    description: str
    impact: str = Field(..., description="HIGH, MEDIUM, LOW")
    estimated_cost: Optional[Decimal] = None
    estimated_time_days: Optional[int] = None


# Validation Request Schemas
class ValidationRequest(BaseModel):
    """Request to run validation."""
    project_id: int
    layout_id: Optional[int] = None
    validation_type: str = Field(default="FULL_VALIDATION", description="UDA_COMPLIANCE, ML_PREDICTION, FULL_VALIDATION")


class OpenSpaceValidationRequest(BaseModel):
    """Request for open space validation."""
    project_type: str
    site_area_m2: Decimal
    total_floor_area_m2: Decimal
    building_count: int
    uda_zone: str
    location_district: str
    additional_features: Optional[Dict[str, Any]] = None


# Validation Response Schemas
class ValidationReportResponse(BaseModel):
    """Validation report response schema."""
    id: int
    project_id: int
    layout_id: Optional[int] = None
    report_type: str
    is_compliant: Optional[bool] = None
    compliance_score: Optional[Decimal] = None
    rule_checks: List[RuleCheck] = []
    ml_predictions: List[MLPrediction] = []
    recommendations: List[Recommendation] = []
    model_versions: Optional[Dict[str, str]] = None
    generated_at: datetime
    generated_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class OpenSpaceValidationResponse(BaseModel):
    """Open space validation response."""
    requires_open_space: bool
    required_open_space_m2: Optional[Decimal] = None
    current_open_space_m2: Optional[Decimal] = None
    is_compliant: bool
    confidence: float
    model_version: str
    recommendations: List[str] = []


class UDAComplianceResponse(BaseModel):
    """UDA compliance check response."""
    is_compliant: bool
    compliance_score: Decimal
    passed_rules: List[str]
    failed_rules: List[RuleCheck]
    warnings: List[RuleCheck]
    uda_zone: str
    checked_rules: List[str]


class ValidationSummary(BaseModel):
    """Summary of validation results."""
    project_id: int
    layout_id: Optional[int] = None
    overall_compliant: bool
    compliance_score: Decimal
    critical_issues: int
    warnings: int
    passed_checks: int
    failed_checks: int
    last_validated: datetime
