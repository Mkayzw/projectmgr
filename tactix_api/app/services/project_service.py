from typing import Optional

from sqlalchemy.orm import Session

from app.models.project import Project, project_members
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.workspace_service import WorkspaceService


class ProjectService:
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_projects_by_workspace(
        db: Session, workspace_id: int, skip: int = 0, limit: int = 100
    ) -> list[Project]:
        """Get projects in a workspace."""
        return (
            db.query(Project)
            .filter(Project.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_projects_by_user(
        db: Session, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Project]:
        """Get projects where user is a member."""
        return (
            db.query(Project)
            .join(project_members, Project.id == project_members.c.project_id)
            .filter(project_members.c.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_projects(db: Session, skip: int = 0, limit: int = 100) -> list[Project]:
        """Get all projects (superuser only)."""
        return db.query(Project).offset(skip).limit(limit).all()

    @staticmethod
    def create_project(
        db: Session, project: ProjectCreate, workspace_id: int, creator_id: int
    ) -> Optional[Project]:
        """Create a new project."""
        # Check if user has access to workspace
        if not WorkspaceService.has_access(db, workspace_id, creator_id):
            return None

        db_project = Project(
            name=project.name,
            description=project.description,
            workspace_id=workspace_id,
        )
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        # Add creator as a member
        ProjectService.add_member(db, db_project.id, creator_id)
        
        return db_project

    @staticmethod
    def update_project(
        db: Session, project_id: int, project_update: ProjectUpdate
    ) -> Optional[Project]:
        """Update project information."""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return None

        update_data = project_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_project, field, value)

        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """Delete a project."""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return False

        db.delete(db_project)
        db.commit()
        return True

    @staticmethod
    def add_member(db: Session, project_id: int, user_id: int) -> bool:
        """Add a member to project."""
        # Check if project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Check if user has access to the workspace
        if not WorkspaceService.has_access(db, project.workspace_id, user_id):
            return False

        # Check if user is already a member
        existing_member = (
            db.query(project_members)
            .filter(
                project_members.c.project_id == project_id,
                project_members.c.user_id == user_id,
            )
            .first()
        )
        if existing_member:
            return True  # Already a member

        # Add member
        db.execute(
            project_members.insert().values(project_id=project_id, user_id=user_id)
        )
        db.commit()
        return True

    @staticmethod
    def remove_member(db: Session, project_id: int, user_id: int) -> bool:
        """Remove a member from project."""
        result = db.execute(
            project_members.delete().where(
                project_members.c.project_id == project_id,
                project_members.c.user_id == user_id,
            )
        )
        db.commit()
        return result.rowcount > 0

    @staticmethod
    def is_member(db: Session, project_id: int, user_id: int) -> bool:
        """Check if user is a member of project."""
        member = (
            db.query(project_members)
            .filter(
                project_members.c.project_id == project_id,
                project_members.c.user_id == user_id,
            )
            .first()
        )
        return member is not None

    @staticmethod
    def has_access(db: Session, project_id: int, user_id: int) -> bool:
        """Check if user has access to project (member or workspace access)."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # Check if user is project member or has workspace access
        return (
            ProjectService.is_member(db, project_id, user_id)
            or WorkspaceService.has_access(db, project.workspace_id, user_id)
        )