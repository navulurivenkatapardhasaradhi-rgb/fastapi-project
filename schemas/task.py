from datetime import datetime
from alembic.environment import Optional
from pydantic import BaseModel, EmailStr, Field
class TaskCreate(BaseModel):
    title: str
    due_date: datetime

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None