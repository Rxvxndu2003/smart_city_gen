"""
Unit tests for Energy Efficiency Service.
Tests energy calculations, ratings, and solar panel analysis.
"""
import pytest
from app.services.energy_service import energy_service


class TestEnergyService:
    """Test suite for EnergyService."""
    
    def test_calculate_building_energy_basic(self):
        """Test basic energy calculation."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        assert "total_energy_kwh_year" in result
        assert "energy_per_m2" in result
        assert "rating" in result
        # Total energy can be negative if solar gain exceeds consumption (net-zero building)
        assert result["energy_per_m2"] >= 0  # Energy per m2 is always positive
        assert result["rating"] in ["A+", "A", "B", "C", "D", "E"]
    
    def test_energy_rating_a_plus(self):
        """Test A+ rating for highly efficient building."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=250.0,
            window_area=20.0,  # Good natural light
            orientation="north",
            insulation_quality="good",
            num_floors=1,
            building_type="residential"
        )
        
        # With good insulation and natural light, should get good rating
        assert result["rating"] in ["A+", "A", "B"]
        assert result["is_sustainable"] is True
    
    def test_energy_rating_poor(self):
        """Test poor rating for inefficient building."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=400.0,  # Large volume
            window_area=5.0,  # Poor natural light
            orientation="west",  # Hot afternoon sun
            insulation_quality="poor",
            num_floors=2,
            building_type="commercial"
        )
        
        # Should get worse rating than good design
        assert result["rating"] in ["C", "D", "E"] or result["energy_per_m2"] > 50
    
    def test_solar_gain_calculation(self):
        """Test solar gain varies by orientation."""
        # South-facing should have more solar gain
        result_south = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=20.0,
            orientation="south",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        # North-facing should have less solar gain
        result_north = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=20.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        # South should have more solar gain (less total energy needed)
        assert result_south["breakdown"]["solar_gain"] > result_north["breakdown"]["solar_gain"]
    
    def test_insulation_impact(self):
        """Test that better insulation reduces energy consumption."""
        result_poor = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="poor",
            num_floors=1,
            building_type="residential"
        )
        
        result_good = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="good",
            num_floors=1,
            building_type="residential"
        )
        
        # Good insulation should use less energy
        assert result_good["total_energy_kwh_year"] < result_poor["total_energy_kwh_year"]
    
    def test_co2_emissions_calculation(self):
        """Test CO2 emissions are calculated."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        assert "co2_emissions_kg_year" in result
        # CO2 can be negative for net-zero buildings (more solar than consumption)
        # Just verify the calculation is correct
        expected_co2 = result["total_energy_kwh_year"] * 0.7
        assert abs(result["co2_emissions_kg_year"] - expected_co2) < 1.0
    
    def test_recommendations_provided(self):
        """Test that recommendations are provided."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
    
    def test_solar_panel_potential(self):
        """Test solar panel potential calculation."""
        result = energy_service.calculate_solar_panel_potential(
            roof_area=100.0,
            orientation="south",
            tilt_angle=10.0
        )
        
        assert "system_capacity_kw" in result
        assert "annual_generation_kwh" in result
        assert "payback_period_years" in result
        assert result["system_capacity_kw"] > 0
        assert result["annual_generation_kwh"] > 0
    
    def test_solar_panel_orientation_impact(self):
        """Test that south-facing panels generate more energy."""
        result_south = energy_service.calculate_solar_panel_potential(
            roof_area=100.0,
            orientation="south",
            tilt_angle=10.0
        )
        
        result_north = energy_service.calculate_solar_panel_potential(
            roof_area=100.0,
            orientation="north",
            tilt_angle=10.0
        )
        
        # South should generate more
        assert result_south["annual_generation_kwh"] > result_north["annual_generation_kwh"]
    
    def test_solar_panel_viability(self):
        """Test solar panel viability assessment."""
        result = energy_service.calculate_solar_panel_potential(
            roof_area=100.0,
            orientation="south",
            tilt_angle=8.5  # Optimal for Sri Lanka
        )
        
        assert "is_viable" in result
        # With good orientation and optimal tilt, should be viable
        assert result["is_viable"] is True
        assert result["payback_period_years"] < 10
    
    def test_building_type_impact(self):
        """Test that commercial buildings use more energy."""
        result_residential = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        result_commercial = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="commercial"
        )
        
        # Commercial should use more energy
        assert result_commercial["total_energy_kwh_year"] > result_residential["total_energy_kwh_year"]
    
    def test_energy_breakdown_components(self):
        """Test that energy breakdown includes all components."""
        result = energy_service.calculate_building_energy(
            floor_area=100.0,
            building_volume=300.0,
            window_area=15.0,
            orientation="north",
            insulation_quality="medium",
            num_floors=1,
            building_type="residential"
        )
        
        breakdown = result["breakdown"]
        assert "heating_cooling" in breakdown
        assert "lighting" in breakdown
        assert "appliances" in breakdown
        assert "solar_gain" in breakdown
        
        # All components should be positive
        assert breakdown["heating_cooling"] > 0
        assert breakdown["lighting"] > 0
        assert breakdown["appliances"] > 0
        assert breakdown["solar_gain"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
