from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import (
    Workspace as WorkspaceSchema,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceWithMembers,
)

router = APIRouter()


@router.get("/", response_model=List[WorkspaceSchema])
def read_workspaces(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve workspaces. Users can only see workspaces they are members of or own.
    """
    if current_user.is_superuser:
        workspaces = db.query(Workspace).offset(skip).limit(limit).all()
    else:
        # Get workspaces where user is owner or member
        workspaces = (
            db.query(Workspace)
            .filter(
                (Workspace.owner_id == current_user.id)
                | (Workspace.members.any(User.id == current_user.id))
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    return workspaces


@router.post("/", response_model=WorkspaceSchema)
def create_workspace(
    *,
    db: Session = Depends(deps.get_db),
    workspace_in: WorkspaceCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new workspace.
    """
    workspace = Workspace(
        **workspace_in.dict(),
        owner_id=current_user.id,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceWithMembers)
def read_workspace(
    *,
    db: Session = Depends(deps.get_db),
    workspace_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get workspace by ID.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Check if user has access to this workspace
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            current_user in workspace.members):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceSchema)
def update_workspace(
    *,
    db: Session = Depends(deps.get_db),
    workspace_id: int,
    workspace_in: WorkspaceUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a workspace.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Only owner or superuser can update workspace
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = workspace_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", response_model=WorkspaceSchema)
def delete_workspace(
    *,
    db: Session = Depends(deps.get_db),
    workspace_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a workspace.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Only owner or superuser can delete workspace
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(workspace)
    db.commit()
    return workspace


@router.post("/{workspace_id}/members/{user_id}", response_model=WorkspaceWithMembers)
def add_workspace_member(
    *,
    db: Session = Depends(deps.get_db),
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Add a member to the workspace.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Only owner or superuser can add members
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user in workspace.members:
        raise HTTPException(status_code=400, detail="User already in workspace")
    
    workspace.members.append(user)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}/members/{user_id}", response_model=WorkspaceWithMembers)
def remove_workspace_member(
    *,
    db: Session = Depends(deps.get_db),
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Remove a member from the workspace.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Only owner or superuser can remove members
    if not (current_user.is_superuser or workspace.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user not in workspace.members:
        raise HTTPException(status_code=400, detail="User not in workspace")
    
    workspace.members.remove(user)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace