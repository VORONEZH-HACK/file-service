from uuid import UUID
from typing import Optional
from sqlmodel import SQLModel, Field


class File(SQLModel, table=True):
    __table_args__ = ({"schema": "fsp"})
    id: Optional[UUID] = Field(default=None, primary_key=True)
    name: str
    type: str
    user_id: UUID
