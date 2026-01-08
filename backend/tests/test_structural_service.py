"""
Unit tests for Structural Integrity Service.
Tests load calculations, safety factors, and foundation requirements.
"""
import pytest
from app.services.structural_service import structural_service


class TestStructuralService:
    """Test suite for StructuralService."""
    
    def test_validate_structural_integrity_basic(self):
        """Test basic structural validation."""
        result = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        assert "is_structurally_safe" in result
        assert "safety_factor" in result
        assert "loads" in result
        assert "foundation" in result
        assert result["validation_status"] in ["PASS", "FAIL"]
    
    def test_safety_factor_minimum(self):
        """Test that safety factor meets minimum requirement."""
        result = structural_service.validate_structural_integrity(
            building_height=9.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        # Should meet minimum safety factor of 2.0
        if result["is_structurally_safe"]:
            assert result["safety_factor"] >= 2.0
    
    def test_load_calculations(self):
        """Test that all loads are calculated."""
        result = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        loads = result["loads"]
        assert "dead_load_kn" in loads
        assert "live_load_kn" in loads
        assert "wind_load_kn" in loads
        assert "seismic_load_kn" in loads
        assert "total_design_load_kn" in loads
        
        # All loads should be positive
        assert loads["dead_load_kn"] > 0
        assert loads["live_load_kn"] > 0
        assert loads["wind_load_kn"] > 0
        assert loads["seismic_load_kn"] > 0
        assert loads["total_design_load_kn"] > 0
    
    def test_building_height_impact(self):
        """Test that taller buildings have higher wind loads."""
        result_low = structural_service.validate_structural_integrity(
            building_height=6.0,
            num_floors=2,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        result_high = structural_service.validate_structural_integrity(
            building_height=15.0,
            num_floors=5,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        # Taller building should have higher wind load
        assert result_high["loads"]["wind_load_kn"] > result_low["loads"]["wind_load_kn"]
    
    def test_seismic_zone_impact(self):
        """Test that higher seismic zones have higher seismic loads."""
        result_low = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        result_high = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="high",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        # High seismic zone should have higher seismic load
        assert result_high["loads"]["seismic_load_kn"] > result_low["loads"]["seismic_load_kn"]
    
    def test_building_type_live_load(self):
        """Test that commercial buildings have higher live loads."""
        result_residential = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        result_commercial = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="commercial",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        # Commercial should have higher live load
        assert result_commercial["loads"]["live_load_kn"] > result_residential["loads"]["live_load_kn"]
    
    def test_foundation_requirements(self):
        """Test foundation requirements calculation."""
        result = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        foundation = result["foundation"]
        assert "type" in foundation
        assert "required_area_m2" in foundation
        assert "required_depth_m" in foundation
        assert "bearing_capacity_kn_m2" in foundation
        assert foundation["required_area_m2"] > 0
    
    def test_material_strength(self):
        """Test different materials have different strengths."""
        result = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        assert "material_strength_mpa" in result
        assert result["material_strength_mpa"] == 25.0  # M25 concrete
    
    def test_recommendations_provided(self):
        """Test that structural recommendations are provided."""
        result = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.23
        )
        
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
    
    def test_column_validation_basic(self):
        """Test basic column validation."""
        result = structural_service.validate_column_design(
            column_height=3.0,
            axial_load=500.0,
            column_size=0.3,
            material="concrete"
        )
        
        assert "is_safe" in result
        assert "safety_factor" in result
        assert "actual_stress_mpa" in result
        assert "allowable_stress_mpa" in result
        assert "slenderness_ratio" in result
    
    def test_column_slenderness(self):
        """Test column slenderness ratio calculation."""
        result = structural_service.validate_column_design(
            column_height=3.0,
            axial_load=500.0,
            column_size=0.3,
            material="concrete"
        )
        
        expected_slenderness = 3.0 / 0.3
        assert abs(result["slenderness_ratio"] - expected_slenderness) < 0.1
    
    def test_column_safety_factor(self):
        """Test column safety factor meets minimum."""
        result = structural_service.validate_column_design(
            column_height=3.0,
            axial_load=200.0,  # Low load
            column_size=0.4,  # Large column
            material="concrete"
        )
        
        # Should be safe with low load and large column
        assert result["is_safe"] is True
        assert result["safety_factor"] >= 2.0
    
    def test_wall_thickness_impact(self):
        """Test that thicker walls improve safety."""
        result_thin = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.15
        )
        
        result_thick = structural_service.validate_structural_integrity(
            building_height=10.0,
            num_floors=3,
            floor_area=100.0,
            building_type="residential",
            location_zone="low",
            foundation_type="shallow",
            material="concrete",
            wall_thickness=0.30
        )
        
        # Thicker walls mean more dead load but better structure
        assert result_thick["loads"]["dead_load_kn"] > result_thin["loads"]["dead_load_kn"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
