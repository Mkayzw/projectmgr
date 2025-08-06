from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import User


# Shared properties
class WorkspaceBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Properties to receive via API on creation
class WorkspaceCreate(WorkspaceBase):
    name: str


# Properties to receive via API on update
class WorkspaceUpdate(WorkspaceBase):
    pass


# Properties shared by models stored in DB
class WorkspaceInDBBase(WorkspaceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Workspace(WorkspaceInDBBase):
    pass


# Additional properties to return via API with members
class WorkspaceWithMembers(Workspace):
    owner: User
    members: List[User] = []