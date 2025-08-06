from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.task import (
    Task as TaskSchema,
    TaskCreate,
    TaskUpdate,
    TaskWithDetails,
)

router = APIRouter()


@router.get("/", response_model=List[TaskSchema])
def read_tasks(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = None,
    status: TaskStatus = None,
    assignee_id: int = None,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve tasks. Users can only see tasks they have access to.
    """
    # Base query
    query = db.query(Task)
    
    # Apply filters
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    # If not superuser, filter by access
    if not current_user.is_superuser:
        # Tasks where user is assignee, creator, or in project/workspace
        query = query.join(Project).join(Workspace).filter(
            (Task.assignee_id == current_user.id)
            | (Task.created_by_id == current_user.id)
            | (Project.members.any(User.id == current_user.id))
            | (Workspace.owner_id == current_user.id)
            | (Workspace.members.any(User.id == current_user.id))
        )
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.post("/", response_model=TaskSchema)
def create_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new task.
    """
    # Check if project exists and user has access
    project = db.query(Project).filter(Project.id == task_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            current_user in workspace.members or current_user in project.members):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if assignee exists and is a member of the project
    if task_in.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")
        if assignee not in project.members and assignee != workspace.owner and assignee not in workspace.members:
            raise HTTPException(status_code=400, detail="Assignee must be a member of the project or workspace")
    
    task = Task(
        **task_in.dict(),
        created_by_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskWithDetails)
def read_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get task by ID.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user has access to this task
    project = db.query(Project).filter(Project.id == task.project_id).first()
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            current_user in workspace.members or current_user in project.members or
            task.assignee_id == current_user.id or task.created_by_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return task


@router.put("/{task_id}", response_model=TaskSchema)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user has access to update this task
    project = db.query(Project).filter(Project.id == task.project_id).first()
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            task.created_by_id == current_user.id or task.assignee_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check if new assignee exists and is a member of the project
    if task_in.assignee_id and task_in.assignee_id != task.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assignee not found")
        if assignee not in project.members and assignee != workspace.owner and assignee not in workspace.members:
            raise HTTPException(status_code=400, detail="Assignee must be a member of the project or workspace")
    
    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", response_model=TaskSchema)
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check if user has access to delete this task
    project = db.query(Project).filter(Project.id == task.project_id).first()
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    
    if not (current_user.is_superuser or workspace.owner_id == current_user.id or 
            task.created_by_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(task)
    db.commit()
    return task