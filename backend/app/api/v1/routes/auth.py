import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
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
from app.services.notifications.email import (
    send_verification_email,
    send_welcome_email,
    send_forgot_password_email,
    send_password_changed_email,
)
from app.middleware.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
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


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    verification_token = secrets.token_urlsafe(48)
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_verified=False,
        email_verification_token=verification_token,
        email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(user)
    await db.flush()

    # Wallet
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

    # Personal org
    org = Organization(
        name=f"{body.full_name or body.email}'s Workspace",
        slug=f"personal-{str(user.id)[:8]}",
    )
    db.add(org)
    await db.flush()
    db.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=OrgRole.OWNER))
    await db.flush()

    await log_action(db, str(user.id), None, "user_registered", "user", str(user.id),
                     request.client.host if request.client else None)
    await db.commit()

    # Send verification email (non-blocking)
    await send_verification_email(user.email, user.full_name or "", verification_token)

    return RegisterResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        email=user.email,
        wallet_address=wallet.address,
        message="Account created. Please check your email to verify your address.",
    )


# ── Verify Email ──────────────────────────────────────────────────────────────

class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email_verification_token == body.token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid verification token")
    if user.email_verification_expires and user.email_verification_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification token expired")
    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token = None
    user.email_verification_expires = None
    await db.commit()

    await send_welcome_email(user.email, user.full_name or "")
    return {"message": "Email verified successfully. Welcome to SlashSure!"}


# ── Resend Verification ───────────────────────────────────────────────────────

class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    # Always return 200 to prevent email enumeration
    if not user or user.is_verified:
        return {"message": "If that email exists and is unverified, a new link has been sent."}

    token = secrets.token_urlsafe(48)
    user.email_verification_token = token
    user.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.commit()

    await send_verification_email(user.email, user.full_name or "", token)
    return {"message": "If that email exists and is unverified, a new link has been sent."}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
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
    await db.commit()

    return LoginResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        user_id=str(user.id),
        email=user.email,
        wallet_address=wallet.address if wallet else None,
        is_verified=user.is_verified,
    )


# ── Forgot Password ───────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()
    # Always return 200 to prevent enumeration
    if not user or not user.is_active:
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(48)
    user.password_reset_token = token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    await send_forgot_password_email(user.email, user.full_name or "", token)
    return {"message": "If that email is registered, a reset link has been sent."}


# ── Reset Password ────────────────────────────────────────────────────────────

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    result = await db.execute(
        select(User).where(User.password_reset_token == body.token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if user.password_reset_expires and user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user.hashed_password = hash_password(body.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()

    await send_password_changed_email(user.email, user.full_name or "")
    return {"message": "Password reset successfully. You can now log in."}


# ── Refresh Token ─────────────────────────────────────────────────────────────

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


# ── Export Wallet Key ─────────────────────────────────────────────────────────

@router.post("/export-key", response_model=ExportKeyResponse)
async def export_private_key(
    body: ExportKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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


# ── Me ────────────────────────────────────────────────────────────────────────

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }


class UpdateProfileBody(BaseModel):
    full_name: Optional[str] = None


@router.patch("/me")
async def update_me(
    body: UpdateProfileBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at,
    }
