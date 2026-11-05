import base64
import json
import time
from datetime import timedelta
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

security = HTTPBearer(auto_error=False)


def _get_encryption_key_and_iv():
    """Extract and validate 32-byte key and 16-byte IV for AES-256-CBC."""
    raw_key = getattr(settings, "ENCRYPTION_FIXED_KEY", "0123456789abcdef0123456789abcdef")
    raw_iv = getattr(settings, "ENCRYPTION_FIXED_IV", "abcdef9876543210")

    # Key: 32 bytes (256 bits)
    if len(raw_key) == 64:
        try:
            key = bytes.fromhex(raw_key)
        except ValueError:
            key = raw_key.encode("utf-8")[:32].ljust(32, b"\0")
    else:
        key = raw_key.encode("utf-8")[:32].ljust(32, b"\0")

    # IV: 16 bytes (128 bits block size)
    if len(raw_iv) == 32:
        try:
            iv = bytes.fromhex(raw_iv)
        except ValueError:
            iv = raw_iv.encode("utf-8")[:16].ljust(16, b"\0")
    else:
        iv = raw_iv.encode("utf-8")[:16].ljust(16, b"\0")

    return key, iv


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generate an AES-256-CBC encrypted token valid for 7 days (or custom expires_delta).
    """
    to_encode = data.copy()
    if expires_delta:
        expire_seconds = int(expires_delta.total_seconds())
    else:
        expire_days = getattr(settings, "TOKEN_EXPIRE_DAYS", 7)
        expire_seconds = expire_days * 86400

    exp_timestamp = int(time.time()) + expire_seconds
    to_encode["exp"] = exp_timestamp

    raw_bytes = json.dumps(to_encode, separators=(",", ":")).encode("utf-8")

    # PKCS7 padding to 128-bit block size
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(raw_bytes) + padder.finalize()

    key, iv = _get_encryption_key_and_iv()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # Hex-encoded token string
    return ciphertext.hex()


def decode_access_token(token: str) -> dict:
    """
    Decode and validate an AES-256-CBC encrypted token.
    Validates token expiration (7 days).
    """
    try:
        try:
            ciphertext = bytes.fromhex(token)
        except ValueError:
            ciphertext = base64.urlsafe_b64decode(token)

        key, iv = _get_encryption_key_and_iv()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        raw_bytes = unpadder.update(padded_data) + unpadder.finalize()
        payload = json.loads(raw_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp is not None:
            if time.time() > float(exp):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
