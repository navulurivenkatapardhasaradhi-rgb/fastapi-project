from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.tasks import Task
from models.users import User

from schemas.task import TaskCreate, TaskUpdate

from core.database import get_db
from utils.security import get_current_user, admin_only

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ✅ GET ALL TASKS
@router.get("/")
async def get_all(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(Task.user_id == user.id)
    )
    return result.scalars().all()


# ✅ GET ONE TASK
@router.get("/{id}")
async def get_one(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task).where(Task.id == id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    if obj.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return obj


# ✅ CREATE TASK
@router.post("/")
async def create(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    try:
        new = Task(**task.dict(), user_id=current_user.id)
        db.add(new)
        await db.commit()
        await db.refresh(new)
        return new
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ REPLACE TASK (PUT)
@router.put("/{id}")
async def replace(
    id: int,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    result = await db.execute(
        select(Task).where(Task.id == id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    if obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    obj.title = task.title
    obj.due_date = task.due_date

    try:
        await db.commit()
        await db.refresh(obj)
        return obj
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ PATCH UPDATE TASK
@router.patch("/{id}")
async def update(
    id: int,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    result = await db.execute(
        select(Task).where(Task.id == id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    if obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if task.status is not None:
        obj.status = task.status

    if task.priority is not None:
        obj.priority = task.priority

    try:
        await db.commit()
        await db.refresh(obj)
        return obj
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ✅ DELETE TASK
@router.delete("/{id}")
async def delete(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        admin_only
    )
):
    result = await db.execute(
        select(Task).where(Task.id == id)
    )
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(status_code=404, detail="Task not found")

    if obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        await db.delete(obj)
        await db.commit()
        return {"message": "deleted"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))