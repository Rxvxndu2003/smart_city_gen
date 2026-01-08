# Smart City Blockchain Integration

## Overview
This directory contains the Ethereum smart contract and deployment scripts for immutable project record storage.

## Smart Contract: SmartCityRegistry.sol

### Features
- Store project design hashes on Ethereum
- Record approvals with cryptographic proof
- IPFS integration for off-chain data storage
- Event emission for indexing and tracking
- Verification of record authenticity

### Contract Functions

#### `storeRecord()`
Store a new project record on the blockchain.
```solidity
function storeRecord(
    uint256 _projectId,
    string memory _ipfsHash,
    string memory _dataHash,
    string memory _recordType,
    string memory _metadata
) public returns (uint256)
```

#### `recordApproval()`
Record an approval decision on the blockchain.
```solidity
function recordApproval(
    uint256 _projectId,
    string memory _ipfsHash,
    string memory _dataHash,
    string memory _approverRole,
    string memory _comment
) public returns (uint256)
```

#### `verifyRecord()`
Verify if a record with given hash exists.
```solidity
function verifyRecord(
    uint256 _projectId,
    string memory _dataHash
) public view returns (bool, uint256)
```

## Deployment Options

### Option 1: Local Testing (Ganache)
```bash
# Install Ganache
npm install -g ganache

# Start local blockchain
ganache --port 8545 --chainId 1337

# Deploy contract
npm install
node compile.js
node deploy.js
```

### Option 2: Ethereum Testnet (Sepolia/Goerli)
1. Get testnet ETH from faucet:
   - Sepolia: https://sepoliafaucet.com/
   - Goerli: https://goerlifaucet.com/

2. Set environment variables:
```bash
export ETHEREUM_PRIVATE_KEY="0x..."
export ETHEREUM_RPC_URL="https://sepolia.infura.io/v3/YOUR_API_KEY"
```

3. Deploy:
```bash
node compile.js
node deploy.js
```

### Option 3: Ethereum Mainnet (Production)
⚠️ **Warning**: Mainnet deployment costs real ETH!

1. Ensure you have sufficient ETH for deployment (estimate: 0.05-0.1 ETH)
2. Use a secure key management solution
3. Set environment variables:
```bash
export ETHEREUM_PRIVATE_KEY="0x..."
export ETHEREUM_RPC_URL="https://mainnet.infura.io/v3/YOUR_API_KEY"
```

4. Deploy:
```bash
node compile.js
node deploy.js
```

## RPC Providers

### Infura (Recommended)
1. Sign up at https://infura.io/
2. Create new project
3. Get RPC endpoint: `https://sepolia.infura.io/v3/YOUR_PROJECT_ID`

### Alchemy
1. Sign up at https://www.alchemy.com/
2. Create app
3. Get RPC endpoint: `https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY`

### QuickNode
1. Sign up at https://www.quicknode.com/
2. Create endpoint
3. Use provided URL

## IPFS Setup

### Option 1: Pinata (Recommended for Production)
1. Sign up at https://pinata.cloud/
2. Get API keys
3. Add to backend .env:
```
PINATA_API_KEY=your_api_key
PINATA_SECRET_KEY=your_secret_key
```

### Option 2: IPFS Desktop (Local Development)
1. Download from https://docs.ipfs.tech/install/ipfs-desktop/
2. Install and run
3. API available at http://localhost:5001

### Option 3: Web3.Storage
1. Sign up at https://web3.storage/
2. Get API token
3. Add to backend .env:
```
WEB3_STORAGE_TOKEN=your_token
```

## Backend Configuration

Add to `backend/.env`:
```env
# Ethereum Configuration
ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
ETHEREUM_CONTRACT_ADDRESS=0x...  # From deployment.json
ETHEREUM_PRIVATE_KEY=0x...  # Server wallet for transactions

# IPFS Configuration
IPFS_GATEWAY_URL=https://ipfs.io/ipfs/
PINATA_API_KEY=your_api_key
PINATA_SECRET_KEY=your_secret_key
```

## Compilation

### Using Solc (Solidity Compiler)
```bash
npm install -g solc
solcjs --bin --abi SmartCityRegistry.sol -o build/
```

### Using Remix IDE (Easiest)
1. Go to https://remix.ethereum.org/
2. Create new file: SmartCityRegistry.sol
3. Paste contract code
4. Compile (Ctrl+S)
5. Download ABI and bytecode
6. Save as SmartCityRegistry.json:
```json
{
  "abi": [...],
  "bytecode": "0x..."
}
```

## Testing

Run contract tests:
```bash
npm test
```

## Security Considerations

1. **Private Key Management**
   - Never commit private keys to git
   - Use environment variables
   - Consider using a hardware wallet for production

2. **Gas Optimization**
   - Batch operations when possible
   - Use events for indexing instead of storage

3. **Access Control**
   - Contract is permissionless by design
   - Backend should validate before submission
   - Consider adding role-based access if needed

## Cost Estimation

### Testnet (Free)
- Deployment: Free (testnet ETH from faucet)
- Transactions: Free

### Mainnet (Real Costs)
- Deployment: ~0.05-0.1 ETH (~$100-200)
- Record storage: ~0.002-0.005 ETH per record (~$5-10)
- Approval recording: ~0.003-0.007 ETH (~$7-15)

*Costs vary based on gas prices*

## Troubleshooting

### "Insufficient funds"
- Get testnet ETH from faucet
- Check balance: `web3.eth.getBalance(address)`

### "Contract creation failed"
- Check gas limit
- Verify RPC connection
- Check contract syntax

### "Nonce too low"
- Reset nonce in Web3 provider
- Wait for pending transactions

## Support

For issues or questions:
- Check Ethereum documentation: https://ethereum.org/en/developers/docs/
- Web3.js docs: https://web3js.readthedocs.io/
- IPFS docs: https://docs.ipfs.tech/
