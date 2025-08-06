from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.user import User


# Shared properties
class ProjectBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workspace_id: Optional[int] = None


# Properties to receive via API on creation
class ProjectCreate(ProjectBase):
    name: str
    workspace_id: int


# Properties to receive via API on update
class ProjectUpdate(ProjectBase):
    pass


# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Additional properties to return via API
class Project(ProjectInDBBase):
    pass


# Additional properties to return via API with members
class ProjectWithMembers(Project):
    members: List[User] = []