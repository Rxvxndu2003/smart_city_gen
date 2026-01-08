"""
Roles router for role management.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.role import Role
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("", summary="List all roles")
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all available roles in the system.
    """
    roles = db.query(Role).all()
    
    return [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description
        }
        for role in roles
    ]
