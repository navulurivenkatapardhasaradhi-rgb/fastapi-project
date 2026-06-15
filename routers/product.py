from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status
)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db

from models.products import Product
from models.users import User

from schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    MessageResponse
)

from utils.security import (
    get_current_user,
    admin_only
)



router = APIRouter(
    prefix="/products",
    tags=["Products"]
)
# CREATE PRODUCT (ADMIN ONLY)
@router.post("/",response_model=ProductResponse,status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only)
):

    existing = await db.execute(
        select(Product).where(
            Product.name == payload.name
        )
    )

    existing_product = existing.scalar_one_or_none()

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product already exists"
        )
    new_product = Product(
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock=payload.stock,
        category=payload.category,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(new_product)

    await db.commit()
    await db.refresh(new_product)

    return new_product


# GET ALL PRODUCTS
@router.get("/",response_model=ProductListResponse)
async def get_products(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None
):

    query = select(Product)

    count_query = select(func.count()).select_from(Product)

    # FILTER NAME
    if name:
        query = query.where(
            Product.name.ilike(f"%{name}%")
        )

        count_query = count_query.where(
            Product.name.ilike(f"%{name}%")
        )

    # FILTER CATEGORY
    if category:
        query = query.where(
            Product.category == category
        )

        count_query = count_query.where(
            Product.category == category
        )

    # FILTER MIN PRICE
    if min_price is not None:
        query = query.where(
            Product.price >= min_price
        )

        count_query = count_query.where(
            Product.price >= min_price
        )

    # FILTER MAX PRICE
    if max_price is not None:
        query = query.where(
            Product.price <= max_price
        )

        count_query = count_query.where(
            Product.price <= max_price
        )

    total_result = await db.execute(count_query)

    total = total_result.scalar()

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)

    products = result.scalars().all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": products
    }

# GET PRODUCT BY ID
@router.get(
    "/{id}",
    response_model=ProductResponse
)
async def get_product(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only)
):

    result = await db.execute(
        select(Product).where(
            Product.id == id
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# UPDATE PRODUCT (ADMIN ONLY)
@router.put("/{id}",response_model=ProductResponse)
async def update_product(
    id: int,
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only)
):

    result = await db.execute(
        select(Product).where(
            Product.id == id
        )
    )

    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db_product.name = payload.name
    db_product.description = payload.description
    db_product.price = payload.price
    db_product.stock = payload.stock
    db_product.category = payload.category
    db_product.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_product)

    return db_product
# PATCH PRODUCT (ADMIN ONLY)
@router.patch("/{id}",response_model=ProductResponse)
async def patch_product(
    id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only)
):

    result = await db.execute(
        select(Product).where(
            Product.id == id
        )
    )

    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if payload.name is not None:
        db_product.name = payload.name

    if payload.description is not None:
        db_product.description = payload.description

    if payload.price is not None:
        db_product.price = payload.price

    if payload.stock is not None:
        db_product.stock = payload.stock

    if payload.category is not None:
        db_product.category = payload.category

    db_product.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_product)

    return db_product


# DELETE PRODUCT (ADMIN ONLY)
@router.delete("/{id}",response_model=MessageResponse)
async def delete_product(
    id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(admin_only)
):

    result = await db.execute(
        select(Product).where(
            Product.id == id
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    await db.delete(product)

    await db.commit()

    return {
        "message": "Product deleted successfully"
    }