"""
Module: auth.py
Handles user authentication, password hashing using PBKDF2-HMAC-SHA256, and session tokens.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional, Tuple


def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2 with HMAC-SHA256 and a random 16-byte salt.
    Complies with OWASP Password Storage Guidelines.
    Format: salt$hash
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(stored_hash: str, provided_password: str) -> bool:
    """
    Verifies a password against the stored salt$hash using constant-time comparison.
    Mitigates timing attacks (CWE-208).
    """
    try:
        salt_hex, key_hex = stored_hash.split('$')
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(expected_key, actual_key)
    except (ValueError, AttributeError):
        return False


def generate_auth_token(username: str, secret_key: str) -> str:
    """
    Generates an authenticated token signed with HMAC-SHA256.
    """
    nonce = secrets.token_hex(16)
    payload = f"{username}:{nonce}"
    signature = hmac.new(secret_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"


def verify_auth_token(token: str, secret_key: str) -> Optional[str]:
    """
    Verifies token signature using constant-time comparison. Returns username if valid.
    """
    try:
        parts = token.split(':')
        if len(parts) != 3:
            return None
        username, nonce, signature = parts
        payload = f"{username}:{nonce}"
        expected_signature = hmac.new(secret_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected_signature, signature):
            return username
        return None
    except (ValueError, AttributeError):
        return None
