from sqlalchemy import String, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50),
        default="user"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )
    otp_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    otp_expires_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    reset_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )
    reset_expires_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    blogs = relationship(
        "Blog",
        back_populates="user",
        cascade="all, delete"
    )
    tasks = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete"
    )
class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    jti: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False
    )
    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )