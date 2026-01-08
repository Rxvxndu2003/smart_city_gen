/**
 * Compile SmartCityRegistry.sol contract
 * 
 * Usage: node compile.js
 */

const solc = require('solc');
const fs = require('fs');
const path = require('path');

console.log('🔨 Compiling SmartCityRegistry.sol...\n');

// Read contract source
const contractPath = path.join(__dirname, 'SmartCityRegistry.sol');
const source = fs.readFileSync(contractPath, 'utf8');

// Prepare input for compiler
const input = {
    language: 'Solidity',
    sources: {
        'SmartCityRegistry.sol': {
            content: source
        }
    },
    settings: {
        outputSelection: {
            '*': {
                '*': ['abi', 'evm.bytecode']
            }
        }
    }
};

// Compile
const output = JSON.parse(solc.compile(JSON.stringify(input)));

// Check for errors
if (output.errors) {
    const errors = output.errors.filter(e => e.severity === 'error');
    const warnings = output.errors.filter(e => e.severity === 'warning');
    
    if (warnings.length > 0) {
        console.log('⚠️  Warnings:');
        warnings.forEach(w => console.log(`   ${w.message}`));
        console.log();
    }
    
    if (errors.length > 0) {
        console.error('❌ Compilation errors:');
        errors.forEach(e => console.error(`   ${e.formattedMessage}`));
        process.exit(1);
    }
}

// Extract compiled contract
const contract = output.contracts['SmartCityRegistry.sol']['SmartCityRegistry'];
const abi = contract.abi;
const bytecode = contract.evm.bytecode.object;

// Save to JSON file
const compiledContract = {
    contractName: 'SmartCityRegistry',
    abi: abi,
    bytecode: '0x' + bytecode,
    compiledAt: new Date().toISOString(),
    compiler: {
        name: 'solc',
        version: solc.version()
    }
};

fs.writeFileSync(
    path.join(__dirname, 'SmartCityRegistry.json'),
    JSON.stringify(compiledContract, null, 2)
);

console.log('✅ Compilation successful!');
console.log(`📄 Output saved to: SmartCityRegistry.json`);
console.log(`📊 Contract size: ${(bytecode.length / 2).toLocaleString()} bytes`);
console.log(`🔧 Compiler version: ${solc.version()}\n`);
console.log('Next step: Run deployment with "node deploy.js"');
