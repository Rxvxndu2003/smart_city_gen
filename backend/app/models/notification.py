"""
Notification model for user notifications.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    """User notification model."""
    
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'APPROVAL_REQUEST', 'STATUS_CHANGE', 'EXPORT_READY', etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    related_project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    related_layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    related_project = relationship("Project", back_populates="notifications")
    related_layout = relationship("Layout", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', read={self.is_read})>"
