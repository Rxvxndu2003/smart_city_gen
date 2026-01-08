"""
ML Service for 3D Building Generation
Uses trained PyTorch model to predict optimal building parameters
"""
import torch
import torch.nn as nn
import json
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np


class BuildingParameterPredictor(nn.Module):
    """Neural network for predicting optimal building parameters"""
    def __init__(self, input_dim=10, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 8)  # Output: enhanced parameters
        )
    
    def forward(self, x):
        return self.network(x)


class MLEnhancedGenerationService:
    """Service for ML-enhanced 3D building generation"""
    
    def __init__(self, model_path: str = "ml_models/deployed_model.pt"):
        self.model_path = Path(model_path)
        self.model = None
        self.feature_stats = None
        self.load_model()
    
    def load_model(self):
        """Load the trained PyTorch model"""
        try:
            if self.model_path.exists():
                print(f"Loading ML model from {self.model_path}")
                checkpoint = torch.load(self.model_path, map_location='cpu', weights_only=False)
                
                # Initialize model architecture
                if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                    input_dim = checkpoint.get('input_dim', 10)
                    hidden_dim = checkpoint.get('hidden_dim', 128)
                    self.model = BuildingParameterPredictor(input_dim, hidden_dim)
                    self.model.load_state_dict(checkpoint['model_state_dict'])
                    self.feature_stats = checkpoint.get('feature_stats', {})
                else:
                    # Assume it's just the state dict
                    self.model = BuildingParameterPredictor()
                    self.model.load_state_dict(checkpoint)
                
                self.model.eval()
                print("✓ ML model loaded successfully")
            else:
                print(f"⚠ Model file not found: {self.model_path}")
                print("Using rule-based parameter enhancement")
                self.model = None
        except Exception as e:
            print(f"✗ Failed to load ML model: {e}")
            print("Using rule-based parameter enhancement")
            self.model = None
    
    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize input features"""
        if self.feature_stats:
            mean = np.array(self.feature_stats.get('mean', [0] * len(features)))
            std = np.array(self.feature_stats.get('std', [1] * len(features)))
            return (features - mean) / (std + 1e-8)
        return features
    
    def predict_building_parameters(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict optimal building parameters using ML model
        
        Args:
            input_params: Basic project parameters
                - site_area: Total site area in m²
                - building_coverage: Building coverage percentage
                - num_floors: Number of floors
                - project_type: RESIDENTIAL, COMMERCIAL, MIXED_USE
                - width: Building width
                - depth: Building depth
                - height: Building height
        
        Returns:
            Enhanced parameters with ML predictions
        """
        # Extract and normalize input features
        features = self._extract_features(input_params)
        
        if self.model is None:
            # Fallback: Use rule-based enhancement
            print("Using standard planning rules for parameter enhancement")
            return self._rule_based_enhancement(input_params)
        
        try:
            # Prepare input tensor
            features_normalized = self.normalize_features(features)
            input_tensor = torch.FloatTensor(features_normalized).unsqueeze(0)
            
            # Make prediction
            with torch.no_grad():
                predictions = self.model(input_tensor)
                predictions = predictions.squeeze().numpy()
            
            # Post-process predictions
            enhanced_params = self._post_process_predictions(input_params, predictions)
            
            print(f"✓ ML predictions generated for {input_params.get('project_type', 'UNKNOWN')} building")
            return enhanced_params
            
        except Exception as e:
            print(f"✗ ML prediction failed: {e}")
            return self._rule_based_enhancement(input_params)
    
    def _extract_features(self, params: Dict[str, Any]) -> np.ndarray:
        """Extract normalized features from input parameters"""
        # Map project type to numeric
        project_type_map = {
            'RESIDENTIAL': 0,
            'COMMERCIAL': 1,
            'MIXED_USE': 2,
            'INDUSTRIAL': 3
        }
        
        features = np.array([
            params.get('site_area', 1000) / 10000,  # Normalize by 10,000 m²
            params.get('building_coverage', 30) / 100,
            params.get('num_floors', 10) / 50,
            params.get('width', 20) / 100,
            params.get('depth', 15) / 100,
            params.get('height', 30) / 200,
            project_type_map.get(params.get('project_type', 'RESIDENTIAL'), 0) / 3,
            params.get('site_area', 1000) * params.get('building_coverage', 30) / 100 / 10000,  # Built area
            params.get('width', 20) / params.get('depth', 15) if params.get('depth', 15) > 0 else 1,  # Aspect ratio
            params.get('height', 30) / params.get('num_floors', 10) if params.get('num_floors', 10) > 0 else 3  # Floor height
        ])
        
        return features
    
    def _post_process_predictions(self, input_params: Dict[str, Any], predictions: np.ndarray) -> Dict[str, Any]:
        """Post-process ML predictions to ensure valid building parameters"""
        enhanced = input_params.copy()
        
        # Predicted enhancements
        enhanced['window_size'] = max(0.8, min(2.5, abs(predictions[0]) * 2))
        enhanced['window_spacing'] = max(2.0, min(4.0, abs(predictions[1]) * 3 + 2.5))
        enhanced['facade_detail_level'] = max(1, min(5, int(abs(predictions[2]) * 5)))
        enhanced['roof_type'] = 'flat' if predictions[3] > 0 else 'sloped'
        enhanced['balcony_enabled'] = predictions[4] > 0
        enhanced['entrance_width'] = max(2.0, min(5.0, abs(predictions[5]) * 3 + 2.5))
        enhanced['material_quality'] = max(0.5, min(1.0, abs(predictions[6])))
        enhanced['architectural_style'] = self._determine_style(predictions[7], input_params.get('project_type'))
        
        # Compliance-aware adjustments
        enhanced['min_open_space'] = input_params.get('site_area', 1000) * (1 - input_params.get('building_coverage', 30) / 100)
        enhanced['max_building_height'] = min(input_params.get('height', 30), 75)  # 75m limit
        
        return enhanced
    
    def _determine_style(self, style_score: float, project_type: str) -> str:
        """Determine architectural style based on ML prediction and project type"""
        if project_type == 'COMMERCIAL':
            return 'modern' if style_score > 0 else 'corporate'
        elif project_type == 'RESIDENTIAL':
            return 'contemporary' if style_score > 0 else 'traditional'
        else:
            return 'mixed'
    
    def _rule_based_enhancement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based parameter enhancement when ML is unavailable"""
        enhanced = params.copy()
        project_type = params.get('project_type', 'RESIDENTIAL')
        
        # Rule-based defaults
        if project_type == 'RESIDENTIAL':
            enhanced.update({
                'window_size': 1.5,
                'window_spacing': 3.0,
                'facade_detail_level': 3,
                'roof_type': 'sloped',
                'balcony_enabled': True,
                'entrance_width': 2.5,
                'material_quality': 0.8,
                'architectural_style': 'contemporary'
            })
        elif project_type == 'COMMERCIAL':
            enhanced.update({
                'window_size': 2.0,
                'window_spacing': 2.5,
                'facade_detail_level': 4,
                'roof_type': 'flat',
                'balcony_enabled': False,
                'entrance_width': 4.0,
                'material_quality': 0.9,
                'architectural_style': 'modern'
            })
        else:  # MIXED_USE
            enhanced.update({
                'window_size': 1.8,
                'window_spacing': 2.8,
                'facade_detail_level': 4,
                'roof_type': 'flat',
                'balcony_enabled': True,
                'entrance_width': 3.5,
                'material_quality': 0.85,
                'architectural_style': 'mixed'
            })
        
        # Compliance calculations
        enhanced['min_open_space'] = params.get('site_area', 1000) * (1 - params.get('building_coverage', 30) / 100)
        enhanced['max_building_height'] = min(params.get('height', 30), 75)
        
        return enhanced
    
    def generate_blender_params(self, input_params: Dict[str, Any]) -> str:
        """Generate complete parameters JSON for Blender script"""
        enhanced = self.predict_building_parameters(input_params)
        
        # Convert Decimal to float for JSON serialization
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif hasattr(obj, '__iter__') and not isinstance(obj, str):
                return [convert_decimals(item) for item in obj]
            elif hasattr(obj, 'is_integer'):  # Decimal
                return float(obj)
            return obj
        
        enhanced = convert_decimals(enhanced)
        
        # Format for Blender script
        blender_params = {
            # Basic dimensions
            'width': float(enhanced.get('width', 20)),
            'depth': float(enhanced.get('depth', 15)),
            'height': float(enhanced.get('height', 30)),
            'num_floors': int(enhanced.get('num_floors', 10)),
            
            # Site parameters
            'site_area': float(enhanced.get('site_area', 1000)),
            'building_coverage': float(enhanced.get('building_coverage', 30)),
            
            # ML-enhanced details
            'window_size': float(enhanced.get('window_size', 1.5)),
            'window_spacing': float(enhanced.get('window_spacing', 3.0)),
            'facade_detail_level': int(enhanced.get('facade_detail_level', 3)),
            'roof_type': str(enhanced.get('roof_type', 'flat')),
            'balcony_enabled': bool(enhanced.get('balcony_enabled', True)),
            'entrance_width': float(enhanced.get('entrance_width', 2.5)),
            'material_quality': float(enhanced.get('material_quality', 0.8)),
            'architectural_style': str(enhanced.get('architectural_style', 'contemporary')),
            
            # Type and compliance
            'project_type': str(enhanced.get('project_type', 'RESIDENTIAL')),
            'min_open_space': float(enhanced.get('min_open_space', 700)),
            'max_building_height': float(enhanced.get('max_building_height', 75)),
            
            # Output settings
            'output_path': str(enhanced.get('output_path', 'output.glb')),
            'format': str(enhanced.get('format', 'GLB'))
        }
        
        return json.dumps(blender_params, indent=2)


# Global singleton instance
_ml_service = None

def get_ml_service() -> MLEnhancedGenerationService:
    """Get or create the ML service singleton"""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLEnhancedGenerationService()
    return _ml_service
