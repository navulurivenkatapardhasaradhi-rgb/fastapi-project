from typing import Optional
from datetime import datetime
from pydantic import BaseModel
class TaskCreate(BaseModel):
    title: str
    due_date: datetime
    status: Optional[str] = None
class TaskUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None