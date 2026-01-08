"""
Authentication service for user login, registration, and token management.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import jwt
from passlib.context import CryptContext
import bcrypt
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models.user import User
from app.models.role import Role, UserRole
from app.schemas.auth import Token, TokenData

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication service for user management and JWT tokens."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plaintext password.
        
        Args:
            password: Plaintext password
            
        Returns:
            str: Hashed password
        """
        # Use bcrypt directly to avoid passlib version issues
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a hashed password.
        
        Args:
            plain_password: Plaintext password to verify
            hashed_password: Hashed password from database
            
        Returns:
            bool: True if password matches, False otherwise
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Optional expiration timedelta
            
        Returns:
            str: Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """
        Create a JWT refresh token with longer expiration.
        
        Args:
            data: Data to encode in token
            
        Returns:
            str: Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def get_user_roles(user: User, db: Session) -> list[str]:
        """
        Get list of role names for a user.
        
        Args:
            user: User object
            db: Database session
            
        Returns:
            list[str]: List of role names
        """
        user_roles = (
            db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        return [role.name for role in user_roles]
    
    @classmethod
    def create_tokens(cls, user: User, db: Session) -> Token:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User object
            db: Database session
            
        Returns:
            Token: Token response with access and refresh tokens
        """
        roles = cls.get_user_roles(user, db)
        
        token_data = {
            "sub": str(user.id),  # JWT subject must be a string
            "email": user.email,
            "roles": roles
        }
        
        access_token = cls.create_access_token(token_data)
        refresh_token = cls.create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    @classmethod
    def authenticate_user(cls, email: str, password: str, db: Session) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: Plaintext password
            db: Database session
            
        Returns:
            Optional[User]: User object if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.warning(f"Authentication failed: User not found for email {email}")
            return None
        
        if not cls.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for email {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User account inactive for email {email}")
            return None
        
        # Update last login timestamp
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User authenticated successfully: {email}")
        return user
    
    @classmethod
    def register_user(
        cls,
        email: str,
        password: str,
        full_name: str,
        phone: Optional[str],
        db: Session,
        default_role: str = "Viewer"
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Register a new user account.
        
        Args:
            email: User email
            password: Plaintext password
            full_name: User full name
            phone: Optional phone number
            db: Database session
            default_role: Default role name to assign
            
        Returns:
            Tuple[Optional[User], Optional[str]]: (User object, error message) or (None, error)
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return None, "User with this email already exists"
        
        # Create new user
        hashed_password = cls.hash_password(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            phone=phone,
            is_active=True
        )
        
        db.add(new_user)
        db.flush()  # Flush to get user.id
        
        # Assign default role
        default_role_obj = db.query(Role).filter(Role.name == default_role).first()
        if default_role_obj:
            user_role = UserRole(
                user_id=new_user.id,
                role_id=default_role_obj.id
            )
            db.add(user_role)
        else:
            logger.warning(f"Default role '{default_role}' not found. User registered without role.")
        
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"New user registered: {email}")
        return new_user, None
    
    @classmethod
    def change_password(
        cls,
        user: User,
        old_password: str,
        new_password: str,
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.
        
        Args:
            user: User object
            old_password: Current password
            new_password: New password
            db: Database session
            
        Returns:
            Tuple[bool, Optional[str]]: (Success boolean, error message if any)
        """
        # Verify old password
        if not cls.verify_password(old_password, user.hashed_password):
            return False, "Current password is incorrect"
        
        # Update to new password
        user.hashed_password = cls.hash_password(new_password)
        db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        return True, None
