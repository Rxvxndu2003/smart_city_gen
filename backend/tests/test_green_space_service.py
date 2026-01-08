"""
Unit tests for Green Space Optimization Service.
Tests green space calculations, UDA compliance, and environmental benefits.
"""
import pytest
from app.services.green_space_service import green_space_service


class TestGreenSpaceService:
    """Test suite for GreenSpaceService."""
    
    def test_calculate_green_space_basic(self):
        """Test basic green space calculation."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        assert "is_compliant" in result
        assert "green_space_percentage" in result
        assert "parks" in result
        assert "trees" in result
        assert "environmental_benefits" in result
    
    def test_uda_compliance_residential(self):
        """Test UDA compliance for residential (15% minimum)."""
        # Compliant case
        result_compliant = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0  # 70% available = compliant
        )
        
        assert result_compliant["is_compliant"] is True
        assert result_compliant["green_space_percentage"] >= 15.0
        
        # Non-compliant case
        result_non_compliant = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=9000.0  # Only 10% available = non-compliant
        )
        
        assert result_non_compliant["is_compliant"] is False
        assert result_non_compliant["green_space_percentage"] < 15.0
    
    def test_uda_compliance_commercial(self):
        """Test UDA compliance for commercial (10% minimum)."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="commercial",
            num_buildings=3,
            building_footprint=8500.0  # 15% available
        )
        
        # Should be compliant (15% > 10% minimum)
        assert result["is_compliant"] is True
        assert result["min_required_percentage"] == 10.0
    
    def test_sustainability_threshold(self):
        """Test sustainability threshold (20%)."""
        result_sustainable = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=2000.0  # 80% available = sustainable
        )
        
        assert result_sustainable["is_sustainable"] is True
        assert result_sustainable["green_space_percentage"] >= 20.0
    
    def test_park_placement_optimization(self):
        """Test park placement optimization."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=10,
            building_footprint=3000.0
        )
        
        parks = result["parks"]
        assert "total_parks" in parks
        assert "park_area_m2" in parks
        assert "garden_area_m2" in parks
        assert "landscaping_area_m2" in parks
        assert parks["total_parks"] > 0
    
    def test_tree_coverage_calculation(self):
        """Test tree coverage requirements."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        trees = result["trees"]
        assert "min_trees" in trees
        assert "recommended_trees" in trees
        assert "min_canopy_area_m2" in trees
        assert trees["recommended_trees"] > trees["min_trees"]
    
    def test_environmental_benefits(self):
        """Test environmental benefits calculation."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        benefits = result["environmental_benefits"]
        assert "temperature_reduction_celsius" in benefits
        assert "annual_co2_absorption_kg" in benefits
        assert "air_quality_score" in benefits
        assert "biodiversity_score" in benefits
        
        # All benefits should be positive
        assert benefits["temperature_reduction_celsius"] >= 0
        assert benefits["annual_co2_absorption_kg"] > 0
    
    def test_co2_absorption_scales_with_trees(self):
        """Test that CO2 absorption increases with more trees."""
        result_small = green_space_service.calculate_green_space_requirements(
            total_area=5000.0,
            building_type="residential",
            num_buildings=3,
            building_footprint=1500.0
        )
        
        result_large = green_space_service.calculate_green_space_requirements(
            total_area=20000.0,
            building_type="residential",
            num_buildings=10,
            building_footprint=6000.0
        )
        
        # Larger area should have more trees and more CO2 absorption
        assert result_large["trees"]["recommended_trees"] > result_small["trees"]["recommended_trees"]
        assert result_large["environmental_benefits"]["annual_co2_absorption_kg"] > \
               result_small["environmental_benefits"]["annual_co2_absorption_kg"]
    
    def test_recommendations_provided(self):
        """Test that recommendations are provided."""
        result = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
    
    def test_urban_heat_island_calculation(self):
        """Test urban heat island effect calculation."""
        result = green_space_service.calculate_urban_heat_island_effect(
            green_space_percentage=20.0,
            building_density=30.0,
            pavement_area=3000.0,
            total_area=10000.0
        )
        
        assert "net_temperature_increase_celsius" in result
        assert "severity" in result
        assert "mitigation_strategies" in result
        assert result["severity"] in ["Low", "Medium", "High"]
    
    def test_green_space_mitigates_heat_island(self):
        """Test that more green space reduces heat island effect."""
        result_low_green = green_space_service.calculate_urban_heat_island_effect(
            green_space_percentage=10.0,
            building_density=40.0,
            pavement_area=4000.0,
            total_area=10000.0
        )
        
        result_high_green = green_space_service.calculate_urban_heat_island_effect(
            green_space_percentage=30.0,
            building_density=40.0,
            pavement_area=4000.0,
            total_area=10000.0
        )
        
        # More green space should reduce temperature increase
        assert result_high_green["net_temperature_increase_celsius"] < \
               result_low_green["net_temperature_increase_celsius"]
    
    def test_building_type_affects_requirements(self):
        """Test that different building types have different requirements."""
        result_residential = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        result_commercial = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="commercial",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        # Residential requires 15%, commercial requires 10%
        assert result_residential["min_required_percentage"] == 15.0
        assert result_commercial["min_required_percentage"] == 10.0
    
    def test_compliance_status(self):
        """Test compliance status is correctly set."""
        result_pass = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=3000.0
        )
        
        result_fail = green_space_service.calculate_green_space_requirements(
            total_area=10000.0,
            building_type="residential",
            num_buildings=5,
            building_footprint=9000.0
        )
        
        assert result_pass["compliance_status"] == "PASS"
        assert result_fail["compliance_status"] == "FAIL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
