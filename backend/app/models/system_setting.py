"""
SystemSetting model for admin panel configuration.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SystemSetting(Base):
    """System settings model for admin configuration."""
    
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    setting_key = Column(String(100), unique=True, nullable=False, index=True)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<SystemSetting(key='{self.setting_key}')>"
