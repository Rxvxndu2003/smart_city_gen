"""
Authentication router for login, registration, and token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    Token,
    RefreshTokenRequest,
    RegisterRequest,
    ChangePasswordRequest
)
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.audit_log import AuditLog

router = APIRouter()


@router.post("/login", response_model=Token, summary="User login")
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with email and password.
    Returns JWT access and refresh tokens.
    """
    user = AuthService.authenticate_user(login_data.email, login_data.password, db)
    
    if not user:
        # Log failed login attempt
        audit_log = AuditLog(
            action="LOGIN_FAILED",
            details={"email": login_data.email, "reason": "Invalid credentials"}
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    tokens = AuthService.create_tokens(user, db)
    
    # Log successful login
    audit_log = AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        details={"email": user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return tokens


@router.post("/register", response_model=Token, summary="User registration", status_code=status.HTTP_201_CREATED)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    Automatically assigns 'Viewer' role by default.
    """
    user, error = AuthService.register_user(
        email=register_data.email,
        password=register_data.password,
        full_name=register_data.full_name,
        phone=register_data.phone,
        db=db,
        default_role="Viewer"
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Create tokens for new user
    tokens = AuthService.create_tokens(user, db)
    
    # Log registration
    audit_log = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        details={"email": user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return tokens


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    # TODO: Implement refresh token validation and new token generation
    # This is a placeholder implementation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Token refresh not yet implemented"
    )


@router.post("/change-password", summary="Change password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for the current user.
    """
    success, error = AuthService.change_password(
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password,
        db=db
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Log password change
    audit_log = AuditLog(
        user_id=current_user.id,
        action="PASSWORD_CHANGED",
        details={"email": current_user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.get("/me", summary="Get current user info")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about the currently authenticated user.
    """
    # Get full role objects instead of just names
    user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == current_user.id)
        .all()
    )
    
    roles = [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description
        }
        for role in user_roles
    ]
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "is_active": current_user.is_active,
        "roles": roles,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }


@router.post("/logout", summary="User logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user.
    Note: Since we're using JWT, actual logout is handled client-side by discarding tokens.
    This endpoint is primarily for logging purposes.
    """
    # Log logout
    audit_log = AuditLog(
        user_id=current_user.id,
        action="LOGOUT",
        details={"email": current_user.email}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Logged out successfully"}
