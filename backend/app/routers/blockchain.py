"""
Blockchain router - Ethereum and IPFS integration endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.blockchain_record import BlockchainRecord, RecordType
from app.services.blockchain_service import blockchain_service
from app.services.ipfs_service import ipfs_service
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter()
audit_service = AuditService()


class StoreRecordRequest(BaseModel):
    """Request to store a record on blockchain."""
    project_id: int
    record_type: str
    metadata: Optional[Dict[str, Any]] = None


class VerifyRecordRequest(BaseModel):
    """Request to verify a record."""
    project_id: int
    data_hash: str


@router.get("/status")
async def get_blockchain_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get blockchain service status.
    """
    blockchain_available = blockchain_service.is_available()
    ipfs_available = ipfs_service.is_available()
    
    status_info = {
        "blockchain": {
            "available": blockchain_available,
            "provider": "Ethereum",
            "network": blockchain_service.rpc_url if blockchain_available else None,
            "contract_address": blockchain_service.contract_address if blockchain_available else None
        },
        "ipfs": {
            "available": ipfs_available,
            "provider": ipfs_service.provider,
            "gateway": ipfs_service.ipfs_gateway if ipfs_available else None
        }
    }
    
    # Add account info if admin
    user_roles = [ur.role.name for ur in current_user.user_roles]
    if "Admin" in user_roles and blockchain_available:
        balance = blockchain_service.get_account_balance()
        status_info["blockchain"]["account_balance_eth"] = balance
        
        gas_estimate = blockchain_service.estimate_gas_cost()
        status_info["blockchain"]["estimated_gas_cost"] = gas_estimate
    
    return status_info


@router.post("/store")
async def store_project_on_blockchain(
    request: StoreRecordRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Store a project record on blockchain and IPFS.
    This creates an immutable proof of the project state.
    """
    # Check if blockchain is available
    if not blockchain_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is not available"
        )
    
    if not ipfs_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IPFS service is not available"
        )
    
    # Get project
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_admin = "Admin" in user_roles
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to store this project on blockchain"
        )
    
    try:
        # Prepare project data for storage
        project_data = {
            "project_id": project.id,
            "name": project.name,
            "description": project.description,
            "project_type": project.project_type,
            "location": {
                "address": project.location_address,
                "district": project.location_district,
                "city": project.location_city,
                "coordinates": project.location_coordinates
            },
            "specifications": {
                "site_area_m2": float(project.site_area_m2) if project.site_area_m2 else None,
                "building_coverage": float(project.building_coverage) if project.building_coverage else None,
                "floor_area_ratio": float(project.floor_area_ratio) if project.floor_area_ratio else None,
                "num_floors": project.num_floors,
                "building_height": float(project.building_height) if project.building_height else None,
                "parking_spaces": project.parking_spaces
            },
            "status": project.status.value,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "owner": project.owner_name,
            "metadata": request.metadata or {},
            "record_type": request.record_type
        }
        
        # Calculate data hash
        data_hash = blockchain_service.calculate_hash(project_data)
        
        # Upload to IPFS
        logger.info(f"Uploading project {project.id} to IPFS...")
        ipfs_hash = await ipfs_service.upload_json(
            project_data,
            f"project_{project.id}_{request.record_type}.json"
        )
        
        if not ipfs_hash:
            raise Exception("Failed to upload to IPFS")
        
        logger.info(f"Project uploaded to IPFS: {ipfs_hash}")
        
        # Store on blockchain
        logger.info(f"Storing record on blockchain...")
        tx_hash = await blockchain_service.store_record(
            project_id=project.id,
            ipfs_hash=ipfs_hash,
            data_hash=data_hash,
            record_type=request.record_type,
            metadata=request.metadata or {}
        )
        
        if not tx_hash:
            raise Exception("Failed to store on blockchain")
        
        logger.info(f"Record stored on blockchain: {tx_hash}")
        
        # Save to database
        blockchain_record = BlockchainRecord(
            project_id=project.id,
            transaction_hash=tx_hash,
            ipfs_hash=ipfs_hash,
            record_type=RecordType(request.record_type),
            data_hash=data_hash,
            record_metadata=request.metadata,
            created_by=current_user.id
        )
        
        db.add(blockchain_record)
        db.commit()
        db.refresh(blockchain_record)
        
        # Audit log
        audit_service.log_action(
            db=db,
            user_id=current_user.id,
            action="BLOCKCHAIN_RECORD_CREATED",
            resource_type="blockchain_record",
            resource_id=blockchain_record.id,
            details={
                "project_id": project.id,
                "tx_hash": tx_hash,
                "ipfs_hash": ipfs_hash,
                "record_type": request.record_type
            }
        )
        
        return {
            "success": True,
            "record_id": blockchain_record.id,
            "transaction_hash": tx_hash,
            "ipfs_hash": ipfs_hash,
            "ipfs_url": ipfs_service.get_gateway_url(ipfs_hash),
            "data_hash": data_hash,
            "message": "Project record stored on blockchain successfully"
        }
    
    except Exception as e:
        logger.error(f"Failed to store project on blockchain: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store on blockchain: {str(e)}"
        )


@router.post("/verify")
async def verify_record(
    request: VerifyRecordRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify if a record exists on the blockchain.
    """
    if not blockchain_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is not available"
        )
    
    try:
        exists, timestamp = blockchain_service.verify_record(
            request.project_id,
            request.data_hash
        )
        
        return {
            "exists": exists,
            "timestamp": timestamp,
            "verified_at": exists
        }
    
    except Exception as e:
        logger.error(f"Failed to verify record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/project/{project_id}/records")
async def get_project_blockchain_records(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all blockchain records for a project.
    """
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check permissions
    user_roles = [ur.role.name for ur in current_user.user_roles]
    is_owner = project.owner_id == current_user.id
    is_authorized = is_owner or any(
        role in ["Admin", "Architect", "Engineer", "Regulator"]
        for role in user_roles
    )
    
    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view blockchain records"
        )
    
    # Get records from database
    db_records = db.query(BlockchainRecord).filter(
        BlockchainRecord.project_id == project_id
    ).order_by(BlockchainRecord.created_at.desc()).all()
    
    records = []
    for record in db_records:
        records.append({
            "id": record.id,
            "transaction_hash": record.transaction_hash,
            "ipfs_hash": record.ipfs_hash,
            "ipfs_url": ipfs_service.get_gateway_url(record.ipfs_hash) if record.ipfs_hash else None,
            "record_type": record.record_type.value,
            "data_hash": record.data_hash,
            "metadata": record.record_metadata,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "created_by": record.creator.full_name if record.creator else None
        })
    
    # If blockchain is available, get on-chain records too
    blockchain_records = []
    if blockchain_service.is_available():
        try:
            blockchain_records = blockchain_service.get_project_records(project_id)
        except Exception as e:
            logger.warning(f"Failed to get blockchain records: {e}")
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "database_records": records,
        "blockchain_records": blockchain_records,
        "total_records": len(records)
    }


@router.get("/ipfs/{ipfs_hash}")
async def get_ipfs_data(
    ipfs_hash: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve data from IPFS.
    """
    if not ipfs_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="IPFS service is not available"
        )
    
    try:
        data = await ipfs_service.get_json(ipfs_hash)
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Data not found on IPFS"
            )
        
        return {
            "ipfs_hash": ipfs_hash,
            "data": data,
            "gateway_url": ipfs_service.get_gateway_url(ipfs_hash)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve from IPFS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve data: {str(e)}"
        )
