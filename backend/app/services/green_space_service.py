"""
Green Space Optimization Service for Smart City Planning System.

This service calculates green space requirements, optimizes park placement,
and analyzes environmental sustainability metrics.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GreenSpaceService:
    """Service for green space optimization and environmental analysis."""
    
    # UDA requirements for Sri Lanka
    MIN_GREEN_SPACE_RESIDENTIAL = 15.0  # 15% minimum for residential
    MIN_GREEN_SPACE_COMMERCIAL = 10.0   # 10% minimum for commercial
    MIN_GREEN_SPACE_MIXED = 12.5        # 12.5% for mixed-use
    
    RECOMMENDED_GREEN_SPACE = 20.0      # 20% recommended for sustainability
    
    # Tree coverage factors
    TREE_CANOPY_AREA = 25.0  # m² average canopy area per tree
    TREES_PER_HECTARE_MIN = 40  # Minimum trees per hectare
    TREES_PER_HECTARE_RECOMMENDED = 80  # Recommended for urban areas
    
    # Environmental factors
    COOLING_FACTOR_PER_PERCENT = 0.5  # °C reduction per 10% green space
    CO2_ABSORPTION_PER_TREE = 22  # kg CO2 per year per tree
    
    def __init__(self):
        """Initialize the green space service."""
        pass
    
    def calculate_green_space_requirements(
        self,
        total_area: float,
        building_type: str = "residential",
        num_buildings: int = 1,
        building_footprint: float = 0
    ) -> Dict[str, any]:
        """
        Calculate green space requirements and optimization.
        
        Args:
            total_area: Total project area in m²
            building_type: Type of development
            num_buildings: Number of buildings
            building_footprint: Total building footprint in m²
            
        Returns:
            Dictionary containing green space analysis
        """
        try:
            # Get minimum requirement
            min_requirement_map = {
                "residential": self.MIN_GREEN_SPACE_RESIDENTIAL,
                "commercial": self.MIN_GREEN_SPACE_COMMERCIAL,
                "mixed": self.MIN_GREEN_SPACE_MIXED
            }
            min_percentage = min_requirement_map.get(building_type, self.MIN_GREEN_SPACE_RESIDENTIAL)
            
            # Calculate required green space
            min_green_space = total_area * (min_percentage / 100)
            recommended_green_space = total_area * (self.RECOMMENDED_GREEN_SPACE / 100)
            
            # Available space for green areas
            available_space = total_area - building_footprint
            
            # Calculate actual green space percentage
            actual_percentage = (available_space / total_area * 100) if total_area > 0 else 0
            
            # Compliance check
            is_compliant = actual_percentage >= min_percentage
            is_sustainable = actual_percentage >= self.RECOMMENDED_GREEN_SPACE
            
            # Optimize park placement
            parks = self._optimize_park_placement(available_space, num_buildings)
            
            # Calculate tree requirements
            trees = self._calculate_tree_coverage(available_space)
            
            # Environmental benefits
            benefits = self._calculate_environmental_benefits(
                available_space, trees["recommended_trees"]
            )
            
            # Get recommendations
            recommendations = self._get_green_space_recommendations(
                actual_percentage, min_percentage, is_sustainable
            )
            
            return {
                "is_compliant": is_compliant,
                "is_sustainable": is_sustainable,
                "green_space_percentage": round(actual_percentage, 2),
                "min_required_percentage": min_percentage,
                "recommended_percentage": self.RECOMMENDED_GREEN_SPACE,
                "areas": {
                    "total_area_m2": round(total_area, 2),
                    "building_footprint_m2": round(building_footprint, 2),
                    "available_green_space_m2": round(available_space, 2),
                    "min_required_m2": round(min_green_space, 2),
                    "recommended_m2": round(recommended_green_space, 2)
                },
                "parks": parks,
                "trees": trees,
                "environmental_benefits": benefits,
                "recommendations": recommendations,
                "compliance_status": "PASS" if is_compliant else "FAIL",
                "calculated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Green space calculation error: {e}")
            raise
    
    def _optimize_park_placement(
        self,
        available_area: float,
        num_buildings: int
    ) -> Dict[str, any]:
        """Optimize park and garden placement."""
        # Distribute green space
        # 40% parks, 30% gardens, 30% landscaping
        park_area = available_area * 0.4
        garden_area = available_area * 0.3
        landscaping_area = available_area * 0.3
        
        # Number of parks (one per 5000 m² or one per 5 buildings)
        num_parks = max(1, int(available_area / 5000), int(num_buildings / 5))
        
        # Average park size
        avg_park_size = park_area / num_parks if num_parks > 0 else 0
        
        # Park types based on size
        park_types = []
        if avg_park_size > 2000:
            park_types.append("Community Park")
        elif avg_park_size > 500:
            park_types.append("Neighborhood Park")
        else:
            park_types.append("Pocket Park")
        
        return {
            "total_parks": num_parks,
            "park_area_m2": round(park_area, 2),
            "garden_area_m2": round(garden_area, 2),
            "landscaping_area_m2": round(landscaping_area, 2),
            "average_park_size_m2": round(avg_park_size, 2),
            "park_types": park_types
        }
    
    def _calculate_tree_coverage(
        self,
        green_area: float
    ) -> Dict[str, any]:
        """Calculate tree coverage requirements."""
        # Convert to hectares
        area_hectares = green_area / 10000
        
        # Calculate tree requirements
        min_trees = int(area_hectares * self.TREES_PER_HECTARE_MIN)
        recommended_trees = int(area_hectares * self.TREES_PER_HECTARE_RECOMMENDED)
        
        # Tree canopy coverage
        min_canopy = min_trees * self.TREE_CANOPY_AREA
        recommended_canopy = recommended_trees * self.TREE_CANOPY_AREA
        
        # Coverage percentage
        min_coverage_percent = (min_canopy / green_area * 100) if green_area > 0 else 0
        recommended_coverage_percent = (recommended_canopy / green_area * 100) if green_area > 0 else 0
        
        return {
            "min_trees": min_trees,
            "recommended_trees": recommended_trees,
            "min_canopy_area_m2": round(min_canopy, 2),
            "recommended_canopy_area_m2": round(recommended_canopy, 2),
            "min_coverage_percentage": round(min_coverage_percent, 2),
            "recommended_coverage_percentage": round(recommended_coverage_percent, 2)
        }
    
    def _calculate_environmental_benefits(
        self,
        green_area: float,
        num_trees: int
    ) -> Dict[str, any]:
        """Calculate environmental benefits of green spaces."""
        # Temperature reduction (urban heat island mitigation)
        green_percentage = min(100, (green_area / 10000) * 100)  # Assume 1 hectare base
        temp_reduction = green_percentage * self.COOLING_FACTOR_PER_PERCENT / 10
        
        # CO2 absorption
        annual_co2_absorption = num_trees * self.CO2_ABSORPTION_PER_TREE
        
        # Air quality improvement (qualitative)
        air_quality_score = min(100, (num_trees / 100) * 10)
        
        # Biodiversity score (based on area and tree diversity)
        biodiversity_score = min(100, (green_area / 1000) * 5 + (num_trees / 50) * 5)
        
        return {
            "temperature_reduction_celsius": round(temp_reduction, 2),
            "annual_co2_absorption_kg": round(annual_co2_absorption, 2),
            "air_quality_score": round(air_quality_score, 2),
            "biodiversity_score": round(biodiversity_score, 2),
            "benefits_summary": [
                f"Reduces urban temperature by ~{temp_reduction:.1f}°C",
                f"Absorbs ~{annual_co2_absorption:.0f} kg CO2 annually",
                f"Improves air quality and reduces pollution",
                f"Enhances biodiversity and ecosystem health"
            ]
        }
    
    def _get_green_space_recommendations(
        self,
        actual_percentage: float,
        min_percentage: float,
        is_sustainable: bool
    ) -> List[str]:
        """Generate green space recommendations."""
        recommendations = []
        
        # Compliance recommendations
        if actual_percentage < min_percentage:
            deficit = min_percentage - actual_percentage
            recommendations.append(
                f"⚠️ CRITICAL: Green space is {deficit:.1f}% below UDA minimum requirement!"
            )
            recommendations.append(
                "🏗️ Reduce building footprint or increase total project area"
            )
        elif actual_percentage < self.RECOMMENDED_GREEN_SPACE:
            recommendations.append(
                f"⚡ Green space meets minimum but below recommended {self.RECOMMENDED_GREEN_SPACE}%"
            )
            recommendations.append(
                "🌳 Consider adding more parks and gardens for sustainability"
            )
        else:
            recommendations.append(
                "✅ Excellent green space allocation! Meets sustainability goals."
            )
        
        # Sustainability recommendations
        if is_sustainable:
            recommendations.append(
                "🌟 Eligible for Green Building certification"
            )
        
        # General recommendations
        recommendations.append(
            "🌲 Plant native Sri Lankan species for better adaptation"
        )
        recommendations.append(
            "💧 Include rain gardens for stormwater management"
        )
        recommendations.append(
            "🦋 Create wildlife corridors to enhance biodiversity"
        )
        recommendations.append(
            "🏃 Design walking paths and recreational areas"
        )
        recommendations.append(
            "🌺 Mix trees, shrubs, and ground cover for layered greenery"
        )
        
        return recommendations
    
    def calculate_urban_heat_island_effect(
        self,
        green_space_percentage: float,
        building_density: float,
        pavement_area: float,
        total_area: float
    ) -> Dict[str, any]:
        """
        Calculate urban heat island effect and mitigation.
        
        Args:
            green_space_percentage: Percentage of green space
            building_density: Building coverage percentage
            pavement_area: Paved area in m²
            total_area: Total area in m²
            
        Returns:
            Heat island analysis
        """
        # Base temperature increase (°C)
        base_increase = 3.0  # Typical urban heat island effect
        
        # Mitigation from green space
        green_mitigation = green_space_percentage * self.COOLING_FACTOR_PER_PERCENT / 10
        
        # Heat contribution from buildings and pavement
        building_contribution = building_density * 0.05
        pavement_percentage = (pavement_area / total_area * 100) if total_area > 0 else 0
        pavement_contribution = pavement_percentage * 0.03
        
        # Net temperature increase
        net_increase = base_increase + building_contribution + pavement_contribution - green_mitigation
        net_increase = max(0, net_increase)
        
        # Mitigation strategies
        strategies = []
        if net_increase > 2.0:
            strategies.append("Increase green space coverage")
            strategies.append("Use cool roofs and reflective materials")
            strategies.append("Plant more trees for shading")
        if pavement_percentage > 30:
            strategies.append("Use permeable paving materials")
            strategies.append("Reduce paved areas where possible")
        
        return {
            "base_heat_island_effect_celsius": base_increase,
            "green_space_mitigation_celsius": round(green_mitigation, 2),
            "building_contribution_celsius": round(building_contribution, 2),
            "pavement_contribution_celsius": round(pavement_contribution, 2),
            "net_temperature_increase_celsius": round(net_increase, 2),
            "severity": "High" if net_increase > 2.5 else "Medium" if net_increase > 1.5 else "Low",
            "mitigation_strategies": strategies
        }


# Singleton instance
green_space_service = GreenSpaceService()
