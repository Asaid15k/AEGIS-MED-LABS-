import qrcode
import hashlib
import json
import base64
from io import BytesIO
from blockchain import store_hash, get_hash

def compute_hash(prescription_data):
    data_str = json.dumps(prescription_data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

def generate_qr(prescription_data):
    data_hash = compute_hash(prescription_data)
    store_hash(prescription_data["prescription_id"], data_hash)
    
    qr = qrcode.make(json.dumps({
        "prescription_id": prescription_data["prescription_id"],
        "hash": data_hash
    }))
    
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

def verify_qr(prescription_id, data_hash):
    stored_hash = get_hash(prescription_id)
    return stored_hash == data_hash