"""
Blockchain utilities for automatic compliance logging.
"""
import logging
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.blockchain_record import BlockchainRecord, RecordType
from app.services.blockchain_service import blockchain_service
from app.services.ipfs_service import ipfs_service
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
audit_service = AuditService()

async def store_project_record_async(
    project_id: int,
    record_type: str,
    user_id: int,
    db: Session,
    metadata: dict = None
):
    """
    Async helper to store project record on blockchain.
    Designed to be used with FastAPI BackgroundTasks.
    """
    try:
        if not blockchain_service.is_available() or not ipfs_service.is_available():
            logger.warning(f"Blockchain/IPFS unavailable. Skipping auto-log for project {project_id}")
            return

        # Get project (create new session if needed, but passing db is safer for now 
        # assuming this runs before db session closes or handles its own scope if needed. 
        # For background tasks, it's safer to create a new session or be careful.
        # However, FastAPI BackgroundTasks runs AFTER response, so dependeny injection DB might be closed.
        # Ideally we should pass data, not DB session. But let's try to query freshly or assume 
        # we need to handle DB session lifecycle. 
        # ACTUALLY: Passing 'db' session to background task is risky as it might be closed.
        # We should create a new session here or pass necessary data. 
        # For simplicity in this existing architecture, let's try to get a fresh session 
        # or rely on the fact that we might need to query safely.
        
        # BETTER APPROACH: Do all DB reads in the main thread, pass DATA to this async function,
        # and create a NEW DB session here for writes.
        pass
        
    except Exception as e:
        logger.error(f"Background blockchain log failed: {e}")

# Revised approach: We will implement the logic to run largely independent of the request scope DB.
from app.database import SessionLocal

async def store_project_record_background(
    project_data: dict,
    record_type: str,
    user_id: int,
    metadata: dict = None
):
    """
    Store record on blockchain running in background.
    Manages its own DB session.
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting background blockchain log for project {project_data['id']} - {record_type}")
        
        # 1. Calculate Hash
        data_hash = blockchain_service.calculate_hash(project_data)
        
        # 2. Upload to IPFS
        ipfs_hash = await ipfs_service.upload_json(
            project_data,
            f"project_{project_data['id']}_{record_type}.json"
        )
        
        if not ipfs_hash:
            logger.error("Failed to upload to IPFS")
            return
            
        # 3. Store on Blockchain
        tx_hash = await blockchain_service.store_record(
            project_id=project_data['id'],
            ipfs_hash=ipfs_hash,
            data_hash=data_hash,
            record_type=record_type,
            metadata=metadata or {}
        )
        
        if not tx_hash:
            logger.error("Failed to store on blockchain")
            return
            
        # 4. Save to DB (Persistent Record)
        # We assume the project exists.
        blockchain_record = BlockchainRecord(
            project_id=project_data['id'],
            transaction_hash=tx_hash,
            ipfs_hash=ipfs_hash,
            record_type=RecordType(record_type),
            data_hash=data_hash,
            record_metadata=metadata,
            created_by=user_id
        )
        
        db.add(blockchain_record)
        db.commit()
        
        logger.info(f"Auto-logged blockchain record: {tx_hash}")
        
    except Exception as e:
        logger.error(f"Background task failed: {e}")
    finally:
        db.close()
