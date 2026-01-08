"""
Admin router - placeholder for admin panel endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User

router = APIRouter()

@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get admin dashboard stats (TODO: Implement)."""
    return {"message": "Admin dashboard endpoint - to be implemented"}

@router.get("/system-settings")
async def get_system_settings(
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """Get system settings (TODO: Implement)."""
    return {"message": "System settings endpoint - to be implemented"}
