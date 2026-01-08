// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SmartCityRegistry
 * @dev Contract for storing immutable urban planning project records
 */
contract SmartCityRegistry {
    struct ProjectRecord {
        uint256 projectId;
        string ipfsHash;      // IPFS CID of project data
        string dataHash;      // SHA-256 hash of project data
        string recordType;    // DESIGN_HASH, APPROVAL, EXPORT, CERTIFICATE
        address submittedBy;
        uint256 timestamp;
        string metadata;      // JSON metadata
    }
    
    // Mapping: project ID => array of records
    mapping(uint256 => ProjectRecord[]) public projectRecords;
    
    // Mapping: transaction hash => record exists
    mapping(bytes32 => bool) public recordExists;
    
    // Events
    event RecordStored(
        uint256 indexed projectId,
        uint256 recordIndex,
        string ipfsHash,
        string dataHash,
        string recordType,
        address indexed submittedBy,
        uint256 timestamp
    );
    
    event ApprovalRecorded(
        uint256 indexed projectId,
        string ipfsHash,
        address indexed approver,
        uint256 timestamp
    );
    
    /**
     * @dev Store a new project record on the blockchain
     */
    function storeRecord(
        uint256 _projectId,
        string memory _ipfsHash,
        string memory _dataHash,
        string memory _recordType,
        string memory _metadata
    ) public returns (uint256) {
        require(_projectId > 0, "Invalid project ID");
        require(bytes(_ipfsHash).length > 0, "IPFS hash required");
        require(bytes(_dataHash).length > 0, "Data hash required");
        
        // Create unique record identifier
        bytes32 recordId = keccak256(abi.encodePacked(
            _projectId,
            _ipfsHash,
            _dataHash,
            block.timestamp
        ));
        
        require(!recordExists[recordId], "Record already exists");
        
        ProjectRecord memory newRecord = ProjectRecord({
            projectId: _projectId,
            ipfsHash: _ipfsHash,
            dataHash: _dataHash,
            recordType: _recordType,
            submittedBy: msg.sender,
            timestamp: block.timestamp,
            metadata: _metadata
        });
        
        projectRecords[_projectId].push(newRecord);
        recordExists[recordId] = true;
        
        uint256 recordIndex = projectRecords[_projectId].length - 1;
        
        emit RecordStored(
            _projectId,
            recordIndex,
            _ipfsHash,
            _dataHash,
            _recordType,
            msg.sender,
            block.timestamp
        );
        
        return recordIndex;
    }
    
    /**
     * @dev Record an approval on the blockchain
     */
    function recordApproval(
        uint256 _projectId,
        string memory _ipfsHash,
        string memory _dataHash,
        string memory _approverRole,
        string memory _comment
    ) public returns (uint256) {
        string memory metadata = string(abi.encodePacked(
            '{"approverRole":"', _approverRole, 
            '","comment":"', _comment, 
            '","approver":"', toAsciiString(msg.sender),
            '"}'
        ));
        
        uint256 recordIndex = storeRecord(
            _projectId,
            _ipfsHash,
            _dataHash,
            "APPROVAL",
            metadata
        );
        
        emit ApprovalRecorded(_projectId, _ipfsHash, msg.sender, block.timestamp);
        
        return recordIndex;
    }
    
    /**
     * @dev Get the number of records for a project
     */
    function getProjectRecordCount(uint256 _projectId) public view returns (uint256) {
        return projectRecords[_projectId].length;
    }
    
    /**
     * @dev Get a specific record for a project
     */
    function getRecord(uint256 _projectId, uint256 _index) 
        public 
        view 
        returns (
            string memory ipfsHash,
            string memory dataHash,
            string memory recordType,
            address submittedBy,
            uint256 timestamp,
            string memory metadata
        ) 
    {
        require(_index < projectRecords[_projectId].length, "Record does not exist");
        
        ProjectRecord memory record = projectRecords[_projectId][_index];
        
        return (
            record.ipfsHash,
            record.dataHash,
            record.recordType,
            record.submittedBy,
            record.timestamp,
            record.metadata
        );
    }
    
    /**
     * @dev Get all records for a project
     */
    function getAllProjectRecords(uint256 _projectId) 
        public 
        view 
        returns (ProjectRecord[] memory) 
    {
        return projectRecords[_projectId];
    }
    
    /**
     * @dev Verify a record exists with given hash
     */
    function verifyRecord(
        uint256 _projectId,
        string memory _dataHash
    ) public view returns (bool, uint256) {
        ProjectRecord[] memory records = projectRecords[_projectId];
        
        for (uint256 i = 0; i < records.length; i++) {
            if (keccak256(bytes(records[i].dataHash)) == keccak256(bytes(_dataHash))) {
                return (true, records[i].timestamp);
            }
        }
        
        return (false, 0);
    }
    
    /**
     * @dev Helper function to convert address to string
     */
    function toAsciiString(address x) internal pure returns (string memory) {
        bytes memory s = new bytes(40);
        for (uint i = 0; i < 20; i++) {
            bytes1 b = bytes1(uint8(uint(uint160(x)) / (2**(8*(19 - i)))));
            bytes1 hi = bytes1(uint8(b) / 16);
            bytes1 lo = bytes1(uint8(b) - 16 * uint8(hi));
            s[2*i] = char(hi);
            s[2*i+1] = char(lo);
        }
        return string(abi.encodePacked("0x", s));
    }
    
    function char(bytes1 b) internal pure returns (bytes1 c) {
        if (uint8(b) < 10) return bytes1(uint8(b) + 0x30);
        else return bytes1(uint8(b) + 0x57);
    }
}
