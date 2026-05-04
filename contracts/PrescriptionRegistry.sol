// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract PrescriptionRegistry {
    mapping(uint256 => bytes32) public prescriptions;

    event PrescriptionStored(
        uint256 indexed prescriptionId,
        bytes32 hash
    );

    function storePrescription(
        uint256 prescriptionId,
        bytes32 hash
    ) public {
        prescriptions[prescriptionId] = hash;
        emit PrescriptionStored(prescriptionId, hash);
    }

    function getHash(
        uint256 prescriptionId
    ) public view returns (bytes32) {
        return prescriptions[prescriptionId];
    }
}