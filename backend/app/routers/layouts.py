"""
Layouts router - placeholder for layout management endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("")
async def list_layouts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List layouts (TODO: Implement)."""
    return {"message": "Layouts endpoint - to be implemented"}
