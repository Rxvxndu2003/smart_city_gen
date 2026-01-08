"""
3D generation and layout schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# Layout Schemas
class LayoutBase(BaseModel):
    """Base layout schema."""
    name: Optional[str] = Field(None, max_length=255)
    building_count: Optional[int] = None
    total_floor_area_m2: Optional[Decimal] = None
    open_space_area_m2: Optional[Decimal] = None
    parking_spaces: Optional[int] = None
    max_building_height_m: Optional[Decimal] = None


class LayoutCreate(LayoutBase):
    """Schema for creating a layout (without generation)."""
    project_id: int
    input_parameters: Optional[Dict[str, Any]] = None


class LayoutUpdate(BaseModel):
    """Schema for updating a layout."""
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None


class LayoutResponse(LayoutBase):
    """Layout response schema."""
    id: int
    project_id: int
    version: int
    status: str
    generation_job_id: Optional[str] = None
    blend_file_path: Optional[str] = None
    glb_file_path: Optional[str] = None
    preview_image_path: Optional[str] = None
    input_parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class LayoutDetailResponse(LayoutResponse):
    """Detailed layout response with related data."""
    project_name: Optional[str] = None
    creator_name: Optional[str] = None
    has_validation_report: bool = False
    approval_count: int = 0


# Generation Job Schemas
class GenerationParameters(BaseModel):
    """3D generation input parameters."""
    project_id: int
    layout_name: Optional[str] = None
    
    # Design parameters
    building_count: int = Field(..., ge=1, le=100)
    max_building_height_m: Decimal = Field(..., ge=3.0, le=200.0)
    open_space_area_m2: Decimal = Field(..., ge=0)
    parking_spaces: int = Field(default=0, ge=0)
    
    # Style parameters
    architectural_style: str = Field(default="Modern", description="Modern, Traditional, Mixed")
    detail_level: str = Field(default="Medium", description="Low, Medium, High")
    
    # Additional parameters
    road_width_m: Optional[Decimal] = Field(default=6.0, ge=3.0, le=20.0)
    include_landscaping: bool = Field(default=True)
    include_utilities: bool = Field(default=False)
    
    # Advanced options
    additional_options: Optional[Dict[str, Any]] = None


class GenerationJobCreate(BaseModel):
    """Request to start a 3D generation job."""
    parameters: GenerationParameters


class GenerationJobResponse(BaseModel):
    """Generation job response schema."""
    id: str
    project_id: int
    layout_id: Optional[int] = None
    status: str
    progress: int
    progress_message: Optional[str] = None
    input_parameters: Dict[str, Any]
    output_files: Optional[List[str]] = None
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class GenerationJobStatusResponse(BaseModel):
    """Generation job status for polling."""
    job_id: str
    status: str
    progress: int
    progress_message: Optional[str] = None
    output_files: Optional[List[str]] = None
    error_message: Optional[str] = None
    estimated_time_remaining_seconds: Optional[int] = None


class GenerationJobListResponse(BaseModel):
    """List of generation jobs."""
    total: int
    jobs: List[GenerationJobResponse]


# GPT Assistant Schemas
class GPTAssistantRequest(BaseModel):
    """Request for GPT design assistant."""
    project_id: int
    layout_id: Optional[int] = None
    query_type: str = Field(..., description="EXPLANATION, RATIONALE, REPORT, RECOMMENDATIONS")
    context: Optional[Dict[str, Any]] = None
    custom_prompt: Optional[str] = None


class GPTAssistantResponse(BaseModel):
    """GPT assistant response."""
    query_type: str
    response_text: str
    model_used: str
    tokens_used: int
    generated_at: datetime
