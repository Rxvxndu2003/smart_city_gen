"""
Blockchain service for Ethereum integration.
Handles smart contract interactions for immutable project records.
"""
import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
try:
    # Try newer web3.py version (6.0+)
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        # Try older web3.py version (5.x)
        from web3.middleware import geth_poa_middleware
    except ImportError:
        # Fallback: no PoA middleware
        geth_poa_middleware = None
from eth_account import Account

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for interacting with Ethereum blockchain."""
    
    def __init__(self):
        self.rpc_url = os.getenv('ETHEREUM_RPC_URL')
        self.contract_address = os.getenv('ETHEREUM_CONTRACT_ADDRESS')
        self.private_key = os.getenv('ETHEREUM_PRIVATE_KEY')
        
        self.web3: Optional[Web3] = None
        self.contract = None
        self.account = None
        
        if self.rpc_url and self.contract_address:
            self._initialize()
    
    def _initialize(self):
        """Initialize Web3 and contract instance."""
        try:
            # Connect to Ethereum network
            self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add middleware for PoA networks (like Sepolia, Goerli)
            if geth_poa_middleware:
                try:
                    self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    logger.info("PoA middleware injected")
                except Exception as e:
                    logger.warning(f"Could not inject PoA middleware: {e}")
            
            if not self.web3.is_connected():
                logger.error("Failed to connect to Ethereum network")
                return
            
            logger.info(f"Connected to Ethereum network: {self.rpc_url}")
            
            # Load contract ABI
            abi_path = os.path.join(
                os.path.dirname(__file__),
                '../../../blockchain/SmartCityRegistry.json'
            )
            
            if os.path.exists(abi_path):
                with open(abi_path, 'r') as f:
                    contract_json = json.load(f)
                    self.contract = self.web3.eth.contract(
                        address=Web3.to_checksum_address(self.contract_address),
                        abi=contract_json['abi']
                    )
                logger.info(f"Contract loaded: {self.contract_address}")
            else:
                logger.warning(f"Contract ABI not found at {abi_path}")
            
            # Setup account if private key provided
            if self.private_key:
                self.account = Account.from_key(self.private_key)
                logger.info(f"Account loaded: {self.account.address}")
        
        except Exception as e:
            logger.error(f"Failed to initialize blockchain service: {e}")
    
    def is_available(self) -> bool:
        """Check if blockchain service is available."""
        return (
            self.web3 is not None and 
            self.web3.is_connected() and 
            self.contract is not None
        )
    
    def calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of data."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    async def store_record(
        self,
        project_id: int,
        ipfs_hash: str,
        data_hash: str,
        record_type: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Store a record on the blockchain.
        
        Args:
            project_id: Project ID
            ipfs_hash: IPFS CID of stored data
            data_hash: SHA-256 hash of data
            record_type: Type of record (DESIGN_HASH, APPROVAL, etc.)
            metadata: Additional metadata
            
        Returns:
            Transaction hash if successful, None otherwise
        """
        if not self.is_available():
            logger.error("Blockchain service not available")
            return None
        
        if not self.account:
            logger.error("No account configured for transactions")
            return None
        
        try:
            metadata_json = json.dumps(metadata)
            
            # Build transaction
            function = self.contract.functions.storeRecord(
                project_id,
                ipfs_hash,
                data_hash,
                record_type,
                metadata_json
            )
            
            # Estimate gas
            gas_estimate = function.estimate_gas({'from': self.account.address})
            
            # Get current gas price
            gas_price = self.web3.eth.gas_price
            
            # Build transaction
            transaction = function.build_transaction({
                'from': self.account.address,
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                private_key=self.private_key
            )
            
            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                tx_hash_hex = tx_hash.hex()
                logger.info(f"Record stored on blockchain: {tx_hash_hex}")
                return tx_hash_hex
            else:
                logger.error(f"Transaction failed: {receipt}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to store record on blockchain: {e}")
            return None
    
    async def record_approval(
        self,
        project_id: int,
        ipfs_hash: str,
        data_hash: str,
        approver_role: str,
        comment: str
    ) -> Optional[str]:
        """
        Record an approval on the blockchain.
        
        Args:
            project_id: Project ID
            ipfs_hash: IPFS CID
            data_hash: SHA-256 hash
            approver_role: Role of approver
            comment: Approval comment
            
        Returns:
            Transaction hash if successful
        """
        if not self.is_available():
            logger.error("Blockchain service not available")
            return None
        
        if not self.account:
            logger.error("No account configured for transactions")
            return None
        
        try:
            # Build transaction
            function = self.contract.functions.recordApproval(
                project_id,
                ipfs_hash,
                data_hash,
                approver_role,
                comment
            )
            
            # Estimate gas
            gas_estimate = function.estimate_gas({'from': self.account.address})
            
            # Get current gas price
            gas_price = self.web3.eth.gas_price
            
            # Build transaction
            transaction = function.build_transaction({
                'from': self.account.address,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': gas_price,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send
            signed_txn = self.web3.eth.account.sign_transaction(
                transaction,
                private_key=self.private_key
            )
            
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt['status'] == 1:
                tx_hash_hex = tx_hash.hex()
                logger.info(f"Approval recorded on blockchain: {tx_hash_hex}")
                return tx_hash_hex
            else:
                logger.error(f"Transaction failed: {receipt}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to record approval: {e}")
            return None
    
    def verify_record(self, project_id: int, data_hash: str) -> tuple[bool, Optional[int]]:
        """
        Verify if a record exists on the blockchain.
        
        Args:
            project_id: Project ID
            data_hash: SHA-256 hash to verify
            
        Returns:
            Tuple of (exists, timestamp)
        """
        if not self.is_available():
            return False, None
        
        try:
            exists, timestamp = self.contract.functions.verifyRecord(
                project_id,
                data_hash
            ).call()
            
            return exists, int(timestamp) if exists else None
        
        except Exception as e:
            logger.error(f"Failed to verify record: {e}")
            return False, None
    
    def get_project_records(self, project_id: int) -> list[Dict[str, Any]]:
        """
        Get all blockchain records for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of records
        """
        if not self.is_available():
            return []
        
        try:
            records = self.contract.functions.getAllProjectRecords(project_id).call()
            
            result = []
            for record in records:
                result.append({
                    'project_id': record[0],
                    'ipfs_hash': record[1],
                    'data_hash': record[2],
                    'record_type': record[3],
                    'submitted_by': record[4],
                    'timestamp': datetime.fromtimestamp(record[5]).isoformat(),
                    'metadata': json.loads(record[6]) if record[6] else {}
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get project records: {e}")
            return []
    
    def get_account_balance(self) -> Optional[float]:
        """Get balance of configured account in ETH."""
        if not self.is_available() or not self.account:
            return None
        
        try:
            balance_wei = self.web3.eth.get_balance(self.account.address)
            return float(self.web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return None
    
    def estimate_gas_cost(self, operation: str = 'store_record') -> Optional[Dict[str, float]]:
        """
        Estimate gas cost for an operation.
        
        Returns:
            Dict with gas and ETH estimates
        """
        if not self.is_available():
            return None
        
        try:
            gas_price = self.web3.eth.gas_price
            
            # Estimated gas units for different operations
            gas_estimates = {
                'store_record': 150000,
                'record_approval': 180000,
                'verify_record': 50000
            }
            
            gas_units = gas_estimates.get(operation, 150000)
            gas_cost_wei = gas_units * gas_price
            gas_cost_eth = float(self.web3.from_wei(gas_cost_wei, 'ether'))
            
            return {
                'gas_units': gas_units,
                'gas_price_gwei': float(self.web3.from_wei(gas_price, 'gwei')),
                'estimated_cost_eth': gas_cost_eth,
                'estimated_cost_usd': gas_cost_eth * 2000  # Approximate ETH price
            }
        
        except Exception as e:
            logger.error(f"Failed to estimate gas: {e}")
            return None


# Singleton instance
blockchain_service = BlockchainService()
