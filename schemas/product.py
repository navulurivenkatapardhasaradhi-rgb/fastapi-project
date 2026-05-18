from pydantic import BaseModel, Field
from typing import Optional


# =========================================================
# CREATE PRODUCT
# =========================================================
class ProductCreate(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    category: str


# =========================================================
# UPDATE PRODUCT
# =========================================================
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(
        default=None,
        gt=0
    )
    stock: Optional[int] = Field(
        default=None,
        ge=0
    )
    category: Optional[str] = None


# =========================================================
# PRODUCT RESPONSE
# =========================================================
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    category: str

    class Config:
        from_attributes = True


# =========================================================
# PRODUCT LIST RESPONSE
# =========================================================
class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: list[ProductResponse]


# =========================================================
# MESSAGE RESPONSE
# =========================================================
class MessageResponse(BaseModel):
    message: str