/**
 * Generate a new Ethereum wallet for deployment
 * 
 * Usage: node generate-wallet.js
 * 
 * This will create a new random wallet and display:
 * - Private key (keep this SECRET!)
 * - Public address (for receiving testnet ETH)
 */

const { Web3 } = require('web3');

console.log('\n🔐 Generating new Ethereum wallet...\n');

// Create Web3 instance (doesn't need RPC for wallet generation)
const web3 = new Web3();

// Generate random wallet
const account = web3.eth.accounts.create();

console.log('✅ Wallet generated successfully!\n');
console.log('━'.repeat(70));
console.log('\n📋 WALLET DETAILS:\n');
console.log(`Address:     ${account.address}`);
console.log(`Private Key: ${account.privateKey}`);
console.log('\n━'.repeat(70));

console.log('\n⚠️  IMPORTANT SECURITY NOTES:\n');
console.log('1. Keep your private key SECRET - never share it or commit to git!');
console.log('2. Anyone with your private key can access your funds!');
console.log('3. Store it safely in your .env file\n');

console.log('📝 Next steps:\n');
console.log('1. Copy the private key above');
console.log('2. Update blockchain/.env:');
console.log(`   ETHEREUM_PRIVATE_KEY=${account.privateKey}`);
console.log('3. Get testnet ETH from a faucet:');
console.log(`   - Address to fund: ${account.address}`);
console.log('   - Sepolia faucet: https://sepoliafaucet.com/');
console.log('   - Alternative: https://sepolia-faucet.pk910.de/\n');
console.log('4. After receiving ETH, run: npm run deploy\n');
