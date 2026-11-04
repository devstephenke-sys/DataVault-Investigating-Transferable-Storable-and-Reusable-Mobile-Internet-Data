"""
DataVault Device Simulator
Simulates a physical DataVault device with token storage and usage tracking
"""
from flask import Flask, request, jsonify
import sqlite3
import datetime
import uuid
import json
import os
import requests
from typing import Optional

app = Flask(__name__)

# Configuration
DATAVAULT_BACKEND_URL = os.getenv("DATAVAULT_BACKEND_URL", "http://localhost:8000")
DEVICE_ID = os.getenv("DEVICE_ID", "DV-001-ABCD")
TOKEN_DB_PATH = "tokens.db"

# Initialize token storage database
def init_token_db():
    conn = sqlite3.connect(TOKEN_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            entitlement_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            device_id TEXT NOT NULL,
            allocated_volume INTEGER NOT NULL,
            remaining_volume INTEGER NOT NULL,
            issued_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE'
        )
    ''')
    conn.commit()
    conn.close()

# Initialize on startup
init_token_db()

class TokenStorage:
    """Local token storage for the device"""

    @staticmethod
    def store_token(entitlement_data: dict) -> bool:
        """Store an entitlement token locally"""
        conn = sqlite3.connect(TOKEN_DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO tokens
                (entitlement_id, token, device_id, allocated_volume, remaining_volume, issued_at, expires_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entitlement_data['entitlement_id'],
                entitlement_data['token'],
                entitlement_data['destination_device_id'],
                entitlement_data['allocated_volume'],
                entitlement_data['remaining_volume'],
                entitlement_data['issued_at'],
                entitlement_data['expires_at'],
                entitlement_data['status']
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def load_token(entitlement_id: str) -> Optional[dict]:
        """Load a token from local storage"""
        conn = sqlite3.connect(TOKEN_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tokens WHERE entitlement_id = ?', (entitlement_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'entitlement_id': row[0],
                'token': row[1],
                'device_id': row[2],
                'allocated_volume': row[3],
                'remaining_volume': row[4],
                'issued_at': row[5],
                'expires_at': row[6],
                'status': row[7]
            }
        return None

    @staticmethod
    def update_remaining_volume(entitlement_id: str, new_volume: int) -> bool:
        """Update remaining volume after usage"""
        conn = sqlite3.connect(TOKEN_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tokens SET remaining_volume = ?, status = ?
            WHERE entitlement_id = ?
        ''', (new_volume, 'PARTIALLY_CONSUMED' if new_volume > 0 else 'EXHAUSTED', entitlement_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def list_tokens() -> list:
        """List all stored tokens"""
        conn = sqlite3.connect(TOKEN_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tokens')
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'entitlement_id': row[0],
                'token': row[1],
                'device_id': row[2],
                'allocated_volume': row[3],
                'remaining_volume': row[4],
                'issued_at': row[5],
                'expires_at': row[6],
                'status': row[7]
            }
            for row in rows
        ]

# API Endpoints
@app.route('/device/status', methods=['GET'])
def device_status():
    """Get device status"""
    return jsonify({
        'device_id': DEVICE_ID,
        'status': 'online',
        'uptime': 3600,  # Mock uptime
        'connected': True
    })

@app.route('/device/token/store', methods=['POST'])
def store_token():
    """Store an entitlement token"""
    data = request.json

    if not data or 'entitlement_id' not in data or 'token' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    success = TokenStorage.store_token(data)

    if success:
        return jsonify({'status': 'stored', 'entitlement_id': data['entitlement_id']}), 201
    else:
        return jsonify({'error': 'Token already exists or storage failed'}), 409

@app.route('/device/token/<entitlement_id>', methods=['GET'])
def get_token(entitlement_id):
    """Retrieve a stored token"""
    token = TokenStorage.load_token(entitlement_id)

    if token:
        return jsonify(token), 200
    else:
        return jsonify({'error': 'Token not found'}), 404

@app.route('/device/tokens', methods=['GET'])
def list_tokens():
    """List all stored tokens"""
    tokens = TokenStorage.list_tokens()
    return jsonify({'tokens': tokens}), 200

@app.route('/device/validate', methods=['POST'])
def validate_token():
    """Validate a token with the backend"""
    data = request.json

    if not data or 'entitlement_id' not in data or 'token' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Call backend validation API
    try:
        response = requests.post(
            f"{DATAVAULT_BACKEND_URL}/api/v1/entitlement/validate",
            json=data,
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/device/report-usage', methods=['POST'])
def report_usage():
    """Report usage to backend"""
    data = request.json

    if not data or 'entitlement_id' not in data or 'volume_consumed' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Update local cache
    entitlement_id = data['entitlement_id']
    volume_consumed = data['volume_consumed']

    token = TokenStorage.load_token(entitlement_id)
    if token:
        new_remaining = token['remaining_volume'] - volume_consumed
        TokenStorage.update_remaining_volume(entitlement_id, new_remaining)

    # Call backend reporting API
    try:
        response = requests.post(
            f"{DATAVAULT_BACKEND_URL}/api/v1/entitlement/report-usage",
            json=data,
            timeout=10
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/device/simulate-traffic', methods=['POST'])
def simulate_traffic():
    """Simulate network traffic through the device"""
    data = request.json
    entitlement_id = data.get('entitlement_id')
    volume_bytes = data.get('volume_bytes', 1073741824)  # Default 1 GB

    if not entitlement_id:
        return jsonify({'error': 'entitlement_id required'}), 400

    # Load token
    token = TokenStorage.load_token(entitlement_id)
    if not token:
        return jsonify({'error': 'Token not found'}), 404

    if token['remaining_volume'] < volume_bytes:
        return jsonify({'error': 'Insufficient quota'}), 400

    # Simulate traffic (in real implementation, this would be actual network traffic)
    # For simulation, we just report usage
    session_id = str(uuid.uuid4())
    report_data = {
        'entitlement_id': entitlement_id,
        'device_id': DEVICE_ID,
        'volume_consumed': volume_bytes,
        'session_id': session_id,
        'reported_at': datetime.datetime.utcnow().isoformat()
    }

    # Report usage
    try:
        response = requests.post(
            f"{DATAVAULT_BACKEND_URL}/api/v1/entitlement/report-usage",
            json=report_data,
            timeout=10
        )
        return jsonify({
            'status': 'traffic_simulated',
            'volume_consumed': volume_bytes,
            'session_id': session_id,
            'report_result': response.json()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/device/restart', methods=['POST'])
def simulate_restart():
    """Simulate device restart to test persistence"""
    # In a real device, this would trigger a reboot
    # For simulation, we just confirm tokens persist
    tokens = TokenStorage.list_tokens()
    return jsonify({
        'status': 'restart_simulated',
        'tokens_persisted': len(tokens),
        'tokens': tokens
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({'status': 'healthy', 'device_id': DEVICE_ID})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
