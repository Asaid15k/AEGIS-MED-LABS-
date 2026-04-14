from web3 import Web3
import json
import os

CONTRACT_ADDRESS = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

artifact_path = r"C:\Users\asaid\OneDrive\Desktop\AEGIS-MED-LABS--main\my-hardhat-project\artifacts\contracts\PrescriptionRegistry.sol\PrescriptionRegistry.json"
with open(artifact_path) as f:
    artifact = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=artifact["abi"])

def store_hash(prescription_id, data_hash):
    tx = contract.functions.storePrescription(prescription_id, data_hash).transact({
        "from": w3.eth.accounts[0]
    })
    w3.eth.wait_for_transaction_receipt(tx)

def get_hash(prescription_id):
    result = contract.functions.prescriptions(prescription_id).call()
    return result[1]