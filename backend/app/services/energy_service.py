"""
Energy Efficiency Validation Service for Smart City Planning System.

This service calculates energy consumption, generates energy ratings,
and provides optimization recommendations for sustainable building design.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EnergyService:
    """Service for calculating building energy efficiency and sustainability metrics."""
    
    # Constants for Sri Lankan climate
    AVERAGE_TEMP_COLOMBO = 27.5  # °C
    COOLING_DEGREE_DAYS = 3650  # Annual cooling degree days
    SOLAR_RADIATION_AVG = 5.5  # kWh/m²/day average for Sri Lanka
    
    # Energy consumption factors (kWh/m²/year)
    LIGHTING_FACTOR = 15.0
    APPLIANCES_FACTOR = 25.0
    HVAC_BASE_FACTOR = 50.0
    
    # U-values (W/m²K) - thermal transmittance
    U_VALUE_WALL_GOOD = 0.35
    U_VALUE_WALL_POOR = 1.5
    U_VALUE_ROOF_GOOD = 0.25
    U_VALUE_ROOF_POOR = 1.0
    U_VALUE_WINDOW_GOOD = 1.8
    U_VALUE_WINDOW_POOR = 5.0
    
    # Energy rating thresholds (kWh/m²/year)
    RATING_A_PLUS = 50
    RATING_A = 75
    RATING_B = 100
    RATING_C = 150
    RATING_D = 200
    
    def __init__(self):
        """Initialize the energy service."""
        pass
    
    def calculate_building_energy(
        self,
        floor_area: float,
        building_volume: float,
        window_area: float,
        orientation: str = "north",
        insulation_quality: str = "medium",
        num_floors: int = 1,
        building_type: str = "residential"
    ) -> Dict[str, any]:
        """
        Calculate comprehensive energy consumption for a building.
        
        Args:
            floor_area: Total floor area in m²
            building_volume: Building volume in m³
            window_area: Total window area in m²
            orientation: Building orientation (north, south, east, west)
            insulation_quality: Insulation quality (poor, medium, good)
            num_floors: Number of floors
            building_type: Type of building (residential, commercial, mixed)
            
        Returns:
            Dictionary containing energy calculations and rating
        """
        try:
            # Calculate individual components
            heating_cooling = self._calculate_hvac_energy(
                building_volume, window_area, insulation_quality, orientation
            )
            
            lighting = self._calculate_lighting_energy(
                floor_area, window_area, building_type
            )
            
            appliances = self._calculate_appliances_energy(
                floor_area, building_type
            )
            
            solar_gain = self._calculate_solar_gain(
                window_area, orientation
            )
            
            # Total annual energy consumption
            total_energy = heating_cooling + lighting + appliances - solar_gain
            
            # Energy per square meter
            energy_per_m2 = total_energy / floor_area if floor_area > 0 else 0
            
            # Generate energy rating
            rating = self._generate_energy_rating(energy_per_m2)
            
            # Calculate CO2 emissions (kg CO2/year)
            # Sri Lanka electricity grid: ~0.7 kg CO2/kWh
            co2_emissions = total_energy * 0.7
            
            # Get optimization recommendations
            recommendations = self._get_optimization_recommendations(
                energy_per_m2, insulation_quality, window_area, floor_area
            )
            
            return {
                "total_energy_kwh_year": round(total_energy, 2),
                "energy_per_m2": round(energy_per_m2, 2),
                "rating": rating,
                "breakdown": {
                    "heating_cooling": round(heating_cooling, 2),
                    "lighting": round(lighting, 2),
                    "appliances": round(appliances, 2),
                    "solar_gain": round(solar_gain, 2)
                },
                "co2_emissions_kg_year": round(co2_emissions, 2),
                "recommendations": recommendations,
                "is_sustainable": rating in ["A+", "A", "B"],
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Energy calculation error: {e}")
            raise
    
    def _calculate_hvac_energy(
        self,
        volume: float,
        window_area: float,
        insulation: str,
        orientation: str
    ) -> float:
        """Calculate heating/cooling energy consumption."""
        # Get U-value based on insulation quality
        u_value_map = {
            "poor": self.U_VALUE_WALL_POOR,
            "medium": (self.U_VALUE_WALL_GOOD + self.U_VALUE_WALL_POOR) / 2,
            "good": self.U_VALUE_WALL_GOOD
        }
        u_value = u_value_map.get(insulation, self.U_VALUE_WALL_POOR)
        
        # Base HVAC energy
        base_energy = volume * self.HVAC_BASE_FACTOR / 100
        
        # Adjust for insulation
        insulation_factor = u_value / self.U_VALUE_WALL_GOOD
        
        # Adjust for window area (more windows = more heat gain)
        window_factor = 1 + (window_area / (volume ** (2/3))) * 0.5
        
        # Adjust for orientation (south/west facing = more cooling needed)
        orientation_factors = {
            "north": 0.9,
            "south": 1.1,
            "east": 1.0,
            "west": 1.15
        }
        orientation_factor = orientation_factors.get(orientation.lower(), 1.0)
        
        return base_energy * insulation_factor * window_factor * orientation_factor
    
    def _calculate_lighting_energy(
        self,
        floor_area: float,
        window_area: float,
        building_type: str
    ) -> float:
        """Calculate lighting energy consumption."""
        # Base lighting energy
        base_lighting = floor_area * self.LIGHTING_FACTOR
        
        # Adjust for natural light (more windows = less artificial lighting)
        window_to_floor_ratio = window_area / floor_area if floor_area > 0 else 0
        natural_light_reduction = min(0.3, window_to_floor_ratio * 0.5)
        
        # Adjust for building type
        type_factors = {
            "residential": 1.0,
            "commercial": 1.3,
            "mixed": 1.15
        }
        type_factor = type_factors.get(building_type, 1.0)
        
        return base_lighting * (1 - natural_light_reduction) * type_factor
    
    def _calculate_appliances_energy(
        self,
        floor_area: float,
        building_type: str
    ) -> float:
        """Calculate appliances and equipment energy consumption."""
        # Base appliances energy
        base_appliances = floor_area * self.APPLIANCES_FACTOR
        
        # Adjust for building type
        type_factors = {
            "residential": 1.0,
            "commercial": 1.5,
            "mixed": 1.25
        }
        type_factor = type_factors.get(building_type, 1.0)
        
        return base_appliances * type_factor
    
    def _calculate_solar_gain(
        self,
        window_area: float,
        orientation: str
    ) -> float:
        """Calculate solar energy gain (passive heating/lighting)."""
        # Solar radiation varies by orientation
        orientation_factors = {
            "north": 0.6,
            "south": 1.0,
            "east": 0.8,
            "west": 0.8
        }
        orientation_factor = orientation_factors.get(orientation.lower(), 0.7)
        
        # Annual solar gain (kWh/year)
        # Assuming 30% of solar radiation is useful
        solar_gain = window_area * self.SOLAR_RADIATION_AVG * 365 * 0.3 * orientation_factor
        
        return solar_gain
    
    def _generate_energy_rating(self, energy_per_m2: float) -> str:
        """Generate energy efficiency rating based on consumption."""
        if energy_per_m2 <= self.RATING_A_PLUS:
            return "A+"
        elif energy_per_m2 <= self.RATING_A:
            return "A"
        elif energy_per_m2 <= self.RATING_B:
            return "B"
        elif energy_per_m2 <= self.RATING_C:
            return "C"
        elif energy_per_m2 <= self.RATING_D:
            return "D"
        else:
            return "E"
    
    def _get_optimization_recommendations(
        self,
        energy_per_m2: float,
        insulation: str,
        window_area: float,
        floor_area: float
    ) -> List[str]:
        """Generate energy optimization recommendations."""
        recommendations = []
        
        # Rating-based recommendations
        if energy_per_m2 > self.RATING_B:
            recommendations.append(
                "⚠️ Energy consumption is high. Consider implementing energy-saving measures."
            )
        
        # Insulation recommendations
        if insulation in ["poor", "medium"]:
            recommendations.append(
                "🏠 Improve building insulation to reduce heating/cooling costs by up to 30%."
            )
        
        # Window recommendations
        window_ratio = window_area / floor_area if floor_area > 0 else 0
        if window_ratio < 0.1:
            recommendations.append(
                "🪟 Increase window area to 10-15% of floor area for better natural lighting."
            )
        elif window_ratio > 0.25:
            recommendations.append(
                "🪟 Excessive window area may increase cooling costs. Consider reducing to 15-20%."
            )
        
        # Solar recommendations
        recommendations.append(
            "☀️ Install solar panels to offset 20-40% of energy consumption."
        )
        
        # LED lighting
        recommendations.append(
            "💡 Use LED lighting to reduce lighting energy by 75% compared to incandescent bulbs."
        )
        
        # HVAC efficiency
        if energy_per_m2 > self.RATING_C:
            recommendations.append(
                "❄️ Install high-efficiency HVAC systems (SEER ≥ 16) to reduce cooling costs."
            )
        
        # Green building
        if energy_per_m2 <= self.RATING_A:
            recommendations.append(
                "🌟 Excellent! Consider applying for Green Building certification."
            )
        
        return recommendations
    
    def calculate_solar_panel_potential(
        self,
        roof_area: float,
        orientation: str = "south",
        tilt_angle: float = 10.0
    ) -> Dict[str, float]:
        """
        Calculate solar panel energy generation potential.
        
        Args:
            roof_area: Available roof area in m²
            orientation: Roof orientation
            tilt_angle: Panel tilt angle in degrees
            
        Returns:
            Dictionary with solar potential calculations
        """
        # Panel efficiency (typical: 18-20%)
        panel_efficiency = 0.18
        
        # System losses (inverter, wiring, shading: ~15%)
        system_efficiency = 0.85
        
        # Usable roof area (accounting for spacing, maintenance access)
        usable_area = roof_area * 0.75
        
        # Orientation factor
        orientation_factors = {
            "north": 0.7,
            "south": 1.0,
            "east": 0.85,
            "west": 0.85
        }
        orientation_factor = orientation_factors.get(orientation.lower(), 0.8)
        
        # Tilt factor (optimal for Sri Lanka: 7-10 degrees)
        optimal_tilt = 8.5
        tilt_factor = 1 - abs(tilt_angle - optimal_tilt) * 0.01
        
        # Annual energy generation (kWh/year)
        annual_generation = (
            usable_area *
            self.SOLAR_RADIATION_AVG * 365 *
            panel_efficiency *
            system_efficiency *
            orientation_factor *
            tilt_factor
        )
        
        # System capacity (kW)
        system_capacity = usable_area * 0.15  # ~150W per m²
        
        # Cost estimate (USD) - typical: $1000-1500 per kW in Sri Lanka
        installation_cost = system_capacity * 1200
        
        # Annual savings (assuming LKR 25/kWh, ~$0.08/kWh)
        annual_savings_usd = annual_generation * 0.08
        
        # Payback period (years)
        payback_period = installation_cost / annual_savings_usd if annual_savings_usd > 0 else 0
        
        return {
            "usable_roof_area_m2": round(usable_area, 2),
            "system_capacity_kw": round(system_capacity, 2),
            "annual_generation_kwh": round(annual_generation, 2),
            "installation_cost_usd": round(installation_cost, 2),
            "annual_savings_usd": round(annual_savings_usd, 2),
            "payback_period_years": round(payback_period, 1),
            "co2_offset_kg_year": round(annual_generation * 0.7, 2),
            "is_viable": payback_period < 10
        }


# Singleton instance
energy_service = EnergyService()
