"""
UDA (Urban Development Authority) House Regulations Validator.
Validates residential house designs against Sri Lankan UDA building regulations.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class UDAHouseValidator:
    """Validator for UDA house building regulations in Sri Lanka."""
    
    def __init__(self):
        """Initialize UDA house validator with regulation rules."""
        self.regulations = self._load_uda_house_regulations()
    
    def _load_uda_house_regulations(self) -> Dict[str, Any]:
        """Load UDA house building regulations."""
        return {
            "setbacks": {
                "front_setback": {
                    "minimum": 10.0,  # feet
                    "description": "Minimum front setback from road boundary",
                    "regulation": "UDA Regulation 2.1.1"
                },
                "rear_setback": {
                    "minimum": 10.0,  # feet
                    "description": "Minimum rear setback",
                    "regulation": "UDA Regulation 2.1.2"
                },
                "side_setback": {
                    "minimum": 5.0,  # feet
                    "description": "Minimum side setback",
                    "regulation": "UDA Regulation 2.1.3"
                }
            },
            "coverage": {
                "max_building_coverage": {
                    "residential": 65.0,  # percentage
                    "description": "Maximum building coverage for residential plots",
                    "regulation": "UDA Regulation 3.2.1"
                }
            },
            "height": {
                "max_floors": {
                    "value": 3,
                    "description": "Maximum number of floors for residential buildings (without special approval)",
                    "regulation": "UDA Regulation 4.1.1"
                },
                "max_height": {
                    "value": 35.0,  # feet
                    "description": "Maximum building height for residential buildings",
                    "regulation": "UDA Regulation 4.1.2"
                },
                "floor_height": {
                    "minimum": 9.0,  # feet
                    "maximum": 12.0,  # feet
                    "description": "Recommended floor to ceiling height",
                    "regulation": "UDA Regulation 4.2.1"
                }
            },
            "rooms": {
                "bedroom": {
                    "min_area": 100.0,  # sq ft
                    "min_width": 9.0,  # feet
                    "min_ventilation": 10.0,  # percentage of floor area
                    "description": "Minimum bedroom requirements",
                    "regulation": "UDA Regulation 5.1.1"
                },
                "living_room": {
                    "min_area": 120.0,  # sq ft
                    "min_width": 10.0,  # feet
                    "description": "Minimum living room requirements",
                    "regulation": "UDA Regulation 5.2.1"
                },
                "kitchen": {
                    "min_area": 60.0,  # sq ft
                    "min_width": 6.0,  # feet
                    "min_ventilation": 20.0,  # percentage of floor area
                    "description": "Minimum kitchen requirements",
                    "regulation": "UDA Regulation 5.3.1"
                },
                "bathroom": {
                    "min_area": 35.0,  # sq ft
                    "min_width": 5.0,  # feet
                    "min_ventilation": 15.0,  # percentage of floor area
                    "description": "Minimum bathroom requirements",
                    "regulation": "UDA Regulation 5.4.1"
                }
            },
            "ventilation": {
                "min_window_area": {
                    "value": 10.0,  # percentage of floor area
                    "description": "Minimum window area for natural ventilation",
                    "regulation": "UDA Regulation 6.1.1"
                },
                "cross_ventilation": {
                    "required": True,
                    "description": "Cross ventilation required for all habitable rooms",
                    "regulation": "UDA Regulation 6.2.1"
                }
            },
            "parking": {
                "residential": {
                    "min_spaces": 1,
                    "space_size": "9ft x 18ft",
                    "description": "Minimum parking requirement for residential houses",
                    "regulation": "UDA Regulation 7.1.1"
                }
            },
            "septic_tank": {
                "min_distance_from_well": 50.0,  # feet
                "min_distance_from_building": 10.0,  # feet
                "description": "Septic tank location requirements",
                "regulation": "UDA Regulation 8.1.1"
            }
        }
    
    def validate_house_design(
        self,
        building_data: Dict[str, Any],
        plot_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a house design against UDA regulations.
        
        Args:
            building_data: Building parameters including dimensions, rooms, etc.
            plot_data: Plot/land parameters including size, setbacks, etc.
            
        Returns:
            Validation report with compliance status and violations
        """
        validation_results = {
            "is_compliant": True,
            "compliance_score": 100.0,
            "violations": [],
            "warnings": [],
            "passed_checks": [],
            "recommendations": []
        }
        
        # Run all validation checks
        self._validate_setbacks(building_data, plot_data, validation_results)
        self._validate_coverage(building_data, plot_data, validation_results)
        self._validate_height(building_data, validation_results)
        self._validate_rooms(building_data, validation_results)
        self._validate_ventilation(building_data, validation_results)
        self._validate_parking(building_data, validation_results)
        
        # Calculate compliance score
        total_checks = (
            len(validation_results["violations"]) +
            len(validation_results["warnings"]) +
            len(validation_results["passed_checks"])
        )
        
        if total_checks > 0:
            # Violations reduce score more than warnings
            violation_penalty = len(validation_results["violations"]) * 15
            warning_penalty = len(validation_results["warnings"]) * 5
            validation_results["compliance_score"] = max(
                0.0,
                100.0 - violation_penalty - warning_penalty
            )
        
        # Set overall compliance status
        validation_results["is_compliant"] = len(validation_results["violations"]) == 0
        
        return validation_results
    
    def _validate_setbacks(
        self,
        building_data: Dict[str, Any],
        plot_data: Optional[Dict[str, Any]],
        results: Dict[str, Any]
    ) -> None:
        """Validate setback requirements."""
        if not plot_data:
            results["warnings"].append({
                "rule": "Setbacks",
                "message": "Plot data not provided - cannot validate setback requirements",
                "regulation": "UDA Regulation 2.1"
            })
            return
        
        setback_rules = self.regulations["setbacks"]
        
        # Check front setback
        front_setback = plot_data.get("front_setback", 0)
        min_front = setback_rules["front_setback"]["minimum"]
        if front_setback < min_front:
            results["violations"].append({
                "rule": "Front Setback",
                "message": f"Front setback {front_setback}ft is less than minimum required {min_front}ft",
                "regulation": setback_rules["front_setback"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Front Setback",
                "message": f"Front setback {front_setback}ft meets minimum requirement",
                "regulation": setback_rules["front_setback"]["regulation"]
            })
        
        # Check rear setback
        rear_setback = plot_data.get("rear_setback", 0)
        min_rear = setback_rules["rear_setback"]["minimum"]
        if rear_setback < min_rear:
            results["violations"].append({
                "rule": "Rear Setback",
                "message": f"Rear setback {rear_setback}ft is less than minimum required {min_rear}ft",
                "regulation": setback_rules["rear_setback"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Rear Setback",
                "message": f"Rear setback {rear_setback}ft meets minimum requirement",
                "regulation": setback_rules["rear_setback"]["regulation"]
            })
        
        # Check side setbacks
        side_setback = plot_data.get("side_setback", 0)
        min_side = setback_rules["side_setback"]["minimum"]
        if side_setback < min_side:
            results["violations"].append({
                "rule": "Side Setback",
                "message": f"Side setback {side_setback}ft is less than minimum required {min_side}ft",
                "regulation": setback_rules["side_setback"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Side Setback",
                "message": f"Side setback {side_setback}ft meets minimum requirement",
                "regulation": setback_rules["side_setback"]["regulation"]
            })
    
    def _validate_coverage(
        self,
        building_data: Dict[str, Any],
        plot_data: Optional[Dict[str, Any]],
        results: Dict[str, Any]
    ) -> None:
        """Validate building coverage requirements."""
        building_coverage = building_data.get("building_coverage", 0)
        max_coverage = self.regulations["coverage"]["max_building_coverage"]["residential"]
        
        if building_coverage > max_coverage:
            results["violations"].append({
                "rule": "Building Coverage",
                "message": f"Building coverage {building_coverage}% exceeds maximum allowed {max_coverage}%",
                "regulation": self.regulations["coverage"]["max_building_coverage"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Building Coverage",
                "message": f"Building coverage {building_coverage}% is within limit",
                "regulation": self.regulations["coverage"]["max_building_coverage"]["regulation"]
            })
    
    def _validate_height(
        self,
        building_data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate building height requirements."""
        floor_count = building_data.get("floor_count", 1)
        building_height = building_data.get("building_height", 0)
        
        # Check floor count
        max_floors = self.regulations["height"]["max_floors"]["value"]
        if floor_count > max_floors:
            results["warnings"].append({
                "rule": "Floor Count",
                "message": f"Building has {floor_count} floors, exceeds typical limit of {max_floors} (may require special approval)",
                "regulation": self.regulations["height"]["max_floors"]["regulation"],
                "severity": "WARNING"
            })
        else:
            results["passed_checks"].append({
                "rule": "Floor Count",
                "message": f"Floor count {floor_count} is within limit",
                "regulation": self.regulations["height"]["max_floors"]["regulation"]
            })
        
        # Check building height
        max_height = self.regulations["height"]["max_height"]["value"]
        if building_height > max_height:
            results["violations"].append({
                "rule": "Building Height",
                "message": f"Building height {building_height}ft exceeds maximum {max_height}ft",
                "regulation": self.regulations["height"]["max_height"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Building Height",
                "message": f"Building height {building_height}ft is within limit",
                "regulation": self.regulations["height"]["max_height"]["regulation"]
            })
    
    def _validate_rooms(
        self,
        building_data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate room size requirements."""
        rooms = building_data.get("rooms", [])
        
        if not rooms:
            results["warnings"].append({
                "rule": "Room Details",
                "message": "No room details provided - cannot validate room requirements",
                "regulation": "UDA Regulation 5"
            })
            return
        
        room_regulations = self.regulations["rooms"]
        
        for room in rooms:
            room_type = room.get("type", "").lower()
            room_area = room.get("area", 0)
            room_width = room.get("width", 0)
            
            # Find matching regulation
            reg_key = None
            for key in room_regulations.keys():
                if key in room_type:
                    reg_key = key
                    break
            
            if not reg_key:
                continue
            
            room_reg = room_regulations[reg_key]
            
            # Check minimum area
            min_area = room_reg.get("min_area", 0)
            if room_area < min_area:
                results["violations"].append({
                    "rule": f"{room_type.title()} Size",
                    "message": f"{room_type.title()} area {room_area}sq.ft is less than minimum {min_area}sq.ft",
                    "regulation": room_reg["regulation"],
                    "severity": "ERROR"
                })
            else:
                results["passed_checks"].append({
                    "rule": f"{room_type.title()} Size",
                    "message": f"{room_type.title()} area meets minimum requirement",
                    "regulation": room_reg["regulation"]
                })
            
            # Check minimum width
            min_width = room_reg.get("min_width", 0)
            if room_width < min_width:
                results["violations"].append({
                    "rule": f"{room_type.title()} Width",
                    "message": f"{room_type.title()} width {room_width}ft is less than minimum {min_width}ft",
                    "regulation": room_reg["regulation"],
                    "severity": "ERROR"
                })
    
    def _validate_ventilation(
        self,
        building_data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate ventilation requirements."""
        # This is a simplified check - would need more detailed room data
        results["recommendations"].append({
            "category": "Ventilation",
            "message": "Ensure all habitable rooms have minimum 10% window area for natural ventilation",
            "regulation": "UDA Regulation 6.1.1"
        })
        
        results["recommendations"].append({
            "category": "Ventilation",
            "message": "Provide cross ventilation in all bedrooms and living areas",
            "regulation": "UDA Regulation 6.2.1"
        })
    
    def _validate_parking(
        self,
        building_data: Dict[str, Any],
        results: Dict[str, Any]
    ) -> None:
        """Validate parking requirements."""
        parking_spaces = building_data.get("parking_spaces", 0)
        min_parking = self.regulations["parking"]["residential"]["min_spaces"]
        
        if parking_spaces < min_parking:
            results["violations"].append({
                "rule": "Parking",
                "message": f"Insufficient parking spaces. Minimum {min_parking} space(s) required",
                "regulation": self.regulations["parking"]["residential"]["regulation"],
                "severity": "ERROR"
            })
        else:
            results["passed_checks"].append({
                "rule": "Parking",
                "message": f"Parking requirement met ({parking_spaces} space(s))",
                "regulation": self.regulations["parking"]["residential"]["regulation"]
            })
    
    def get_regulations_summary(self) -> Dict[str, Any]:
        """Get a summary of all UDA house regulations."""
        return {
            "regulation_categories": list(self.regulations.keys()),
            "regulations": self.regulations,
            "version": "UDA Sri Lanka 2024",
            "applicable_to": "Residential houses and small-scale residential buildings"
        }


# Singleton instance
_uda_validator = None

def get_uda_validator() -> UDAHouseValidator:
    """Get or create UDA house validator instance."""
    global _uda_validator
    if _uda_validator is None:
        _uda_validator = UDAHouseValidator()
    return _uda_validator
