"""
File upload router for project documents and attachments.
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter()

UPLOAD_DIR = Path("storage/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file for a project."""
    try:
        # Validate file size (max 50MB)
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="File too large (max 50MB)")
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # Create project subdirectory if project_id provided
        if project_id:
            project_dir = UPLOAD_DIR / str(project_id)
            project_dir.mkdir(parents=True, exist_ok=True)
            file_path = project_dir / unique_name
        else:
            file_path = UPLOAD_DIR / unique_name
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "filename": file.filename,
            "stored_name": unique_name,
            "file_path": str(file_path),
            "size": file_path.stat().st_size,
            "project_id": project_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/download/{project_id}/{filename}")
async def download_file(
    project_id: int,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download a file by project ID and filename."""
    file_path = UPLOAD_DIR / str(project_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.get("/list/{project_id}")
async def list_files(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """List all files for a project."""
    project_dir = UPLOAD_DIR / str(project_id)
    
    if not project_dir.exists():
        return {"files": []}
    
    files = []
    for file_path in project_dir.iterdir():
        if file_path.is_file():
            files.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            })
    
    return {"files": files}

@router.delete("/delete/{project_id}/{filename}")
async def delete_file(
    project_id: int,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a file."""
    file_path = UPLOAD_DIR / str(project_id) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path.unlink()
    
    return {"success": True, "message": "File deleted"}
