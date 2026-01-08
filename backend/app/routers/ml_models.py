"""
ML Models router - Machine Learning prediction endpoints for compliance prediction.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

# Optional PyTorch import
try:
    import torch
    import numpy as np
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️  PyTorch not installed - ML predictions will use rule-based fallback")

router = APIRouter()

# Load model and feature columns
MODEL_PATH = Path("ml_models/deployed_model.pt")
FEATURES_PATH = Path("ml_models/feature_columns.json")

# Global model variable
model = None
feature_columns = None

def load_model():
    """Load the trained ML model."""
    global model, feature_columns
    
    if not TORCH_AVAILABLE:
        print("⚠️  PyTorch not available - using rule-based fallback")
        return
    
    if model is None and MODEL_PATH.exists():
        try:
            model = torch.jit.load(str(MODEL_PATH))
            model.eval()
            print("✓ ML model loaded successfully")
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            model = None
    
    if feature_columns is None and FEATURES_PATH.exists():
        try:
            with open(FEATURES_PATH, 'r') as f:
                feature_columns = json.load(f)
            print("✓ Feature columns loaded successfully")
        except Exception as e:
            print(f"✗ Failed to load features: {e}")
            feature_columns = None

class PredictionRequest(BaseModel):
    project_id: int

class ComplianceCheck(BaseModel):
    name: str
    status: str  # 'PASS', 'FAIL', 'WARNING'
    actual_value: float
    expected_range: str
    message: str

class PredictionResponse(BaseModel):
    project_id: int
    predicted_compliance: bool
    confidence: float
    compliance_score: float
    message: str
    checks: Optional[list[ComplianceCheck]] = None

@router.post("/predict", response_model=PredictionResponse)
async def predict_compliance(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict project compliance using ML model."""
    from datetime import datetime, timezone
    
    # Load model if not loaded
    load_model()
    
    # Get project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If PyTorch not available or model not loaded, use rule-based prediction
    if not TORCH_AVAILABLE or model is None or feature_columns is None:
        # Simple rule-based prediction
        compliance_score, detailed_checks = calculate_rule_based_compliance(project)
        predicted_compliance = compliance_score >= 0.7
        confidence = 0.85
        message = "Prediction based on city planning regulations and building codes"
        
        # Save prediction to database
        project.predicted_compliance = 1 if predicted_compliance else 0
        project.compliance_confidence = float(confidence)
        project.compliance_score = float(compliance_score)
        project.prediction_message = message
        project.predicted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
        
        return PredictionResponse(
            project_id=project.id,
            predicted_compliance=predicted_compliance,
            confidence=confidence,
            compliance_score=compliance_score,
            message=message,
            checks=detailed_checks
        )
    
    try:
        # Prepare input features
        input_features = prepare_features(project, feature_columns)
        
        # Make prediction
        with torch.no_grad():
            input_tensor = torch.FloatTensor(input_features).unsqueeze(0)
            output = model(input_tensor)
            probability = torch.sigmoid(output).item()
        
        # Determine compliance
        predicted_compliance = probability >= 0.5
        compliance_score = probability
        confidence = abs(probability - 0.5) * 2  # Confidence based on distance from 0.5
        message = "Prediction from trained ML model"
        
        # Get detailed checks for ML prediction too
        _, detailed_checks = calculate_rule_based_compliance(project)
        
        # Save prediction to database
        project.predicted_compliance = 1 if predicted_compliance else 0
        project.compliance_confidence = float(confidence)
        project.compliance_score = float(compliance_score)
        project.prediction_message = message
        project.predicted_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)
        
        return PredictionResponse(
            project_id=project.id,
            predicted_compliance=predicted_compliance,
            confidence=confidence,
            compliance_score=compliance_score,
            message=message,
            checks=detailed_checks
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/predict/{project_id}", response_model=PredictionResponse)
async def predict_compliance_get(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get compliance prediction for a project (GET method)."""
    return await predict_compliance(
        PredictionRequest(project_id=project_id),
        current_user,
        db
    )

@router.get("/model-info")
async def get_model_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about the loaded ML model."""
    load_model()
    
    return {
        "pytorch_available": TORCH_AVAILABLE,
        "model_loaded": model is not None,
        "model_path": str(MODEL_PATH),
        "model_exists": MODEL_PATH.exists(),
        "features_loaded": feature_columns is not None,
        "num_features": len(feature_columns) if feature_columns else 0,
        "features": feature_columns if feature_columns else []
    }

def calculate_rule_based_compliance(project: Project) -> tuple[float, list[dict]]:
    """Calculate compliance score based on rules and return detailed checks."""
    score = 0.0
    checks = 0
    detailed_checks = []
    
    # Check site area (reasonable range)
    site_area = float(project.site_area_m2)
    site_area_pass = 100 <= site_area <= 10000
    if site_area_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Site Area",
        "status": "PASS" if site_area_pass else "FAIL",
        "actual_value": site_area,
        "expected_range": "100 - 10,000 m²",
        "message": f"Site area is {site_area:.2f} m²" + (" ✓" if site_area_pass else " - Outside acceptable range")
    })
    
    # Check building coverage (typically 30-70%)
    coverage = float(project.building_coverage)
    coverage_pass = 30 <= coverage <= 70
    if coverage_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Building Coverage",
        "status": "PASS" if coverage_pass else "FAIL",
        "actual_value": coverage,
        "expected_range": "30 - 70%",
        "message": f"Building coverage is {coverage:.2f}%" + (" ✓" if coverage_pass else " - Outside acceptable range")
    })
    
    # Check open space (minimum 20%)
    open_space = float(project.open_space_percentage)
    open_space_pass = open_space >= 20
    if open_space_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Open Space",
        "status": "PASS" if open_space_pass else "FAIL",
        "actual_value": open_space,
        "expected_range": "≥ 20%",
        "message": f"Open space is {open_space:.2f}%" + (" ✓" if open_space_pass else " - Below minimum requirement")
    })
    
    # Check FAR (typical range 1-3)
    far = float(project.floor_area_ratio)
    far_pass = 1 <= far <= 3
    if far_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Floor Area Ratio (FAR)",
        "status": "PASS" if far_pass else "FAIL",
        "actual_value": far,
        "expected_range": "1.0 - 3.0",
        "message": f"FAR is {far:.2f}" + (" ✓" if far_pass else " - Outside acceptable range")
    })
    
    # Check parking (at least 1 space per 100m²)
    required_parking = site_area / 100
    parking_spaces = float(project.parking_spaces)
    parking_pass = parking_spaces >= required_parking * 0.8
    if parking_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Parking Spaces",
        "status": "PASS" if parking_pass else "FAIL",
        "actual_value": parking_spaces,
        "expected_range": f"≥ {required_parking * 0.8:.1f} spaces",
        "message": f"Provided {parking_spaces:.0f} spaces (required: {required_parking * 0.8:.1f})" + (" ✓" if parking_pass else " - Insufficient parking")
    })
    
    # Check building height vs floors (typical 3-4m per floor)
    expected_height = float(project.num_floors) * 3.5
    actual_height = float(project.building_height)
    height_pass = abs(actual_height - expected_height) / expected_height < 0.2 if expected_height > 0 else True
    if height_pass:
        score += 1
    checks += 1
    detailed_checks.append({
        "name": "Building Height",
        "status": "PASS" if height_pass else "WARNING",
        "actual_value": actual_height,
        "expected_range": f"{expected_height * 0.8:.1f} - {expected_height * 1.2:.1f} m",
        "message": f"Height is {actual_height:.2f}m for {project.num_floors} floors (expected ~{expected_height:.2f}m)" + (" ✓" if height_pass else " ⚠")
    })
    
    return (score / checks if checks > 0 else 0.5, detailed_checks)

def prepare_features(project: Project, feature_cols: list) -> list:
    """Prepare input features for the model."""
    features = []
    
    # Map project attributes to features
    feature_map = {
        'site_area': float(project.site_area_m2),
        'building_coverage': float(project.building_coverage),
        'floor_area_ratio': float(project.floor_area_ratio),
        'num_floors': float(project.num_floors),
        'building_height': float(project.building_height),
        'open_space_percentage': float(project.open_space_percentage),
        'parking_spaces': float(project.parking_spaces),
    }
    
    # Add categorical encodings if needed
    for col in feature_cols:
        if col in feature_map:
            features.append(float(feature_map[col]))
        elif col.startswith('project_type_'):
            type_name = col.replace('project_type_', '')
            features.append(1.0 if project.project_type == type_name else 0.0)
        elif col.startswith('district_'):
            district_name = col.replace('district_', '')
            features.append(1.0 if project.district == district_name else 0.0)
        else:
            features.append(0.0)  # Default value
    
    return features
