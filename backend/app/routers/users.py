"""
Users router for user management (admin only).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserRoleAssignRequest,
    UserRoleRemoveRequest
)
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.audit_log import AuditLog
from app.dependencies.auth import require_role, get_current_user
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("", response_model=UserListResponse, summary="List all users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    role_name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filtering.
    Admin only.
    """
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) | 
            (User.full_name.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if role_name:
        query = query.join(UserRole).join(Role).filter(Role.name == role_name)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    
    # Convert to response
    user_responses = []
    for user in users:
        # Get full role objects instead of just names
        user_roles = (
            db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        
        roles = [
            {
                "id": role.id,
                "name": role.name,
                "display_name": role.display_name,
                "description": role.description,
                "created_at": role.created_at.isoformat() if role.created_at else None
            }
            for role in user_roles
        ]
        
        user_responses.append({
            **user.__dict__,
            "roles": roles
        })
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "users": user_responses
    }


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get full role objects instead of just names
    user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    
    roles = [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "created_at": role.created_at.isoformat() if role.created_at else None
        }
        for role in user_roles
    ]
    
    return {
        **user.__dict__,
        "roles": roles
    }


@router.post("", response_model=UserResponse, summary="Create new user", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Create a new user account.
    Admin only.
    """
    user, error = AuthService.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        db=db
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Assign additional roles if specified
    if user_data.role_ids:
        for role_id in user_data.role_ids:
            role = db.query(Role).filter(Role.id == role_id).first()
            if role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role_id,
                    assigned_by=current_user.id
                )
                db.add(user_role)
        db.commit()
    
    # Log user creation
    audit_log = AuditLog(
        user_id=current_user.id,
        action="USER_CREATED",
        resource_type="USER",
        resource_id=user.id,
        details={"created_user_email": user.email}
    )
    db.add(audit_log)
    db.commit()
    
    # Get full role objects instead of just names
    user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    
    roles = [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "created_at": role.created_at.isoformat() if role.created_at else None
        }
        for role in user_roles
    ]
    
    return {
        **user.__dict__,
        "roles": roles
    }


@router.put("/{user_id}", response_model=UserResponse, summary="Update user")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Update user details.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.email is not None:
        # Check if email already exists
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        user.email = user_data.email
    
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    if user_data.phone is not None:
        user.phone = user_data.phone
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    # Log user update
    audit_log = AuditLog(
        user_id=current_user.id,
        action="USER_UPDATED",
        resource_type="USER",
        resource_id=user.id,
        details={"updated_fields": user_data.dict(exclude_unset=True)}
    )
    db.add(audit_log)
    db.commit()
    
    # Get full role objects instead of just names
    user_roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    
    roles = [
        {
            "id": role.id,
            "name": role.name,
            "display_name": role.display_name,
            "description": role.description,
            "created_at": role.created_at.isoformat() if role.created_at else None
        }
        for role in user_roles
    ]
    
    return {
        **user.__dict__,
        "roles": roles
    }


@router.delete("/{user_id}", summary="Delete user")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Delete a user account.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user_email = user.email
    db.delete(user)
    db.commit()
    
    # Log user deletion
    audit_log = AuditLog(
        user_id=current_user.id,
        action="USER_DELETED",
        resource_type="USER",
        resource_id=user_id,
        details={"deleted_user_email": user_email}
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": f"User {user_email} deleted successfully"}


@router.post("/{user_id}/roles/assign", summary="Assign roles to user")
async def assign_roles(
    user_id: int,
    role_data: UserRoleAssignRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Assign one or more roles to a user.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    assigned_roles = []
    for role_id in role_data.role_ids:
        # Check if role exists
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            continue
        
        # Check if user already has this role
        existing = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if not existing:
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=current_user.id
            )
            db.add(user_role)
            assigned_roles.append(role.name)
    
    db.commit()
    
    # Log role assignment
    if assigned_roles:
        audit_log = AuditLog(
            user_id=current_user.id,
            action="ROLES_ASSIGNED",
            resource_type="USER",
            resource_id=user_id,
            details={"assigned_roles": assigned_roles, "target_user_email": user.email}
        )
        db.add(audit_log)
        db.commit()
    
    return {
        "message": f"Assigned {len(assigned_roles)} role(s) to user",
        "roles": assigned_roles
    }


@router.post("/{user_id}/roles/remove", summary="Remove roles from user")
async def remove_roles(
    user_id: int,
    role_data: UserRoleRemoveRequest,
    current_user: User = Depends(require_role("Admin")),
    db: Session = Depends(get_db)
):
    """
    Remove one or more roles from a user.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    removed_roles = []
    for role_id in role_data.role_ids:
        user_role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if user_role:
            role = db.query(Role).filter(Role.id == role_id).first()
            db.delete(user_role)
            if role:
                removed_roles.append(role.name)
    
    db.commit()
    
    # Log role removal
    if removed_roles:
        audit_log = AuditLog(
            user_id=current_user.id,
            action="ROLES_REMOVED",
            resource_type="USER",
            resource_id=user_id,
            details={"removed_roles": removed_roles, "target_user_email": user.email}
        )
        db.add(audit_log)
        db.commit()
    
    return {
        "message": f"Removed {len(removed_roles)} role(s) from user",
        "roles": removed_roles
    }
