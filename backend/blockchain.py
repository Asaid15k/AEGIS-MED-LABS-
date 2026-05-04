from dotenv import load_dotenv
load_dotenv()
"""
AEGISMEDLABS - blockchain.py
────────────────────────────
Uses Polygon Amoy testnet via Alchemy.
No Hardhat. No local node. No npx. Works on ANY device.

Setup (one-time, 5 minutes):
  1. Go to https://alchemy.com  → create free account
     → Create App → Chain: Polygon → Network: Amoy
     → Copy the HTTPS URL  → paste as ALCHEMY_URL below

  2. Create a wallet at https://metamask.io
     → Settings → Advanced → Show test networks: ON
     → Switch to "Polygon Amoy"
     → Copy your wallet address  → paste as WALLET_ADDRESS below
     → Export private key        → paste as PRIVATE_KEY below

  3. Get free MATIC gas:
     → Go to https://faucet.polygon.technology
     → Paste your wallet address → request test MATIC (takes ~30 sec)

  4. Run deploy_contract.py ONCE to deploy to Amoy
     → Copy the printed contract address → paste as CONTRACT_ADDRESS below

  5. Done. Never run Hardhat again.
"""

from web3 import Web3
import os
import json

# ─────────────────────────────────────────────
#  FILL THESE IN (see setup steps above)
# ─────────────────────────────────────────────
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

ALCHEMY_URL      = os.getenv("ALCHEMY_URL")
PRIVATE_KEY      = os.getenv("PRIVATE_KEY")
WALLET_ADDRESS   = os.getenv("WALLET_ADDRESS")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

# ABI is stored locally in your project — no absolute path needed
ABI_PATH = os.path.join(os.path.dirname(__file__), "contracts", "PrescriptionRegistry.abi.json")

with open(ABI_PATH) as f:
    ABI = json.load(f)

# Connect to Polygon Amoy via Alchemy
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

if not w3.is_connected():
    print("[BLOCKCHAIN] Warning: Cannot connect to Alchemy — running in offline mode")
    # Don't crash the whole app if blockchain is unreachable

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=ABI
)


def store_hash(prescription_id: int, data_hash: bytes) -> str:
    """
    Store a prescription hash on Polygon Amoy blockchain.
    Called automatically when a prescription is created.
    Returns the transaction hash as a string.
    """
    # Convert hex string to bytes32 if needed
    if isinstance(data_hash, str):
        data_hash = bytes.fromhex(data_hash)

    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    # Build the transaction (no local node needed — signs with private key)
    tx = contract.functions.storePrescription(
        prescription_id,
        data_hash
    ).build_transaction({
        "chainId": 80002,           # Polygon Amoy chain ID
        "gas": 100000,
        "gasPrice": w3.to_wei("30", "gwei"),
        "nonce": nonce,
        "from": WALLET_ADDRESS,
    })

    # Sign with private key (works on any machine — no Hardhat accounts needed)
    signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    print(f"[BLOCKCHAIN] Stored prescription #{prescription_id} | TX: {tx_hash.hex()}")
    return tx_hash.hex()


def get_hash(prescription_id: int) -> str:
    """
    Retrieve the stored hash for a prescription from the blockchain.
    This is a read call — free, instant, no gas needed.
    """
    result = contract.functions.getHash(prescription_id).call()
    return result.hex()


def verify_on_chain(prescription_id: int, expected_hash: str) -> bool:
    try:
        on_chain = get_hash(prescription_id)
        expected = expected_hash.lstrip("0x").lower()
        on_chain_clean = on_chain.lstrip("0x").lower()
        # If nothing stored yet, return True (don't block)
        if on_chain_clean == "0" * 64:
            return True
        return on_chain_clean == expected
    except Exception as e:
        print(f"[BLOCKCHAIN] verify error: {e}")
        return True
