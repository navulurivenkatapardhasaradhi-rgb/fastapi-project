from datetime import datetime, timedelta, timezone
from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    HTTPException,
    Request
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.config import settings
from models.users import User, RevokedToken
from schemas.user_schema import (
    RegisterRequest,
    VerifyOtpRequest,
    ResendOtpRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    MessageResponse,
    UserUpdate
)
from utils.security import (
    hash_password,
    verify_password,
    hash_text,
    verify_text,
    generate_otp,
    create_access_token
)
from utils.emailer import (
    send_email,
    build_otp_body,
    build_reset_body
)
from utils.security import (
    get_current_user,
    admin_only
)
from utils.security import limiter
router = APIRouter(prefix="/users", tags=["Users"])
@router.post("/register", response_model=MessageResponse)
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )
    otp = generate_otp()
    new_user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role.lower(),
        is_verified=False,
        otp_hash=hash_text(otp),
        otp_expires_at=datetime.now(timezone.utc)
        + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
    )
    db.add(new_user)
    await db.commit()
    background_tasks.add_task(
        send_email,
        payload.email.lower(),
        "Verify your email",
        build_otp_body(payload.name, otp),
    )
    return {
        "message": "Registered successfully. OTP sent to email."
    }
@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(
    payload: VerifyOtpRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if user.is_verified:
        return {
            "message": "Email already verified"
        }
    if not user.otp_hash or not user.otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP not available"
        )
    if datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="OTP expired"
        )
    if not verify_text(payload.otp, user.otp_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    user.is_verified = True
    user.otp_hash = None
    user.otp_expires_at = None
    await db.commit()
    return {
        "message": "Email verified successfully"
    }
@router.post("/resend-otp", response_model=MessageResponse)
async def resend_otp(
    payload: ResendOtpRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email already verified"
        )
    otp = generate_otp()
    user.otp_hash = hash_text(otp)
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.OTP_EXPIRE_MINUTES
    )
    await db.commit()
    background_tasks.add_task(
        send_email,
        user.email.lower(),
        "Your new verification OTP",
        build_otp_body(user.name, otp),
    )
    return {
        "message": "OTP resent successfully"
    }
@router.post("/login", response_model=TokenResponse)
@limiter.limit("3/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email"
        )
    if not verify_password(
        payload.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Verify email first"
        )
    token, _, _ = create_access_token(
        user.id,
        user.email,
        user.role
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }
@router.get("/profile")
async def profile(
    current_user: User = Depends(admin_only)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_verified": current_user.is_verified
    }
# GET ALL USERS 
@router.get("/")
async def get_users(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User))
    return result.scalars().all()
# GET USER BY ID
@router.get("/{id}")
async def get_user(
    id: int,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == id)
    )    
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user
@router.patch("/{id}")
async def update_user(
    id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(User).where(User.id == id)
    )
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if current_user.id != id and current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    if payload.email:
        existing = await db.execute(
            select(User).where(User.email.lower() == payload.email.lower())
        )
        existing_user = existing.scalar_one_or_none()
        if existing_user and existing_user.id != id:
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )
        db_user.email = payload.email.lower()
    if payload.password:
        db_user.hashed_password = hash_password(
            payload.password
        )
    if payload.role and current_user.role == "admin":
        db_user.role = payload.role.lower()
    await db.commit()
    await db.refresh(db_user)
    return db_user
@router.delete("/{id}")
async def delete_user(
    id: int,
    admin: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    await db.delete(user)
    await db.commit()
    return {
        "message": "User deleted successfully"
    }
@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    otp = generate_otp()
    user.reset_hash = hash_text(otp)
    user.reset_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
    )
    await db.commit()
    background_tasks.add_task(
        send_email,
        user.email.lower(),
        "Password reset OTP",
        build_reset_body(user.name, otp),
    )
    return {
        "message": "Password reset OTP sent to email"
    }
@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email.lower() == payload.email.lower())
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if not user.reset_hash or not user.reset_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Reset OTP not available"
        )
    if datetime.now(timezone.utc) > user.reset_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Reset OTP expired"
        )
    if not verify_text(payload.otp, user.reset_hash):
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    user.hashed_password = hash_password(
        payload.new_password
    )
    user.reset_hash = None
    user.reset_expires_at = None
    await db.commit()
    return {
        "message": "Password reset successfully"
    }
@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    payload = getattr(request.state, "token_payload", None)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        raise HTTPException(
            status_code=400,
            detail="Invalid token"
        )
    expires_at = datetime.fromtimestamp(
        exp,
        tz=timezone.utc
    )
    db.add(
        RevokedToken(
            jti=jti,
            expires_at=expires_at
        )
    )
    await db.commit()
    return {
        "message": "Logged out successfully"
    }