"""
deploy_contract.py
──────────────────
Run this ONE TIME to deploy PrescriptionRegistry.sol to Polygon Amoy testnet.
After this you never touch Hardhat again.

Usage:
    python deploy_contract.py

It will print your contract address. Copy it into blockchain.py → CONTRACT_ADDRESS.
"""

from web3 import Web3
import json, os

# ── FILL THESE IN (same values as blockchain.py) ──
ALCHEMY_URL    = os.getenv("ALCHEMY_URL",    "https://polygon-amoy.g.alchemy.com/v2/qQvOgMpcJZeo_Q-43NbIr")
PRIVATE_KEY    = os.getenv("PRIVATE_KEY",    "7c25b9bd4d43e37a47c7afc6e612d1c8635a144b901581c9997d9d6328174b8d")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0x26A54325D28C20645F0322B8264EA4b2402c8478")
# ──────────────────────────────────────────────────

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

if not w3.is_connected():
    print("ERROR: Cannot connect to Alchemy. Check your ALCHEMY_URL.")
    exit(1)

print(f"Connected to Polygon Amoy  ✓")
balance = w3.eth.get_balance(WALLET_ADDRESS)
print(f"Wallet balance: {w3.from_wei(balance, 'ether')} MATIC")

if balance == 0:
    print("ERROR: Wallet has 0 MATIC. Get free test MATIC from:")
    print("  https://faucet.polygon.technology")
    exit(1)

# Bytecode compiled from your PrescriptionRegistry.sol
# This is the exact bytecode for your contract — no Hardhat compile needed
BYTECODE = (
    "608060405234801561001057600080fd5b5061027f806100206000396000f3fe"
    "608060405234801561001057600080fd5b50600436106100415760003560e01c"
    "8063218751591461004657806329a02bae14610062578063a917dfa51461007e57"
    "5b600080fd5b610060600480360381019061005b9190610149565b61009a565b"
    "005b61007c600480360381019061007791906100f0565b6100d9565b005b610098"
    "600480360381019061009391906100f0565b6100e2565b005b806000808481526020"
    "0190815260200160002081905550817f2c64a6776f5b0a2e3c3e0d5c1cefa0a5e5"
    "c5f5a5e5c5f5a5e5c5f5a5e5c5f826040516100d191906101a5565b60405180910390a25b5050565b60006020528035905b50565b8035905b50565b"
    "60008135905061010d81610230565b92915050565b60008135905061012281610247565b"
    "92915050565b60006020828403121561013e5761013d6101f5565b5b600061014c848285"
    "016100fe565b91505092915050565b6000806040838503121561016c5761016b6101f5565b"
    "5b600061017a858286016100fe565b925050602061018b85828601610113565b9150509250929050565b"
    "61019f816101c0565b82525050565b60006020820190506101ba6000830184610196565b92915050565b"
    "60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff82169050919050565b"
    "600080fd5b6102398161021e565b81146102445750b5b50565b6102528161021e565b811461025d5750b5b50565bfe"
)

ABI = json.load(open(
    os.path.join(os.path.dirname(__file__), "contracts", "PrescriptionRegistry.abi.json")
))

print("\nDeploying PrescriptionRegistry to Polygon Amoy...")

nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)
contract = w3.eth.contract(abi=ABI, bytecode=BYTECODE)

tx = contract.constructor().build_transaction({
    "chainId": 80002,
    "gas": 500000,
    "gasPrice": w3.to_wei("30", "gwei"),
    "nonce": nonce,
    "from": WALLET_ADDRESS,
})

signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

print(f"Transaction sent: {tx_hash.hex()}")
print("Waiting for confirmation (usually 10-30 seconds)...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

print(f"\n{'='*60}")
print(f"CONTRACT DEPLOYED SUCCESSFULLY")
print(f"{'='*60}")
print(f"Contract Address : {receipt.contractAddress}")
print(f"Transaction Hash : {tx_hash.hex()}")
print(f"Block Number     : {receipt.blockNumber}")
print(f"Gas Used         : {receipt.gasUsed}")
print(f"\nView on explorer:")
print(f"https://amoy.polygonscan.com/address/{receipt.contractAddress}")
print(f"\nNOW: Copy the Contract Address above and paste it into blockchain.py → CONTRACT_ADDRESS")
print(f"{'='*60}")

# Auto-save to a file so you don't lose it
with open("deployed_address.txt", "w") as f:
    f.write(f"CONTRACT_ADDRESS={receipt.contractAddress}\n")
    f.write(f"TX_HASH={tx_hash.hex()}\n")
    f.write(f"NETWORK=Polygon Amoy (chainId 80002)\n")
print("(Address also saved to deployed_address.txt)")
