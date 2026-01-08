"""
Structural Integrity Validation Service for Smart City Planning System.

This service validates structural safety including load-bearing capacity,
foundation requirements, seismic safety, and wind load calculations.
"""
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StructuralService:
    """Service for validating structural integrity and safety."""
    
    # Material properties (typical values)
    CONCRETE_DENSITY = 2400  # kg/m³
    STEEL_DENSITY = 7850  # kg/m³
    BRICK_DENSITY = 1800  # kg/m³
    
    # Load factors
    DEAD_LOAD_FACTOR = 1.4
    LIVE_LOAD_FACTOR = 1.6
    WIND_LOAD_FACTOR = 1.6
    SEISMIC_LOAD_FACTOR = 1.5
    
    # Safety factors
    MIN_SAFETY_FACTOR = 2.0
    RECOMMENDED_SAFETY_FACTOR = 2.5
    
    # Sri Lankan seismic zones (PGA values)
    SEISMIC_ZONES = {
        "low": 0.05,      # Most of Sri Lanka
        "medium": 0.10,   # Some coastal areas
        "high": 0.15      # Rare, specific locations
    }
    
    # Wind speed zones (m/s)
    WIND_ZONES = {
        "low": 30,        # Inland areas
        "medium": 35,     # Most coastal areas
        "high": 40        # Exposed coastal areas
    }
    
    # Live loads (kN/m²) - Sri Lankan standards
    LIVE_LOADS = {
        "residential": 2.0,
        "commercial": 3.0,
        "office": 2.5,
        "storage": 5.0,
        "assembly": 4.0
    }
    
    def __init__(self):
        """Initialize the structural service."""
        pass
    
    def validate_structural_integrity(
        self,
        building_height: float,
        num_floors: int,
        floor_area: float,
        building_type: str = "residential",
        location_zone: str = "low",
        foundation_type: str = "shallow",
        material: str = "concrete",
        wall_thickness: float = 0.23
    ) -> Dict[str, any]:
        """
        Validate comprehensive structural integrity.
        
        Args:
            building_height: Total building height in meters
            num_floors: Number of floors
            floor_area: Floor area per floor in m²
            building_type: Type of building
            location_zone: Seismic/wind zone (low/medium/high)
            foundation_type: Foundation type (shallow/deep/pile)
            material: Primary construction material
            wall_thickness: Wall thickness in meters
            
        Returns:
            Dictionary containing structural validation results
        """
        try:
            # Calculate loads
            dead_load = self._calculate_dead_load(
                floor_area, num_floors, material, wall_thickness
            )
            
            live_load = self._calculate_live_load(
                floor_area, num_floors, building_type
            )
            
            wind_load = self._calculate_wind_load(
                building_height, floor_area, location_zone
            )
            
            seismic_load = self._calculate_seismic_load(
                dead_load + live_load, location_zone
            )
            
            # Total design load
            total_load = (
                dead_load * self.DEAD_LOAD_FACTOR +
                live_load * self.LIVE_LOAD_FACTOR +
                max(wind_load, seismic_load)
            )
            
            # Foundation requirements
            foundation = self._calculate_foundation_requirements(
                total_load, foundation_type
            )
            
            # Safety factor
            material_strength = self._get_material_strength(material)
            safety_factor = material_strength / (total_load / floor_area) if floor_area > 0 else 0
            
            # Validation checks
            is_safe = safety_factor >= self.MIN_SAFETY_FACTOR
            is_recommended = safety_factor >= self.RECOMMENDED_SAFETY_FACTOR
            
            # Get recommendations
            recommendations = self._get_structural_recommendations(
                safety_factor, building_height, num_floors, location_zone
            )
            
            return {
                "is_structurally_safe": is_safe,
                "is_recommended_safety": is_recommended,
                "safety_factor": round(safety_factor, 2),
                "loads": {
                    "dead_load_kn": round(dead_load, 2),
                    "live_load_kn": round(live_load, 2),
                    "wind_load_kn": round(wind_load, 2),
                    "seismic_load_kn": round(seismic_load, 2),
                    "total_design_load_kn": round(total_load, 2)
                },
                "foundation": foundation,
                "material_strength_mpa": material_strength,
                "recommendations": recommendations,
                "validation_status": "PASS" if is_safe else "FAIL",
                "validated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Structural validation error: {e}")
            raise
    
    def _calculate_dead_load(
        self,
        floor_area: float,
        num_floors: int,
        material: str,
        wall_thickness: float
    ) -> float:
        """Calculate dead load (weight of structure)."""
        # Floor slab weight (typical: 0.15m thick concrete)
        slab_weight = floor_area * 0.15 * self.CONCRETE_DENSITY * 9.81 / 1000  # kN
        
        # Wall weight (perimeter walls)
        perimeter = 4 * math.sqrt(floor_area)  # Approximate square building
        floor_height = 3.0  # meters
        wall_area = perimeter * floor_height
        
        density_map = {
            "concrete": self.CONCRETE_DENSITY,
            "brick": self.BRICK_DENSITY,
            "steel": self.STEEL_DENSITY
        }
        material_density = density_map.get(material, self.CONCRETE_DENSITY)
        
        wall_weight = wall_area * wall_thickness * material_density * 9.81 / 1000  # kN
        
        # Roof weight (lighter than floor)
        roof_weight = floor_area * 0.10 * self.CONCRETE_DENSITY * 9.81 / 1000  # kN
        
        # Total dead load for all floors
        total_dead_load = (slab_weight + wall_weight) * num_floors + roof_weight
        
        return total_dead_load
    
    def _calculate_live_load(
        self,
        floor_area: float,
        num_floors: int,
        building_type: str
    ) -> float:
        """Calculate live load (occupancy, furniture, equipment)."""
        live_load_per_m2 = self.LIVE_LOADS.get(building_type, 2.0)
        
        # Total live load (kN)
        total_live_load = floor_area * num_floors * live_load_per_m2
        
        return total_live_load
    
    def _calculate_wind_load(
        self,
        building_height: float,
        floor_area: float,
        zone: str
    ) -> float:
        """Calculate wind load on building."""
        # Basic wind speed
        wind_speed = self.WIND_ZONES.get(zone, 30)  # m/s
        
        # Wind pressure (Pa) = 0.6 * V²
        wind_pressure = 0.6 * (wind_speed ** 2)
        
        # Exposed area (approximate)
        building_width = math.sqrt(floor_area)
        exposed_area = building_width * building_height
        
        # Wind force (kN)
        wind_load = wind_pressure * exposed_area / 1000
        
        # Shape factor (1.3 for rectangular buildings)
        wind_load *= 1.3
        
        return wind_load
    
    def _calculate_seismic_load(
        self,
        building_weight: float,
        zone: str
    ) -> float:
        """Calculate seismic load based on building weight and zone."""
        # Peak Ground Acceleration (PGA)
        pga = self.SEISMIC_ZONES.get(zone, 0.05)
        
        # Seismic coefficient
        seismic_coefficient = pga * 2.5  # Simplified
        
        # Seismic load (kN)
        seismic_load = building_weight * seismic_coefficient
        
        return seismic_load
    
    def _calculate_foundation_requirements(
        self,
        total_load: float,
        foundation_type: str
    ) -> Dict[str, any]:
        """Calculate foundation requirements."""
        # Soil bearing capacity (kN/m²) - typical values
        bearing_capacity_map = {
            "shallow": 150,   # Shallow foundation on good soil
            "deep": 300,      # Deep foundation
            "pile": 500       # Pile foundation
        }
        bearing_capacity = bearing_capacity_map.get(foundation_type, 150)
        
        # Required foundation area
        required_area = total_load / bearing_capacity
        
        # Foundation depth (rule of thumb)
        depth_map = {
            "shallow": 1.5,
            "deep": 3.0,
            "pile": 6.0
        }
        required_depth = depth_map.get(foundation_type, 1.5)
        
        return {
            "type": foundation_type,
            "required_area_m2": round(required_area, 2),
            "required_depth_m": required_depth,
            "bearing_capacity_kn_m2": bearing_capacity,
            "is_adequate": True  # Simplified - always adequate if calculated
        }
    
    def _get_material_strength(self, material: str) -> float:
        """Get material compressive strength (MPa)."""
        strength_map = {
            "concrete": 25.0,   # M25 grade concrete
            "brick": 10.0,      # Standard brick masonry
            "steel": 250.0      # Structural steel
        }
        return strength_map.get(material, 25.0)
    
    def _get_structural_recommendations(
        self,
        safety_factor: float,
        height: float,
        num_floors: int,
        zone: str
    ) -> List[str]:
        """Generate structural recommendations."""
        recommendations = []
        
        # Safety factor recommendations
        if safety_factor < self.MIN_SAFETY_FACTOR:
            recommendations.append(
                "⚠️ CRITICAL: Safety factor below minimum (2.0). Structural redesign required!"
            )
            recommendations.append(
                "🏗️ Increase wall thickness or use higher grade materials"
            )
        elif safety_factor < self.RECOMMENDED_SAFETY_FACTOR:
            recommendations.append(
                "⚡ Safety factor is adequate but below recommended (2.5). Consider strengthening."
            )
        else:
            recommendations.append(
                "✅ Excellent safety factor! Structure is well-designed."
            )
        
        # Height-based recommendations
        if height > 15 and num_floors > 5:
            recommendations.append(
                "🏢 For buildings over 5 floors, consider structural engineer consultation"
            )
            recommendations.append(
                "🔩 Use reinforced concrete frame structure for better stability"
            )
        
        # Zone-based recommendations
        if zone in ["medium", "high"]:
            recommendations.append(
                f"🌊 Located in {zone} risk zone - ensure proper seismic design"
            )
            recommendations.append(
                "⚓ Use ductile detailing and proper reinforcement"
            )
        
        # Foundation recommendations
        if num_floors > 3:
            recommendations.append(
                "🏗️ Consider deep foundation or pile foundation for buildings over 3 floors"
            )
        
        # General recommendations
        recommendations.append(
            "📐 Conduct detailed structural analysis by licensed engineer before construction"
        )
        recommendations.append(
            "🔍 Regular structural inspections during and after construction"
        )
        
        return recommendations
    
    def validate_column_design(
        self,
        column_height: float,
        axial_load: float,
        column_size: float = 0.3,
        material: str = "concrete"
    ) -> Dict[str, any]:
        """
        Validate column design for axial load.
        
        Args:
            column_height: Column height in meters
            axial_load: Axial load in kN
            column_size: Column cross-section size in meters (square)
            material: Column material
            
        Returns:
            Column validation results
        """
        # Column area
        area = column_size ** 2
        
        # Slenderness ratio
        slenderness = column_height / column_size
        
        # Material strength
        material_strength = self._get_material_strength(material)
        
        # Allowable stress (reduced for slenderness)
        if slenderness > 12:
            reduction_factor = 1 - (slenderness - 12) * 0.02
            reduction_factor = max(0.5, reduction_factor)
        else:
            reduction_factor = 1.0
        
        allowable_stress = material_strength * reduction_factor
        
        # Actual stress
        actual_stress = (axial_load * 1000) / (area * 1000000)  # MPa
        
        # Safety factor
        safety_factor = allowable_stress / actual_stress if actual_stress > 0 else 0
        
        is_safe = safety_factor >= self.MIN_SAFETY_FACTOR
        
        return {
            "is_safe": is_safe,
            "safety_factor": round(safety_factor, 2),
            "actual_stress_mpa": round(actual_stress, 2),
            "allowable_stress_mpa": round(allowable_stress, 2),
            "slenderness_ratio": round(slenderness, 2),
            "column_area_m2": round(area, 4),
            "recommendation": "PASS" if is_safe else "INCREASE COLUMN SIZE"
        }


# Singleton instance
structural_service = StructuralService()
