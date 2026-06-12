from typing import Optional
from pydantic import BaseModel, EmailStr
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "user"
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str
class ResendOtpRequest(BaseModel):
    email: EmailStr
class ForgotPasswordRequest(BaseModel):
    email: EmailStr
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
class MessageResponse(BaseModel):
    message: str