from typing import Optional

from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import ProjectService


class TaskService:
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks_by_project(
        db: Session,
        project_id: int,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks in a project with optional filters."""
        query = db.query(Task).filter(Task.project_id == project_id)
        
        if status:
            query = query.filter(Task.status == status)
        if assignee_id:
            query = query.filter(Task.assignee_id == assignee_id)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_by_assignee(
        db: Session,
        assignee_id: int,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks assigned to a user with optional status filter."""
        query = db.query(Task).filter(Task.assignee_id == assignee_id)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_by_user_access(
        db: Session,
        user_id: int,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Get tasks that user has access to (through project membership)."""
        # Get all projects user has access to
        user_projects = ProjectService.get_projects_by_user(db, user_id)
        project_ids = [p.id for p in user_projects]
        
        if not project_ids:
            return []
        
        query = db.query(Task).filter(Task.project_id.in_(project_ids))
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_all_tasks(
        db: Session,
        status: Optional[TaskStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """Get all tasks (superuser only)."""
        query = db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create_task(
        db: Session, task: TaskCreate, project_id: int, creator_id: int
    ) -> Optional[Task]:
        """Create a new task."""
        # Check if user has access to project
        if not ProjectService.has_access(db, project_id, creator_id):
            return None

        # Validate assignee if provided
        if task.assignee_id:
            assignee = db.query(User).filter(User.id == task.assignee_id).first()
            if not assignee:
                return None
            # Check if assignee has access to project
            if not ProjectService.has_access(db, project_id, task.assignee_id):
                return None

        db_task = Task(
            title=task.title,
            description=task.description,
            status=task.status or TaskStatus.TODO,
            priority=task.priority or TaskPriority.MEDIUM,
            due_date=task.due_date,
            project_id=project_id,
            assignee_id=task.assignee_id,
            creator_id=creator_id,
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def update_task(
        db: Session, task_id: int, task_update: TaskUpdate, user_id: int
    ) -> Optional[Task]:
        """Update task information."""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return None

        # Check if user has access to the task's project
        if not ProjectService.has_access(db, db_task.project_id, user_id):
            return None

        update_data = task_update.model_dump(exclude_unset=True)
        
        # Validate assignee if being updated
        if "assignee_id" in update_data and update_data["assignee_id"]:
            assignee = db.query(User).filter(User.id == update_data["assignee_id"]).first()
            if not assignee:
                return None
            # Check if assignee has access to project
            if not ProjectService.has_access(db, db_task.project_id, update_data["assignee_id"]):
                return None

        for field, value in update_data.items():
            setattr(db_task, field, value)

        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int, user_id: int) -> bool:
        """Delete a task."""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return False

        # Check if user has access to the task's project
        if not ProjectService.has_access(db, db_task.project_id, user_id):
            return False

        db.delete(db_task)
        db.commit()
        return True

    @staticmethod
    def has_access(db: Session, task_id: int, user_id: int) -> bool:
        """Check if user has access to task (through project access)."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return False
        
        return ProjectService.has_access(db, task.project_id, user_id)

    @staticmethod
    def update_task_status(
        db: Session, task_id: int, status: TaskStatus, user_id: int
    ) -> Optional[Task]:
        """Update task status."""
        db_task = db.query(Task).filter(Task.id == task_id).first()
        if not db_task:
            return None

        # Check if user has access to the task's project
        if not ProjectService.has_access(db, db_task.project_id, user_id):
            return None

        db_task.status = status
        db.commit()
        db.refresh(db_task)
        return db_task