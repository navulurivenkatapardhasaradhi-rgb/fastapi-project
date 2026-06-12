from sqlalchemy import (
    String,
    Integer,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from core.database import Base
class Blog(Base):
    __tablename__ = "blogs"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    title: Mapped[str] = mapped_column(
        String(255)
    )
    content: Mapped[str] = mapped_column(
        String(255)
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )
    user = relationship(
        "User",
        back_populates="blogs"
    )