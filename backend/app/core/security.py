import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from eth_account import Account
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Account.enable_unaudited_hdwallet_features()


# ─── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(subject: str, extra: dict = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire, "type": "access", **(extra or {})}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# ─── Wallet Generation ─────────────────────────────────────────────────────────

def generate_wallet() -> dict:
    """Generate a new Ethereum-compatible wallet."""
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex(),
    }


def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from user password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return kdf.derive(password.encode())


def encrypt_private_key(private_key: str, password: str) -> dict:
    """Encrypt wallet private key using password-derived AES-GCM key."""
    salt = os.urandom(16)
    key = derive_key_from_password(password, salt)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, private_key.encode(), None)
    return {
        "encrypted_key": ciphertext.hex(),
        "salt": salt.hex(),
        "nonce": nonce.hex(),
    }


def decrypt_private_key(encrypted_key: str, salt: str, nonce: str, password: str) -> str:
    """Decrypt wallet private key using password-derived AES-GCM key."""
    key = derive_key_from_password(password, bytes.fromhex(salt))
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(bytes.fromhex(nonce), bytes.fromhex(encrypted_key), None)
    return plaintext.decode()


_MASTER_SALT = b"slashsure-wallet-v1-master-salt-"  # fixed 32-byte salt


def encrypt_with_master(private_key: str) -> dict:
    """Encrypt a wallet private key with the server WALLET_MASTER_KEY."""
    key = derive_key_from_password(settings.WALLET_MASTER_KEY, _MASTER_SALT)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, private_key.encode(), None)
    return {"encrypted_key": ciphertext.hex(), "nonce": nonce.hex()}


def decrypt_with_master(encrypted_key: str, nonce: str) -> str:
    """Decrypt a wallet private key using the server WALLET_MASTER_KEY."""
    key = derive_key_from_password(settings.WALLET_MASTER_KEY, _MASTER_SALT)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(bytes.fromhex(nonce), bytes.fromhex(encrypted_key), None)
    return plaintext.decode()


# ─── Webhook Signature ─────────────────────────────────────────────────────────

def sign_webhook_payload(payload: str) -> str:
    return hmac.new(
        settings.WEBHOOK_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(payload: str, signature: str) -> bool:
    expected = sign_webhook_payload(payload)
    return hmac.compare_digest(expected, signature)


# ─── Misc ──────────────────────────────────────────────────────────────────────

def generate_api_key() -> str:
    return f"ss_{secrets.token_urlsafe(40)}"


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()
