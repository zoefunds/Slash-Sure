"""Helpers to retrieve a user's wallet private key for signing GenLayer transactions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.core.security import decrypt_with_master


async def get_user_private_key(user_id: str, db: AsyncSession) -> str | None:
    """Return the user's plaintext private key decrypted with the master key.
    Returns None if no master-encrypted copy exists (pre-migration wallets).
    """
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet or not wallet.master_encrypted_private_key:
        return None
    return decrypt_with_master(wallet.master_encrypted_private_key, wallet.master_encryption_nonce)
