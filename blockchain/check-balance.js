/**
 * Check wallet balance on Sepolia testnet
 * 
 * Usage: node check-balance.js
 */

const { Web3 } = require('web3');
require('dotenv').config();

async function checkBalance() {
    const rpcUrl = process.env.ETHEREUM_RPC_URL || 'http://localhost:8545';
    const privateKey = process.env.ETHEREUM_PRIVATE_KEY;
    
    if (!privateKey) {
        console.error('❌ ETHEREUM_PRIVATE_KEY not set in .env file');
        process.exit(1);
    }
    
    const web3 = new Web3(rpcUrl);
    const account = web3.eth.accounts.privateKeyToAccount(privateKey);
    
    console.log('\n💼 Wallet Information:\n');
    console.log(`Address: ${account.address}`);
    console.log(`Network: ${rpcUrl}\n`);
    
    try {
        const balance = await web3.eth.getBalance(account.address);
        const balanceEth = web3.utils.fromWei(balance, 'ether');
        
        console.log(`Balance: ${balanceEth} ETH\n`);
        
        if (parseFloat(balanceEth) === 0) {
            console.log('⚠️  Your wallet has no ETH!');
            console.log('\n📝 To deploy the contract, you need testnet ETH.');
            console.log('\n🚰 Get free testnet ETH from these faucets:');
            console.log('   1. https://sepoliafaucet.com/');
            console.log('   2. https://www.alchemy.com/faucets/ethereum-sepolia');
            console.log('   3. https://faucet.quicknode.com/ethereum/sepolia');
            console.log(`\n👉 Use this address: ${account.address}\n`);
        } else if (parseFloat(balanceEth) < 0.05) {
            console.log('⚠️  Low balance - you might need more ETH for deployment');
            console.log('   Recommended: 0.1+ ETH for safe deployment\n');
        } else {
            console.log('✅ You have enough ETH to deploy the contract!');
            console.log('   Run: npm run deploy\n');
        }
        
        // Check Etherscan link
        console.log(`🔍 View on Etherscan: https://sepolia.etherscan.io/address/${account.address}\n`);
        
    } catch (error) {
        console.error('❌ Error checking balance:', error.message);
        console.log('\nMake sure:');
        console.log('1. Your internet connection is working');
        console.log('2. The RPC URL in .env is correct');
        console.log('3. Infura/Alchemy service is operational\n');
    }
}

checkBalance().catch(console.error);
