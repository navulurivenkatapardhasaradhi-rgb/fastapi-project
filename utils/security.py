from datetime import datetime, timedelta, timezone
import secrets

from fastapi import Depends, HTTPException,status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from jose import jwt, JWTError

from passlib.context import CryptContext

from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db

from models.users import User


ALGORITHM = "HS256"
SECRET_KEY = settings.SECRET_KEY
EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


security = HTTPBearer()


limiter = Limiter(
    key_func=get_remote_address
)


# =========================================
# PASSWORD HASHING
# =========================================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# =========================================
# VERIFY PASSWORD
# =========================================
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# =========================================
# HASH TEXT
# =========================================
def hash_text(text: str) -> str:
    return pwd_context.hash(text)


# =========================================
# VERIFY TEXT
# =========================================
def verify_text(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# =========================================
# GENERATE OTP
# =========================================
def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


# =========================================
# CREATE ACCESS TOKEN
# =========================================
def create_access_token(
    user_id: int,
    email: str,
    role: str
):

    jti = secrets.token_urlsafe(16)

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "jti": jti,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token, jti, expire


# =========================================
# DECODE TOKEN
# =========================================
def decode_token(token: str):
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )


# =========================================
# CURRENT USER
# =========================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):

    token = credentials.credentials

    try:
        payload = decode_token(token)

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# =========================================
# ADMIN ONLY
# =========================================
async def admin_only(current_user: User = Depends(get_current_user)):
     # 👈 add this line (debug)

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins only"
        )
    
    return current_user

# =========================================
# USER OR ADMIN
# =========================================
async def user_or_admin(
    current_user: User = Depends(get_current_user)
):
    return current_user