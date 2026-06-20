from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decrypt_private_key,
    encrypt_private_key,
    generate_wallet,
    hash_password,
    verify_password,
    decode_token,
)
from app.db.base import get_db
from app.models.user import Organization, OrganizationMember, OrgRole, User
from app.models.wallet import Wallet
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshRequest,
    RefreshResponse,
    ExportKeyRequest,
    ExportKeyResponse,
)
from app.services.notifications.email import send_welcome_email
from app.middleware.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Check email uniqueness
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    # Generate wallet and encrypt with password
    wallet_data = generate_wallet()
    encrypted = encrypt_private_key(wallet_data["private_key"], body.password)
    wallet = Wallet(
        user_id=user.id,
        address=wallet_data["address"],
        encrypted_private_key=encrypted["encrypted_key"],
        encryption_salt=encrypted["salt"],
        encryption_nonce=encrypted["nonce"],
    )
    db.add(wallet)

    # Create personal organization
    org = Organization(
        name=f"{body.full_name or body.email}'s Workspace",
        slug=f"personal-{str(user.id)[:8]}",
    )
    db.add(org)
    await db.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db.add(member)
    await db.flush()

    await send_welcome_email(user.email, user.full_name or "")
    await log_action(db, str(user.id), None, "user_registered", "user", str(user.id),
                     request.client.host if request.client else None)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=str(user.id),
        email=user.email,
        wallet_address=wallet.address,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login_at = datetime.now(timezone.utc)

    wallet_result = await db.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = wallet_result.scalar_one_or_none()

    await log_action(db, str(user.id), None, "user_login", "user", str(user.id),
                     request.client.host if request.client else None)

    return LoginResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        email=user.email,
        wallet_address=wallet.address if wallet else None,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return RefreshResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/export-key", response_model=ExportKeyResponse)
async def export_private_key(
    body: ExportKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export wallet private key — requires password confirmation."""
    if not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=403, detail="Invalid password")

    result = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    private_key = decrypt_private_key(
        wallet.encrypted_private_key,
        wallet.encryption_salt,
        wallet.encryption_nonce,
        body.password,
    )
    return ExportKeyResponse(private_key=private_key, address=wallet.address)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }
