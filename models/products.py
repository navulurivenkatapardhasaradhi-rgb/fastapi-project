from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime
)
from core.database import Base
class Product(Base):
    __tablename__ = "products"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    name = Column(
        String,
        nullable=False
    )
    description = Column(
        String,
        nullable=False
    )
    price = Column(
        Float,
        nullable=False
    )
    stock = Column(
        Integer,
        default=0
    )
    category = Column(
        String,
        nullable=False
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)