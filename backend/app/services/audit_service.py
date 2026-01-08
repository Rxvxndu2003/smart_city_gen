"""
Audit Service for logging user actions and system events.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    def log_action(
        db: Session,
        user_id: int,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[AuditLog]:
        """
        Log an audit action.
        
        Args:
            db: Database session
            user_id: ID of user performing action
            action: Action being performed
            resource_type: Type of resource being acted upon
            resource_id: ID of resource
            details: Additional details as JSON
            ip_address: IP address of user
            user_agent: User agent string
            
        Returns:
            Created AuditLog or None if failed
        """
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            
            return audit_log
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            db.rollback()
            return None
