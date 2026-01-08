"""
Validation Service for UDA (Urban Development Authority) compliance checking.
Implements Sri Lankan building regulations and zoning rules.
"""
from typing import Dict, Any, List, Tuple
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, rule_id: str, description: str, severity: str = "ERROR"):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity  # ERROR, WARNING, INFO
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate the rule.
        
        Returns:
            Tuple of (is_valid, message)
        """
        raise NotImplementedError


class SetbackValidation(ValidationRule):
    """Validate setback requirements."""
    
    def __init__(self):
        super().__init__(
            "UDA_SETBACK",
            "Building setback requirements",
            "ERROR"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if setbacks meet minimum requirements."""
        setback_front = project_data.get('setback_front', 0)
        setback_side = project_data.get('setback_side', 0)
        setback_rear = project_data.get('setback_rear', 0)
        
        min_front = 3.0  # meters
        min_side = 1.5   # meters
        min_rear = 3.0   # meters
        
        issues = []
        
        if setback_front < min_front:
            issues.append(f"Front setback {setback_front}m is less than minimum {min_front}m")
        
        if setback_side < min_side:
            issues.append(f"Side setback {setback_side}m is less than minimum {min_side}m")
        
        if setback_rear < min_rear:
            issues.append(f"Rear setback {setback_rear}m is less than minimum {min_rear}m")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "Setback requirements met"


