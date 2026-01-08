"""
Project and site volume schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# GeoJSON helper schemas
class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry."""
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=3)  # [lng, lat] or [lng, lat, alt]


class GeoJSONPolygon(BaseModel):
    """GeoJSON Polygon geometry."""
    type: str = "Polygon"
    coordinates: List[List[List[float]]]  # Array of linear rings


# Site Volume Schemas
class SiteVolumeBase(BaseModel):
    """Base site volume schema."""
    volume_type: str = Field(..., description="SITE_BOUNDARY, ZONING_ENVELOPE, SETBACK, HEIGHT_PLANE")
    geometry: GeoJSONPolygon
    height_max: Optional[Decimal] = None
    height_min: Optional[Decimal] = None
    floor_area_ratio: Optional[Decimal] = None
    coverage_ratio: Optional[Decimal] = None
    properties: Optional[Dict[str, Any]] = None


class SiteVolumeCreate(SiteVolumeBase):
    """Schema for creating a site volume."""
    pass


class SiteVolumeUpdate(BaseModel):
    """Schema for updating a site volume."""
    height_max: Optional[Decimal] = None
    height_min: Optional[Decimal] = None
    floor_area_ratio: Optional[Decimal] = None
    coverage_ratio: Optional[Decimal] = None
    properties: Optional[Dict[str, Any]] = None


class SiteVolumeResponse(SiteVolumeBase):
    """Site volume response schema."""
    id: int
    project_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Project Schemas
class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    location_address: Optional[str] = Field(None, max_length=500)
    location_district: Optional[str] = Field(None, max_length=100)
    location_city: Optional[str] = Field(None, max_length=100)
    uda_zone: Optional[str] = Field(None, max_length=50)


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    # Location (accept both formats)
    district: Optional[str] = None
    location_coordinates: Optional[GeoJSONPoint] = None
    
    # Site parameters (accept both formats)
    site_area: Optional[Decimal] = None
    site_area_m2: Optional[Decimal] = None
    site_boundary: Optional[GeoJSONPolygon] = None
    
    # Building parameters
    building_coverage: Optional[Decimal] = None
    floor_area_ratio: Optional[Decimal] = None
    num_floors: Optional[int] = None
    building_height: Optional[Decimal] = None
    open_space_percentage: Optional[Decimal] = None
    parking_spaces: Optional[int] = None
    owner_name: Optional[str] = None
    
    # Urban Planning Parameters
    # Zoning
    residential_percentage: Optional[Decimal] = None
    commercial_percentage: Optional[Decimal] = None
    industrial_percentage: Optional[Decimal] = None
    green_space_percentage: Optional[Decimal] = None
    
    # Infrastructure
    road_network_type: Optional[str] = None
    main_road_width: Optional[Decimal] = None
    secondary_road_width: Optional[Decimal] = None
    pedestrian_path_width: Optional[Decimal] = None
    
    # Demographics
    target_population: Optional[int] = None
    population_density: Optional[Decimal] = None
    average_household_size: Optional[Decimal] = None
    
    # Environmental
    climate_zone: Optional[str] = None
    sustainability_rating: Optional[str] = None
    renewable_energy_target: Optional[Decimal] = None
    water_management_strategy: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = Field(None, max_length=100)
    location_address: Optional[str] = Field(None, max_length=500)
    location_district: Optional[str] = Field(None, max_length=100)
    location_city: Optional[str] = Field(None, max_length=100)
    uda_zone: Optional[str] = Field(None, max_length=50)
    site_area_m2: Optional[Decimal] = None
    building_coverage: Optional[Decimal] = None
    floor_area_ratio: Optional[Decimal] = None
    num_floors: Optional[int] = None
    building_height: Optional[Decimal] = None
    open_space_percentage: Optional[Decimal] = None
    parking_spaces: Optional[int] = None
    owner_name: Optional[str] = Field(None, max_length=255)
    
    # Urban Planning Parameters
    residential_percentage: Optional[Decimal] = None
    commercial_percentage: Optional[Decimal] = None
    industrial_percentage: Optional[Decimal] = None
    green_space_percentage: Optional[Decimal] = None
    road_network_type: Optional[str] = None
    main_road_width: Optional[Decimal] = None
    secondary_road_width: Optional[Decimal] = None
    pedestrian_path_width: Optional[Decimal] = None
    target_population: Optional[int] = None
    population_density: Optional[Decimal] = None
    average_household_size: Optional[Decimal] = None
    climate_zone: Optional[str] = None
    sustainability_rating: Optional[str] = None
    renewable_energy_target: Optional[Decimal] = None
    water_management_strategy: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Project response schema."""
    id: int
    owner_id: int
    status: str
    location_coordinates: Optional[GeoJSONPoint] = None
    site_area_m2: Optional[Decimal] = None
    building_coverage: Optional[Decimal] = None
    floor_area_ratio: Optional[Decimal] = None
    num_floors: Optional[int] = None
    building_height: Optional[Decimal] = None
    open_space_percentage: Optional[Decimal] = None
    parking_spaces: Optional[int] = None
    owner_name: Optional[str] = None
    model_url: Optional[str] = None
    enhanced_renders_metadata: Optional[list] = None
    predicted_compliance: Optional[int] = None
    compliance_confidence: Optional[Decimal] = None
    compliance_score: Optional[Decimal] = None
    prediction_message: Optional[str] = None
    predicted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    
    # Urban Planning Parameters (for response)
    residential_percentage: Optional[Decimal] = None
    commercial_percentage: Optional[Decimal] = None
    industrial_percentage: Optional[Decimal] = None
    green_space_percentage: Optional[Decimal] = None
    road_network_type: Optional[str] = None
    main_road_width: Optional[Decimal] = None
    secondary_road_width: Optional[Decimal] = None
    pedestrian_path_width: Optional[Decimal] = None
    target_population: Optional[int] = None
    population_density: Optional[Decimal] = None
    average_household_size: Optional[Decimal] = None
    climate_zone: Optional[str] = None
    sustainability_rating: Optional[str] = None
    renewable_energy_target: Optional[Decimal] = None
    water_management_strategy: Optional[str] = None
    
    # Aliases for backward compatibility with frontend
    district: Optional[str] = None
    site_area: Optional[Decimal] = None
    
    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with relationships."""
    site_volumes: List[SiteVolumeResponse] = []
    owner_name: Optional[str] = None
    layout_count: int = 0


class ProjectListResponse(BaseModel):
    """Paginated project list response."""
    total: int
    page: int
    page_size: int
    projects: List[ProjectResponse]


class ProjectParametersUpdate(BaseModel):
    """Schema for updating project parameters."""
    target_floor_area_m2: Optional[Decimal] = None
    target_building_count: Optional[int] = None
    max_building_height_m: Optional[Decimal] = None
    min_open_space_ratio: Optional[Decimal] = None
    parking_requirement: Optional[int] = None
    additional_parameters: Optional[Dict[str, Any]] = None
