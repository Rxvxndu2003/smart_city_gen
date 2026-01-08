"""
IPFS service for decentralized file storage.
Supports multiple IPFS providers: Pinata, Web3.Storage, and local IPFS node.
"""
import os
import json
import logging
import httpx
from typing import Optional, Dict, Any, BinaryIO
from io import BytesIO

logger = logging.getLogger(__name__)


class IPFSService:
    """Service for storing and retrieving data from IPFS."""
    
    def __init__(self):
        # Pinata configuration
        self.pinata_api_key = os.getenv('PINATA_API_KEY')
        self.pinata_secret = os.getenv('PINATA_SECRET_KEY')
        
        # Web3.Storage configuration
        self.web3_storage_token = os.getenv('WEB3_STORAGE_TOKEN')
        
        # Local IPFS node configuration
        self.ipfs_api_url = os.getenv('IPFS_API_URL', 'http://localhost:5001')
        self.ipfs_gateway = os.getenv('IPFS_GATEWAY_URL', 'https://ipfs.io/ipfs/')
        
        # Determine which provider to use
        if self.pinata_api_key and self.pinata_secret:
            self.provider = 'pinata'
            logger.info("IPFS provider: Pinata")
        elif self.web3_storage_token:
            self.provider = 'web3storage'
            logger.info("IPFS provider: Web3.Storage")
        else:
            self.provider = 'local'
            logger.info(f"IPFS provider: Local node at {self.ipfs_api_url}")
    
    def is_available(self) -> bool:
        """Check if IPFS service is available."""
        if self.provider == 'pinata':
            return bool(self.pinata_api_key and self.pinata_secret)
        elif self.provider == 'web3storage':
            return bool(self.web3_storage_token)
        else:
            # Check local node
            try:
                import httpx
                response = httpx.get(f"{self.ipfs_api_url}/api/v0/id", timeout=5)
                return response.status_code == 200
            except:
                return False
    
    async def upload_json(self, data: Dict[str, Any], filename: str = "data.json") -> Optional[str]:
        """
        Upload JSON data to IPFS.
        
        Args:
            data: Dictionary to upload
            filename: Name for the file
            
        Returns:
            IPFS CID (Content Identifier) if successful
        """
        json_str = json.dumps(data, indent=2)
        json_bytes = json_str.encode('utf-8')
        
        return await self.upload_file(BytesIO(json_bytes), filename)
    
    async def upload_file(self, file: BinaryIO, filename: str) -> Optional[str]:
        """
        Upload a file to IPFS.
        
        Args:
            file: File-like object to upload
            filename: Name of the file
            
        Returns:
            IPFS CID if successful
        """
        if self.provider == 'pinata':
            return await self._upload_to_pinata(file, filename)
        elif self.provider == 'web3storage':
            return await self._upload_to_web3storage(file, filename)
        else:
            return await self._upload_to_local(file, filename)
    
    async def _upload_to_pinata(self, file: BinaryIO, filename: str) -> Optional[str]:
        """Upload file to Pinata."""
        try:
            async with httpx.AsyncClient() as client:
                files = {
                    'file': (filename, file, 'application/octet-stream')
                }
                
                headers = {
                    'pinata_api_key': self.pinata_api_key,
                    'pinata_secret_api_key': self.pinata_secret
                }
                
                # Optional metadata
                pinata_options = {
                    'cidVersion': 1
                }
                
                from datetime import datetime
                pinata_metadata = {
                    'name': filename,
                    'keyvalues': {
                        'source': 'smart_city_planning',
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                }
                
                data = {
                    'pinataOptions': json.dumps(pinata_options),
                    'pinataMetadata': json.dumps(pinata_metadata)
                }
                
                response = await client.post(
                    'https://api.pinata.cloud/pinning/pinFileToIPFS',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result['IpfsHash']
                    logger.info(f"File uploaded to Pinata: {ipfs_hash}")
                    return ipfs_hash
                else:
                    logger.error(f"Pinata upload failed: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Failed to upload to Pinata: {e}")
            return None
    
    async def _upload_to_web3storage(self, file: BinaryIO, filename: str) -> Optional[str]:
        """Upload file to Web3.Storage."""
        try:
            async with httpx.AsyncClient() as client:
                files = {
                    'file': (filename, file, 'application/octet-stream')
                }
                
                headers = {
                    'Authorization': f'Bearer {self.web3_storage_token}'
                }
                
                response = await client.post(
                    'https://api.web3.storage/upload',
                    files=files,
                    headers=headers,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result['cid']
                    logger.info(f"File uploaded to Web3.Storage: {ipfs_hash}")
                    return ipfs_hash
                else:
                    logger.error(f"Web3.Storage upload failed: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Failed to upload to Web3.Storage: {e}")
            return None
    
    async def _upload_to_local(self, file: BinaryIO, filename: str) -> Optional[str]:
        """Upload file to local IPFS node."""
        try:
            async with httpx.AsyncClient() as client:
                files = {
                    'file': (filename, file, 'application/octet-stream')
                }
                
                response = await client.post(
                    f'{self.ipfs_api_url}/api/v0/add',
                    files=files,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ipfs_hash = result['Hash']
                    logger.info(f"File uploaded to local IPFS: {ipfs_hash}")
                    return ipfs_hash
                else:
                    logger.error(f"Local IPFS upload failed: {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Failed to upload to local IPFS: {e}")
            return None
    
    async def get_file(self, ipfs_hash: str) -> Optional[bytes]:
        """
        Retrieve a file from IPFS.
        
        Args:
            ipfs_hash: IPFS CID
            
        Returns:
            File content as bytes
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ipfs_gateway}{ipfs_hash}",
                    timeout=60
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Failed to retrieve from IPFS: {response.status_code}")
                    return None
        
        except Exception as e:
            logger.error(f"Failed to get file from IPFS: {e}")
            return None
    
    async def get_json(self, ipfs_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve and parse JSON data from IPFS.
        
        Args:
            ipfs_hash: IPFS CID
            
        Returns:
            Parsed JSON data
        """
        content = await self.get_file(ipfs_hash)
        if content:
            try:
                return json.loads(content.decode('utf-8'))
            except Exception as e:
                logger.error(f"Failed to parse JSON from IPFS: {e}")
                return None
        return None
    
    def get_gateway_url(self, ipfs_hash: str) -> str:
        """Get public gateway URL for an IPFS hash."""
        if self.provider == 'pinata':
            return f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
        else:
            return f"{self.ipfs_gateway}{ipfs_hash}"
    
    async def pin_hash(self, ipfs_hash: str) -> bool:
        """
        Pin an existing IPFS hash (for Pinata).
        
        Args:
            ipfs_hash: IPFS CID to pin
            
        Returns:
            True if successful
        """
        if self.provider != 'pinata':
            logger.warning("Pin by hash only supported for Pinata")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'pinata_api_key': self.pinata_api_key,
                    'pinata_secret_api_key': self.pinata_secret,
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'hashToPin': ipfs_hash,
                    'pinataMetadata': {
                        'name': f'Pin of {ipfs_hash}'
                    }
                }
                
                response = await client.post(
                    'https://api.pinata.cloud/pinning/pinByHash',
                    json=data,
                    headers=headers,
                    timeout=60
                )
                
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"Failed to pin hash: {e}")
            return False


# Singleton instance
ipfs_service = IPFSService()
