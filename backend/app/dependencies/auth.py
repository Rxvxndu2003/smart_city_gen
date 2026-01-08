"""
Authentication dependencies for FastAPI.
JWT validation and role-based access control.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
import logging

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.role import Role, UserRole
from app.schemas.auth import TokenData

logger = logging.getLogger(__name__)

# HTTP Bearer token security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from request header
        db: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert user_id from string to integer
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id in token: {user_id_str}")
            raise credentials_exception
            
        token_data = TokenData(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", [])
        )
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception
    
    # Get user from database with eager loading of roles
    user = db.query(User).options(
        joinedload(User.user_roles).joinedload(UserRole.role)
    ).filter(User.id == token_data.user_id).first()
    
    if user is None:
        logger.warning(f"User not found: {token_data.user_id}")
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


def get_user_roles(user: User, db: Session) -> List[str]:
    """
    Get list of role names for a user.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        List[str]: List of role names
    """
    user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    return [role.name for role in user_roles]


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Usage:
        @app.get("/admin/users")
        def get_users(user: User = Depends(require_role("Admin"))):
            ...
    
    Args:
        required_role: Name of required role
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_roles = get_user_roles(current_user, db)
        
        if required_role not in user_roles:
            logger.warning(
                f"User {current_user.id} attempted to access resource requiring "
                f"role '{required_role}' but has roles: {user_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required role: {required_role}"
            )
        
        return current_user
    
    return role_checker


def require_roles(required_roles: List[str], require_all: bool = False):
    """
    Dependency factory to require one or more roles.
    
    Usage:
        # Require ANY of the roles
        @app.get("/projects")
        def get_projects(user: User = Depends(require_roles(["Architect", "Engineer"]))):
            ...
        
        # Require ALL of the roles
        @app.post("/admin/critical")
        def critical_action(user: User = Depends(require_roles(["Admin", "Auditor"], require_all=True))):
            ...
    
    Args:
        required_roles: List of role names
        require_all: If True, user must have all roles; if False, user needs at least one
        
    Returns:
        Dependency function
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_roles = get_user_roles(current_user, db)
        
        if require_all:
            # User must have ALL required roles
            missing_roles = set(required_roles) - set(user_roles)
            if missing_roles:
                logger.warning(
                    f"User {current_user.id} missing required roles: {missing_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User missing required roles: {', '.join(missing_roles)}"
                )
        else:
            # User must have AT LEAST ONE required role
            has_required_role = any(role in user_roles for role in required_roles)
            if not has_required_role:
                logger.warning(
                    f"User {current_user.id} does not have any of the required roles: {required_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User must have one of these roles: {', '.join(required_roles)}"
                )
        
        return current_user
    
    return role_checker


def require_admin(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    """
    Convenience dependency to require Admin role.
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        def delete_user(user_id: int, admin: User = Depends(require_admin)):
            ...
    """
    return require_role("Admin")(current_user, db)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that have optional authentication.
    
    Args:
        credentials: Optional HTTP Bearer token
        db: Database session
        
    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        return user
        
    except JWTError:
        return None
