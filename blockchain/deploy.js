/**
 * Deployment script for SmartCityRegistry contract
 * 
 * Usage:
 * 1. Install dependencies: npm install web3 @truffle/hdwallet-provider
 * 2. Set environment variables in .env:
 *    - ETHEREUM_PRIVATE_KEY
 *    - ETHEREUM_RPC_URL (e.g., Infura/Alchemy endpoint)
 * 3. Run: node deploy.js
 */

const { Web3 } = require('web3');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

// Compiled contract ABI and bytecode
// You need to compile the Solidity contract first using solc or Remix
const contractJSON = require('./SmartCityRegistry.json'); // Generated from compilation

async function deploy() {
    console.log('🚀 Starting SmartCityRegistry deployment...\n');
    
    // Connect to Ethereum network
    const rpcUrl = process.env.ETHEREUM_RPC_URL || 'http://localhost:8545'; // Ganache for local testing
    const web3 = new Web3(rpcUrl);
    
    console.log(`📡 Connected to: ${rpcUrl}`);
    
    // Get deployer account
    const privateKey = process.env.ETHEREUM_PRIVATE_KEY;
    if (!privateKey) {
        console.error('❌ ETHEREUM_PRIVATE_KEY not set in environment variables');
        process.exit(1);
    }
    
    const account = web3.eth.accounts.privateKeyToAccount(privateKey);
    web3.eth.accounts.wallet.add(account);
    web3.eth.defaultAccount = account.address;
    
    console.log(`👤 Deployer address: ${account.address}`);
    
    // Check balance
    const balance = await web3.eth.getBalance(account.address);
    console.log(`💰 Balance: ${web3.utils.fromWei(balance, 'ether')} ETH\n`);
    
    if (balance === '0') {
        console.error('❌ Insufficient funds for deployment');
        process.exit(1);
    }
    
    // Create contract instance
    const contract = new web3.eth.Contract(contractJSON.abi);
    
    // Deploy contract
    console.log('📝 Deploying contract...');
    
    const deployTx = contract.deploy({
        data: contractJSON.bytecode,
        arguments: []
    });
    
    const gas = await deployTx.estimateGas({ from: account.address });
    console.log(`⛽ Estimated gas: ${gas}`);
    
    // Convert BigInt to Number for calculations
    const gasLimit = Number(gas);
    const gasWithBuffer = Math.floor(gasLimit * 1.2); // Add 20% buffer
    
    const deployedContract = await deployTx.send({
        from: account.address,
        gas: gasWithBuffer,
        gasPrice: await web3.eth.getGasPrice()
    });
    
    console.log('\n✅ Contract deployed successfully!');
    console.log(`📍 Contract address: ${deployedContract.options.address}`);
    console.log(`🔗 Transaction hash: ${deployedContract.transactionHash}`);
    
    // Save deployment info
    const deploymentInfo = {
        contractAddress: deployedContract.options.address,
        transactionHash: deployedContract.transactionHash,
        deployer: account.address,
        network: rpcUrl,
        deployedAt: new Date().toISOString(),
        abi: contractJSON.abi
    };
    
    fs.writeFileSync(
        path.join(__dirname, 'deployment.json'),
        JSON.stringify(deploymentInfo, null, 2)
    );
    
    console.log('\n📄 Deployment info saved to deployment.json');
    console.log('\n🎉 Deployment complete!');
    console.log('\n📋 Next steps:');
    console.log('1. Add contract address to backend .env:');
    console.log(`   ETHEREUM_CONTRACT_ADDRESS=${deployedContract.options.address}`);
    console.log('2. Add RPC URL to backend .env:');
    console.log(`   ETHEREUM_RPC_URL=${rpcUrl}`);
}

deploy().catch(console.error);