class BuildingCoverageValidation(ValidationRule):
    """Validate building coverage ratio."""
    
    def __init__(self):
        super().__init__(
            "UDA_COVERAGE",
            "Building coverage ratio compliance",
            "ERROR"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if building coverage is within limits."""
        site_area = project_data.get('site_area', 0)
        building_footprint = project_data.get('building_footprint', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        
        if site_area == 0:
            return False, "Site area not specified"
        
        # Maximum coverage ratios by project type
        max_coverage = {
            'RESIDENTIAL': 0.60,  # 60%
            'COMMERCIAL': 0.70,   # 70%
            'INDUSTRIAL': 0.65,   # 65%
            'MIXED_USE': 0.65,    # 65%
            'INSTITUTIONAL': 0.55  # 55%
        }.get(project_type, 0.60)
        
        actual_coverage = building_footprint / site_area
        
        if actual_coverage > max_coverage:
            return False, f"Building coverage {actual_coverage*100:.1f}% exceeds maximum {max_coverage*100:.1f}% for {project_type}"
        
        return True, f"Building coverage {actual_coverage*100:.1f}% is within limits"


class FloorAreaRatioValidation(ValidationRule):
    """Validate Floor Area Ratio (FAR)."""
    
    def __init__(self):
        super().__init__(
            "UDA_FAR",
            "Floor Area Ratio compliance",
            "ERROR"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if FAR is within limits."""
        site_area = project_data.get('site_area', 0)
        total_floor_area = project_data.get('total_floor_area', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        district = project_data.get('district', 'COLOMBO')
        
        if site_area == 0:
            return False, "Site area not specified"
        
        # Maximum FAR by project type and district
        # Colombo has higher FAR limits
        if district.upper() == 'COLOMBO':
            max_far = {
                'RESIDENTIAL': 3.0,
                'COMMERCIAL': 4.0,
                'INDUSTRIAL': 2.5,
                'MIXED_USE': 3.5,
                'INSTITUTIONAL': 2.0
            }.get(project_type, 2.5)
        else:
            max_far = {
                'RESIDENTIAL': 2.5,
                'COMMERCIAL': 3.0,
                'INDUSTRIAL': 2.0,
                'MIXED_USE': 2.75,
                'INSTITUTIONAL': 1.5
            }.get(project_type, 2.0)
        
        actual_far = total_floor_area / site_area
        
        if actual_far > max_far:
            return False, f"FAR {actual_far:.2f} exceeds maximum {max_far:.2f} for {project_type} in {district}"
        
        return True, f"FAR {actual_far:.2f} is within limits"


class BuildingHeightValidation(ValidationRule):
    """Validate building height restrictions."""
    
    def __init__(self):
        super().__init__(
            "UDA_HEIGHT",
            "Building height restrictions",
            "ERROR"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if building height is within limits."""
        building_height = project_data.get('building_height', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        district = project_data.get('district', 'COLOMBO')
        
        # Maximum heights by project type (in meters)
        if district.upper() == 'COLOMBO':
            max_height = {
                'RESIDENTIAL': 45.0,  # ~15 floors
                'COMMERCIAL': 60.0,   # ~20 floors
                'INDUSTRIAL': 30.0,   # ~10 floors
                'MIXED_USE': 50.0,    # ~16 floors
                'INSTITUTIONAL': 30.0  # ~10 floors
            }.get(project_type, 30.0)
        else:
            max_height = {
                'RESIDENTIAL': 30.0,  # ~10 floors
                'COMMERCIAL': 45.0,   # ~15 floors
                'INDUSTRIAL': 24.0,   # ~8 floors
                'MIXED_USE': 36.0,    # ~12 floors
                'INSTITUTIONAL': 24.0  # ~8 floors
            }.get(project_type, 24.0)
        
        if building_height > max_height:
            return False, f"Building height {building_height}m exceeds maximum {max_height}m for {project_type} in {district}"
        
        return True, f"Building height {building_height}m is within limits"


class OpenSpaceValidation(ValidationRule):
    """Validate open space requirements."""
    
    def __init__(self):
        super().__init__(
            "UDA_OPEN_SPACE",
            "Open space requirements",
            "WARNING"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if adequate open space is provided."""
        site_area = project_data.get('site_area', 0)
        open_space_area = project_data.get('open_space_area', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        
        if site_area == 0:
            return False, "Site area not specified"
        
        # Minimum open space ratios
        min_open_space_ratio = {
            'RESIDENTIAL': 0.15,   # 15%
            'COMMERCIAL': 0.10,    # 10%
            'INDUSTRIAL': 0.20,    # 20%
            'MIXED_USE': 0.15,     # 15%
            'INSTITUTIONAL': 0.25   # 25%
        }.get(project_type, 0.15)
        
        required_open_space = site_area * min_open_space_ratio
        
        if open_space_area < required_open_space:
            return False, f"Open space {open_space_area}m² is less than minimum required {required_open_space:.1f}m² ({min_open_space_ratio*100}%)"
        
        return True, f"Open space {open_space_area}m² meets minimum requirements"


class ParkingValidation(ValidationRule):
    """Validate parking requirements."""
    
    def __init__(self):
        super().__init__(
            "UDA_PARKING",
            "Parking space requirements",
            "WARNING"
        )
    
    def validate(self, project_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if adequate parking is provided."""
        parking_spaces = project_data.get('parking_spaces', 0)
        project_type = project_data.get('project_type', 'RESIDENTIAL')
        total_floor_area = project_data.get('total_floor_area', 0)
        
        # Parking requirements per 100m² of floor area
        required_per_100m2 = {
            'RESIDENTIAL': 1.0,    # 1 space per 100m²
            'COMMERCIAL': 2.5,     # 2.5 spaces per 100m²
            'INDUSTRIAL': 1.5,     # 1.5 spaces per 100m²
            'MIXED_USE': 2.0,      # 2 spaces per 100m²
            'INSTITUTIONAL': 1.0    # 1 space per 100m²
        }.get(project_type, 1.0)
        
        required_spaces = int((total_floor_area / 100) * required_per_100m2)
        
        if parking_spaces < required_spaces:
            return False, f"Parking spaces {parking_spaces} is less than minimum required {required_spaces}"
        
        return True, f"Parking spaces {parking_spaces} meets requirements"


class ValidationService:
    """Main validation service for UDA compliance."""
    
    def __init__(self):
        """Initialize validation service with all rules."""
        self.rules = [
            SetbackValidation(),
            BuildingCoverageValidation(),
            FloorAreaRatioValidation(),
            BuildingHeightValidation(),
            OpenSpaceValidation(),
            ParkingValidation()
        ]
    
    def validate_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a project against all UDA rules.
        
        Args:
            project_data: Dictionary with project information
            
        Returns:
            Validation report with results
        """
        results = []
        errors = []
        warnings = []
        info = []
        
        for rule in self.rules:
            try:
                is_valid, message = rule.validate(project_data)
                
                result = {
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "severity": rule.severity,
                    "is_valid": is_valid,
                    "message": message
                }
                
                results.append(result)
                
                if not is_valid:
                    if rule.severity == "ERROR":
                        errors.append(message)
                    elif rule.severity == "WARNING":
                        warnings.append(message)
                else:
                    info.append(message)
                    
            except Exception as e:
                logger.error(f"Error validating rule {rule.rule_id}: {e}")
                errors.append(f"Validation error for {rule.description}: {str(e)}")
        
        is_compliant = len(errors) == 0
        
        return {
            "is_compliant": is_compliant,
            "compliance_score": self._calculate_compliance_score(results),
            "total_checks": len(results),
            "passed_checks": len([r for r in results if r["is_valid"]]),
            "failed_checks": len([r for r in results if not r["is_valid"]]),
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "detailed_results": results,
            "summary": self._generate_summary(is_compliant, errors, warnings)
        }
    
    def _calculate_compliance_score(self, results: List[Dict]) -> float:
        """Calculate compliance score (0-100)."""
        if not results:
            return 0.0
        
        total_weight = 0
        passed_weight = 0
        
        for result in results:
            # Weight by severity
            weight = 3 if result["severity"] == "ERROR" else 1
            total_weight += weight
            
            if result["is_valid"]:
                passed_weight += weight
        
        return round((passed_weight / total_weight) * 100, 2) if total_weight > 0 else 0.0
    
    def _generate_summary(self, is_compliant: bool, errors: List[str], warnings: List[str]) -> str:
        """Generate human-readable summary."""
        if is_compliant and not warnings:
            return "Project is fully compliant with all UDA regulations."
        elif is_compliant:
            return f"Project is compliant but has {len(warnings)} warnings that should be addressed."
        else:
            return f"Project is NOT compliant. Found {len(errors)} critical issues that must be resolved."


# Global validation service instance
validation_service = ValidationService()
