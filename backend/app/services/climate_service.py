"""
Climate Data Integration Service for Smart City Planning System.

This service integrates weather data and provides climate-aware design recommendations.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ClimateService:
    """Service for climate data integration and analysis."""
    
    # Sri Lankan climate data (averages for Colombo)
    CLIMATE_DATA = {
        "colombo": {
            "avg_temp_celsius": 27.5,
            "avg_humidity_percent": 77,
            "annual_rainfall_mm": 2400,
            "avg_solar_radiation_kwh_m2_day": 5.5,
            "prevailing_wind_direction": "southwest",
            "avg_wind_speed_ms": 3.5,
            "monsoon_months": ["May", "June", "October", "November"]
        },
        "kandy": {
            "avg_temp_celsius": 24.0,
            "avg_humidity_percent": 80,
            "annual_rainfall_mm": 1900,
            "avg_solar_radiation_kwh_m2_day": 5.0,
            "prevailing_wind_direction": "southwest",
            "avg_wind_speed_ms": 2.5,
            "monsoon_months": ["May", "June", "October", "November"]
        },
        "jaffna": {
            "avg_temp_celsius": 28.5,
            "avg_humidity_percent": 75,
            "annual_rainfall_mm": 1300,
            "avg_solar_radiation_kwh_m2_day": 6.0,
            "prevailing_wind_direction": "northeast",
            "avg_wind_speed_ms": 4.0,
            "monsoon_months": ["October", "November", "December"]
        }
    }
    
    def __init__(self):
        """Initialize the climate service."""
        pass
    
    def get_climate_data(
        self,
        location: str = "colombo",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Get climate data for a location.
        
        Args:
            location: Location name (colombo, kandy, jaffna)
            latitude: Latitude (for future API integration)
            longitude: Longitude (for future API integration)
            
        Returns:
            Climate data dictionary
        """
        try:
            # Get climate data for location
            location_key = location.lower()
            climate = self.CLIMATE_DATA.get(location_key, self.CLIMATE_DATA["colombo"])
            
            # TODO: Integrate with OpenWeatherMap API or similar
            # For now, return stored data
            
            return {
                "location": location,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "climate_data": climate,
                "data_source": "Historical averages",
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Get climate data error: {e}")
            raise
    
    def generate_climate_recommendations(
        self,
        location: str = "colombo",
        building_type: str = "residential"
    ) -> Dict[str, any]:
        """
        Generate climate-aware design recommendations.
        
        Args:
            location: Location name
            building_type: Type of building
            
        Returns:
            Design recommendations based on climate
        """
        try:
            # Get climate data
            climate_data = self.get_climate_data(location)
            climate = climate_data["climate_data"]
            
            recommendations = []
            
            # Temperature-based recommendations
            avg_temp = climate["avg_temp_celsius"]
            if avg_temp > 27:
                recommendations.append({
                    "category": "Cooling",
                    "priority": "High",
                    "recommendation": "Use natural ventilation and cross-ventilation design",
                    "reason": f"High average temperature ({avg_temp}°C)"
                })
                recommendations.append({
                    "category": "Cooling",
                    "priority": "High",
                    "recommendation": "Install high-efficiency air conditioning (SEER ≥ 16)",
                    "reason": "Reduce cooling costs in hot climate"
                })
                recommendations.append({
                    "category": "Shading",
                    "priority": "High",
                    "recommendation": "Provide external shading devices (overhangs, louvers)",
                    "reason": "Reduce solar heat gain"
                })
            
            # Humidity-based recommendations
            humidity = climate["avg_humidity_percent"]
            if humidity > 75:
                recommendations.append({
                    "category": "Ventilation",
                    "priority": "High",
                    "recommendation": "Ensure adequate ventilation to prevent mold and dampness",
                    "reason": f"High humidity ({humidity}%)"
                })
                recommendations.append({
                    "category": "Materials",
                    "priority": "Medium",
                    "recommendation": "Use moisture-resistant materials and finishes",
                    "reason": "Prevent deterioration in humid conditions"
                })
            
            # Rainfall-based recommendations
            rainfall = climate["annual_rainfall_mm"]
            if rainfall > 2000:
                recommendations.append({
                    "category": "Drainage",
                    "priority": "High",
                    "recommendation": "Design robust stormwater drainage system",
                    "reason": f"High annual rainfall ({rainfall}mm)"
                })
                recommendations.append({
                    "category": "Roofing",
                    "priority": "High",
                    "recommendation": "Use sloped roofs with proper waterproofing",
                    "reason": "Handle heavy rainfall effectively"
                })
                recommendations.append({
                    "category": "Landscaping",
                    "priority": "Medium",
                    "recommendation": "Include rain gardens and permeable surfaces",
                    "reason": "Manage stormwater runoff"
                })
            
            # Solar radiation recommendations
            solar = climate["avg_solar_radiation_kwh_m2_day"]
            if solar > 5.0:
                recommendations.append({
                    "category": "Solar Energy",
                    "priority": "High",
                    "recommendation": "Install solar panels for energy generation",
                    "reason": f"Excellent solar potential ({solar} kWh/m²/day)"
                })
                recommendations.append({
                    "category": "Orientation",
                    "priority": "Medium",
                    "recommendation": "Orient building to minimize east-west sun exposure",
                    "reason": "Reduce cooling load from solar heat gain"
                })
            
            # Wind-based recommendations
            wind_direction = climate["prevailing_wind_direction"]
            recommendations.append({
                "category": "Orientation",
                "priority": "Medium",
                "recommendation": f"Orient openings toward {wind_direction} for natural ventilation",
                "reason": f"Utilize prevailing {wind_direction} winds"
            })
            
            # Monsoon recommendations
            monsoon_months = climate["monsoon_months"]
            recommendations.append({
                "category": "Construction Planning",
                "priority": "Medium",
                "recommendation": f"Avoid major construction during monsoon months: {', '.join(monsoon_months)}",
                "reason": "Minimize weather-related delays"
            })
            
            # General tropical climate recommendations
            recommendations.append({
                "category": "Materials",
                "priority": "Medium",
                "recommendation": "Use light-colored, reflective roofing materials",
                "reason": "Reduce heat absorption"
            })
            recommendations.append({
                "category": "Landscaping",
                "priority": "High",
                "recommendation": "Plant trees for natural shading and cooling",
                "reason": "Reduce urban heat island effect"
            })
            
            return {
                "location": location,
                "building_type": building_type,
                "climate_summary": {
                    "temperature": f"{avg_temp}°C average",
                    "humidity": f"{humidity}% average",
                    "rainfall": f"{rainfall}mm annual",
                    "solar": f"{solar} kWh/m²/day"
                },
                "recommendations": recommendations,
                "total_recommendations": len(recommendations),
                "high_priority_count": len([r for r in recommendations if r["priority"] == "High"]),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Generate climate recommendations error: {e}")
            raise
    
    def calculate_optimal_orientation(
        self,
        location: str = "colombo"
    ) -> Dict[str, any]:
        """
        Calculate optimal building orientation for climate.
        
        Args:
            location: Location name
            
        Returns:
            Optimal orientation recommendations
        """
        climate_data = self.get_climate_data(location)
        climate = climate_data["climate_data"]
        
        wind_direction = climate["prevailing_wind_direction"]
        
        # Orientation recommendations
        orientations = {
            "primary_facade": "north" if wind_direction == "southwest" else "south",
            "window_orientation": wind_direction,
            "solar_panel_orientation": "south",
            "solar_panel_tilt": 8.5  # Optimal for Sri Lanka (latitude ~7°N)
        }
        
        return {
            "location": location,
            "optimal_orientations": orientations,
            "reasoning": {
                "primary_facade": "Minimize direct sun exposure",
                "window_orientation": f"Maximize natural ventilation from {wind_direction} winds",
                "solar_panels": "Maximize solar energy generation"
            }
        }


# Singleton instance
climate_service = ClimateService()
