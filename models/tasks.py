from sqlalchemy import Column, Float, String, Integer, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base
from models.users import User
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="pending")

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # ✅ MATCH THIS
    user: Mapped["User"] = relationship("User", back_populates="tasks")