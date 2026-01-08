"""
Dependencies initialization.
"""
from app.dependencies.auth import get_current_user, require_role, require_roles
from app.dependencies.database import get_db

__all__ = ["get_current_user", "require_role", "require_roles", "get_db"]
