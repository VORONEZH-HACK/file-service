from uuid import uuid4
from typing import Optional
from sqlmodel import SQLModel, Field


class File(SQLModel, table=True):
    id: Optional[uuid4] = Field(default=None, primary_key=True)
    name: str
    type: str
    user_id: uuid4 = Field(foreign_key="users.id")

