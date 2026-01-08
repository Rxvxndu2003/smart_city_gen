"""
User and Role schemas for user management and RBAC.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# Role Schemas
class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., max_length=50)
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleCreate(RoleBase):
    """Schema for creating a new role."""
    pass


class RoleUpdate(BaseModel):
    """Schema for updating an existing role."""
    display_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Role response schema."""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    role_ids: Optional[List[int]] = None


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class UserWithRolesResponse(UserResponse):
    """User response with role details."""
    pass


class UserListResponse(BaseModel):
    """Paginated user list response."""
    total: int
    page: int
    page_size: int
    users: List[UserResponse]


# User-Role Assignment Schemas
class UserRoleAssignRequest(BaseModel):
    """Request to assign roles to a user."""
    role_ids: List[int]


class UserRoleRemoveRequest(BaseModel):
    """Request to remove roles from a user."""
    role_ids: List[int]


class UserRoleResponse(BaseModel):
    """User-role assignment response."""
    id: int
    user_id: int
    role_id: int
    assigned_at: datetime
    assigned_by: Optional[int] = None
    role: RoleResponse
    
    model_config = ConfigDict(from_attributes=True)
