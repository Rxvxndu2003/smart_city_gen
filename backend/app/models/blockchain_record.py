"""
BlockchainRecord model for future blockchain integration.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class RecordType(str, enum.Enum):
    """Blockchain record type enum."""
    DESIGN_HASH = "DESIGN_HASH"
    SUBMISSION_HASH = "SUBMISSION_HASH"
    APPROVAL_HASH = "APPROVAL_HASH"
    REJECTION_HASH = "REJECTION_HASH"
    APPROVAL = "APPROVAL"
    EXPORT = "EXPORT"
    CERTIFICATE = "CERTIFICATE"


class BlockchainRecord(Base):
    """Blockchain record model for immutable design records."""
    
    __tablename__ = "blockchain_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    layout_id = Column(Integer, ForeignKey("layouts.id", ondelete="CASCADE"), nullable=True)
    transaction_hash = Column(String(66), unique=True, nullable=True, index=True)  # Ethereum tx hash
    ipfs_hash = Column(String(100), nullable=True)  # IPFS CID
    record_type = Column(Enum(RecordType), nullable=False)
    data_hash = Column(String(64), nullable=False)  # SHA-256 of data
    record_metadata = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="blockchain_records")
    layout = relationship("Layout", back_populates="blockchain_records")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<BlockchainRecord(id={self.id}, type='{self.record_type}', tx='{self.transaction_hash}')>"
