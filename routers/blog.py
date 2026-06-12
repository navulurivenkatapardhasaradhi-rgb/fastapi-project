from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.blogs import Blog
from schemas.blog import BlogCreate
from utils.security import get_db, get_current_user,admin_only
from models.users import User
router = APIRouter(prefix="/blogs", tags=["Blogs"])
@router.post("/")
async def create(
    blog: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    try:
        new = Blog(**blog.dict(), user_id=current_user.id)
        db.add(new)
        await db.commit()
        await db.refresh(new)
        return new
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_all(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog))
    return result.scalars().all()
@router.put("/{id}")
async def update(
    id: int,
    blog: BlogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    result = await db.execute(select(Blog).where(Blog.id == id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Blog not found")
    if obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    obj.title = blog.title
    obj.content = blog.content
    try:
        await db.commit()
        await db.refresh(obj)
        return obj
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/{id}")
async def delete(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    result = await db.execute(select(Blog).where(Blog.id == id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Blog not found")
    if obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    try:
        await db.delete(obj)
        await db.commit()
        return {"message": "deleted"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))