from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project import Project
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.project import (
    Project as ProjectSchema,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithMembers,
)

router = APIRouter()


@router.get("/", response_model=List[ProjectSchema])
def read_projects(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    workspace_id: int = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve projects. Users can only see projects they have access to.
    """
    if current_user.is_superuser:
        query = db.query(Project)
        if workspace_id:
            query = query.filter(Project.workspace_id == workspace_id)
        projects = query.offset(skip).limit(limit).all()
    else:
        # Get projects where user is a member or in a workspace where user is a member/owner
        query = (
            db.query(Project)
            .join(Workspace)
            .filter(
                (Project.members.any(User.id == current_user.id))
                | (Workspace.owner_id == current_user.id)
                | (Workspace.members.any(User.id == current_user.id))
            )
        )
        if workspace_id:
            query = query.filter(Project.workspace_id == workspace_id)
        projects = query.offset(skip).limit(limit).all()
    return projects


@router.post("/", response_model=ProjectSchema)
def create_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: ProjectCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new project.
    """
    # Check if workspace exists and user has access
    workspace = db.query(Workspace).filter(Workspace.id == project_in.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            current_user in workspace.members):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    project = Project(**project_in.dict())
    project.members.append(current_user)  # Add creator as a member
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectWithMembers)
def read_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to this project
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            current_user in workspace.members or current_user in project.members):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return project


@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: ProjectUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to update this project
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = project_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=ProjectSchema)
def delete_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to delete this project
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(project)
    db.commit()
    return project


@router.post("/{project_id}/members/{user_id}", response_model=ProjectWithMembers)
def add_project_member(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Add a member to the project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to add members
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in project.members:
        raise HTTPException(status_code=400, detail="User already in project")
    
    project.members.append(user)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}/members/{user_id}", response_model=ProjectWithMembers)
def remove_project_member(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove a member from the project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access to remove members
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user not in project.members:
        raise HTTPException(status_code=400, detail="User not in project")
    
    project.members.remove(user)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project