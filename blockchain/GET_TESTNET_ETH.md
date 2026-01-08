# 🚀 Quick Deployment Guide

## Current Status

✅ Wallet created: `0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF`  
❌ Balance: 0 ETH (needs testnet ETH)

## Get Testnet ETH (Required for Deployment)

Your wallet needs Sepolia testnet ETH to deploy the smart contract. Here are the easiest options:

### Option 1: Sepolia Faucet (Recommended - Fastest)
1. Visit: https://sepoliafaucet.com/
2. Paste your wallet address: `0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF`
3. Complete the captcha
4. Click "Request 0.5 SepoliaETH"
5. Wait 1-2 minutes for confirmation

### Option 2: Alchemy Faucet
1. Visit: https://www.alchemy.com/faucets/ethereum-sepolia
2. Sign in with Alchemy (free account)
3. Paste wallet address: `0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF`
4. Receive 0.5 ETH instantly

### Option 3: QuickNode Faucet  
1. Visit: https://faucet.quicknode.com/ethereum/sepolia
2. Connect Twitter or complete verification
3. Paste wallet: `0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF`
4. Receive ETH

### Option 4: POW Faucet (No limits!)
1. Visit: https://sepolia-faucet.pk910.de/
2. Paste wallet: `0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF`
3. Start mining (browser-based, takes ~10-30 minutes for 0.05 ETH)
4. Good for larger amounts

## Check Your Balance

After requesting from a faucet, check if ETH arrived:

```bash
# Visit Sepolia Etherscan:
https://sepolia.etherscan.io/address/0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF

# Or run the deployment script (it will show balance):
npm run deploy
```

## Deploy Contract

Once you have testnet ETH (0.1+ recommended):

```bash
cd /Users/ravindubandara/Desktop/smart_city/blockchain
npm run deploy
```

Expected output:
```
🚀 Starting SmartCityRegistry deployment...
📡 Connected to: https://sepolia.infura.io/...
👤 Deployer address: 0x75eF0ae8ed6C0B3eb23607D2b2C0f5161A8F94CF
💰 Balance: 0.5 ETH

📝 Deploying contract...
⛽ Estimated gas: 2333920
✅ Contract deployed successfully!
📍 Contract address: 0x...
🔗 Transaction hash: 0x...
```

## After Deployment

The deployment script will automatically save contract details to `deployment.json`. You'll need to:

1. Copy the contract address to backend `.env`:
   ```bash
   ETHEREUM_CONTRACT_ADDRESS=<contract_address_from_deployment.json>
   ```

2. Restart the backend server to load blockchain integration

## Troubleshooting

**"Insufficient funds for deployment"**
- Get more testnet ETH from faucets above
- You need ~0.05-0.1 ETH for deployment

**"Network error" or "RPC URL failed"**
- Check your internet connection
- Infura might be down, try later
- Alternative RPC: Get free Alchemy key at https://www.alchemy.com/

**"Contract ABI not found"**
- Run `npm run compile` first
- Check that `SmartCityRegistry.json` exists

## Important Notes

⚠️ **Keep your private key secret!** It's stored in `.env` which is gitignored.  
💰 This is **testnet ETH** - it has no real value  
🔄 Testnet can be reset, your contract might disappear (rare)  
📊 Deployment costs ~$0 (testnet is free)

## Next Steps After Deployment

1. ✅ Contract deployed on Sepolia
2. Configure backend with contract address  
3. Test blockchain endpoints via API
4. Store your first project on blockchain!

---

Need help? Check the main `BLOCKCHAIN_SETUP.md` for detailed documentation.
