from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.users import RevokedToken
from utils.security import decode_token
PUBLIC_PATHS = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/users/register",
    "/users/login",
    "/users/verify-otp",
    "/users/resend-otp",
    "/users/forgot-password",
    "/users/reset-password"
]
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header missing"}
            )
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token type"}
            )
        token = auth_header.split(" ")[1]
        try:
            payload = decode_token(token)
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token"}
            )
        jti = payload.get("jti")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RevokedToken).where(
                    RevokedToken.jti == jti
                )
            )
            revoked = result.scalar_one_or_none()
            if revoked:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token revoked"}
                )
        request.state.user = payload
        return await call_next(request)