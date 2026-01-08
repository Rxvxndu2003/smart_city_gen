"""
ML Service for model predictions and recommendations.
Loads and uses deployed ML models for urban planning recommendations.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Optional imports
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("PyTorch not available")
    
try:
    import pickle
    PICKLE_AVAILABLE = True
except ImportError:
    PICKLE_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Model paths (relative to project root)
MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent
PYTORCH_MODEL_PATH = MODEL_DIR / "deployed_model.pt"
CLF_MODEL_PATH = MODEL_DIR / "clf_requires_open_space.pkl"
REG_MODEL_PATH = MODEL_DIR / "reg_min_open_space_m2.pkl"
FEATURE_COLUMNS_PATH = MODEL_DIR / "feature_columns.json"


class MLService:
    """Machine Learning service for urban planning predictions."""
    
    def __init__(self):
        """Initialize ML service and load models."""
        self.pytorch_model = None
        self.clf_model = None
        self.reg_model = None
        self.feature_columns = None
        self.models_loaded = False
        
        self._load_models()
    
    def _load_models(self):
        """Load all ML models from disk."""
        try:
            # Load PyTorch model
            if TORCH_AVAILABLE and PYTORCH_MODEL_PATH.exists():
                self.pytorch_model = torch.load(PYTORCH_MODEL_PATH, map_location=torch.device('cpu'))
                self.pytorch_model.eval()
                logger.info("PyTorch model loaded successfully")
            else:
                if not TORCH_AVAILABLE:
                    logger.warning("PyTorch not available, skipping model loading")
                else:
                    logger.warning(f"PyTorch model not found at {PYTORCH_MODEL_PATH}")
            
            # Load classifier for open space requirement
            if PICKLE_AVAILABLE and CLF_MODEL_PATH.exists():
                with open(CLF_MODEL_PATH, 'rb') as f:
                    self.clf_model = pickle.load(f)
                logger.info("Open space classifier loaded successfully")
            else:
                if not PICKLE_AVAILABLE:
                    logger.warning("Pickle not available")
                else:
                    logger.warning(f"Classifier model not found at {CLF_MODEL_PATH}")
            
            # Load regressor for minimum open space area
            if PICKLE_AVAILABLE and REG_MODEL_PATH.exists():
                with open(REG_MODEL_PATH, 'rb') as f:
                    self.reg_model = pickle.load(f)
                logger.info("Open space regressor loaded successfully")
            else:
                if not PICKLE_AVAILABLE:
                    logger.warning("Pickle not available")
                else:
                    logger.warning(f"Regressor model not found at {REG_MODEL_PATH}")
            
            # Load feature columns
            if FEATURE_COLUMNS_PATH.exists():
                import json
                with open(FEATURE_COLUMNS_PATH, 'r') as f:
                    self.feature_columns = json.load(f)
                logger.info("Feature columns loaded successfully")
            else:
                logger.warning(f"Feature columns not found at {FEATURE_COLUMNS_PATH}")
            
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            self.models_loaded = False
    
    def predict_open_space_requirement(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict if open space is required and minimum area needed.
        
        Args:
            project_data: Dictionary with project features
            
        Returns:
            Dict with prediction results
        """
        if not self.models_loaded or not self.clf_model or not self.reg_model:
            return {
                "error": "ML models not loaded",
                "requires_open_space": None,
                "min_open_space_m2": None
            }
        
        try:
            # Prepare features
            features = self._prepare_features(project_data)
            
            # Predict if open space is required
            requires_open_space = bool(self.clf_model.predict(features)[0])
            
            # Predict minimum open space area if required
            min_open_space_m2 = 0.0
            if requires_open_space:
                min_open_space_m2 = float(self.reg_model.predict(features)[0])
            
            return {
                "requires_open_space": requires_open_space,
                "min_open_space_m2": round(min_open_space_m2, 2),
                "site_area_m2": project_data.get("site_area", 0),
                "open_space_ratio": round(min_open_space_m2 / project_data.get("site_area", 1) * 100, 2) if requires_open_space else 0
            }
            
        except Exception as e:
            logger.error(f"Error in open space prediction: {e}")
            return {
                "error": str(e),
                "requires_open_space": None,
                "min_open_space_m2": None
            }
    
    def get_project_recommendations(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive recommendations for a project.
        
        Args:
            project_data: Dictionary with project information
            
        Returns:
            Dict with recommendations
        """
        recommendations = {
            "open_space": self.predict_open_space_requirement(project_data),
            "building_parameters": self._get_building_recommendations(project_data),
            "compliance_tips": self._get_compliance_tips(project_data)
        }
        
        return recommendations
    
    def _prepare_features(self, project_data: Dict[str, Any]) -> Any:
        """
        Prepare feature vector from project data.
        
        Args:
            project_data: Raw project data
            
        Returns:
            Feature vector (numpy array if available, list otherwise)
        """
        # Extract relevant features based on what models expect
        features = {
            'site_area': project_data.get('site_area', 0),
            'project_type': project_data.get('project_type', 'RESIDENTIAL'),
            'district': project_data.get('district', 'COLOMBO'),
            'building_height': project_data.get('building_height', 0),
            'floor_count': project_data.get('floor_count', 1),
            'total_floor_area': project_data.get('total_floor_area', 0)
        }
        
        # Convert categorical to numerical (simple encoding)
        type_mapping = {
            'RESIDENTIAL': 1,
            'COMMERCIAL': 2,
            'INDUSTRIAL': 3,
            'MIXED_USE': 4,
            'INSTITUTIONAL': 5
        }
        
        feature_vector = [
            features['site_area'],
            type_mapping.get(features['project_type'], 1),
            features['building_height'],
            features['floor_count'],
            features['total_floor_area']
        ]
        
        if NUMPY_AVAILABLE:
            import numpy as np
            return np.array([feature_vector])
        return [feature_vector]
    
    def _get_building_recommendations(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get building parameter recommendations based on UDA rules."""
        site_area = project_data.get('site_area', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        
        # Basic UDA guidelines (simplified)
        recommendations = {
            "max_building_coverage": 0.6 if project_type == 'RESIDENTIAL' else 0.7,
            "max_floor_area_ratio": 2.5 if project_type == 'RESIDENTIAL' else 3.0,
            "min_setback_front": 3.0,
            "min_setback_side": 1.5,
            "min_setback_rear": 3.0,
            "max_building_height": 18.0 if project_type == 'RESIDENTIAL' else 30.0
        }
        
        # Calculate recommended values
        recommendations["recommended_coverage_m2"] = round(site_area * recommendations["max_building_coverage"], 2)
        recommendations["recommended_total_floor_area_m2"] = round(site_area * recommendations["max_floor_area_ratio"], 2)
        
        return recommendations
    
    def _get_compliance_tips(self, project_data: Dict[str, Any]) -> List[str]:
        """Get compliance tips based on project type and location."""
        tips = [
            "Ensure all setback requirements are met",
            "Verify building coverage does not exceed maximum allowed",
            "Check floor area ratio compliance",
            "Provide adequate parking spaces as per UDA regulations",
            "Ensure proper waste management facilities",
            "Include fire safety measures and emergency exits"
        ]
        
        project_type = project_data.get('project_type')
        
        if project_type == 'RESIDENTIAL':
            tips.extend([
                "Provide minimum 15% open space for landscaping",
                "Ensure adequate natural ventilation in all units",
                "Include recreational facilities for residents"
            ])
        elif project_type == 'COMMERCIAL':
            tips.extend([
                "Provide adequate loading/unloading areas",
                "Ensure accessibility compliance for persons with disabilities",
                "Include proper signage and wayfinding"
            ])
        
        return tips


# Global ML service instance
ml_service = MLService()
