"""
Export and file download schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# Export Schemas
class ExportRequest(BaseModel):
    """Request to generate an export."""
    layout_id: int
    export_types: List[str] = Field(..., description="List of: IFC, DXF, FBX, GLB, XLSX, PDF_REPORT")
    parameters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseModel):
    """Export response schema."""
    id: int
    project_id: int
    layout_id: int
    export_type: str
    file_path: str
    file_size_bytes: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    generated_at: datetime
    generated_by: Optional[int] = None
    download_count: int
    download_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ExportListResponse(BaseModel):
    """List of exports."""
    total: int
    exports: List[ExportResponse]


class ExportStatusResponse(BaseModel):
    """Export generation status."""
    export_id: int
    status: str
    progress: int
    message: Optional[str] = None
    file_path: Optional[str] = None
    download_url: Optional[str] = None


class BulkExportRequest(BaseModel):
    """Request to generate multiple exports."""
    layout_ids: List[int]
    export_types: List[str]
    parameters: Optional[Dict[str, Any]] = None


class BulkExportResponse(BaseModel):
    """Bulk export response."""
    total_requested: int
    exports_created: List[ExportResponse]
    errors: List[Dict[str, str]] = []
