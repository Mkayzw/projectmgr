from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace, workspace_members
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    @staticmethod
    def get_workspace(db: Session, workspace_id: int) -> Optional[Workspace]:
        """Get workspace by ID."""
        return db.query(Workspace).filter(Workspace.id == workspace_id).first()

    @staticmethod
    def get_workspaces_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Workspace]:
        """Get workspaces where user is owner or member."""
        return (
            db.query(Workspace)
            .join(workspace_members, Workspace.id == workspace_members.c.workspace_id)
            .filter(
                (Workspace.owner_id == user_id) | (workspace_members.c.user_id == user_id)
            )
            .distinct()
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_all_workspaces(db: Session, skip: int = 0, limit: int = 100) -> list[Workspace]:
        """Get all workspaces (superuser only)."""
        return db.query(Workspace).offset(skip).limit(limit).all()

    @staticmethod
    def create_workspace(db: Session, workspace: WorkspaceCreate, owner_id: int) -> Workspace:
        """Create a new workspace."""
        db_workspace = Workspace(
            name=workspace.name,
            description=workspace.description,
            owner_id=owner_id,
        )
        db.add(db_workspace)
        db.commit()
        db.refresh(db_workspace)
        
        # Add owner as a member
        WorkspaceService.add_member(db, db_workspace.id, owner_id)
        
        return db_workspace

    @staticmethod
    def update_workspace(
        db: Session, workspace_id: int, workspace_update: WorkspaceUpdate
    ) -> Optional[Workspace]:
        """Update workspace information."""
        db_workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not db_workspace:
            return None

        update_data = workspace_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_workspace, field, value)

        db.commit()
        db.refresh(db_workspace)
        return db_workspace

    @staticmethod
    def delete_workspace(db: Session, workspace_id: int) -> bool:
        """Delete a workspace."""
        db_workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not db_workspace:
            return False

        db.delete(db_workspace)
        db.commit()
        return True

    @staticmethod
    def add_member(db: Session, workspace_id: int, user_id: int) -> bool:
        """Add a member to workspace."""
        # Check if workspace exists
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            return False

        # Check if user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Check if user is already a member
        existing_member = (
            db.query(workspace_members)
            .filter(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
            .first()
        )
        if existing_member:
            return True  # Already a member

        # Add member
        db.execute(
            workspace_members.insert().values(
                workspace_id=workspace_id, user_id=user_id
            )
        )
        db.commit()
        return True

    @staticmethod
    def remove_member(db: Session, workspace_id: int, user_id: int) -> bool:
        """Remove a member from workspace."""
        result = db.execute(
            workspace_members.delete().where(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
        )
        db.commit()
        return result.rowcount > 0

    @staticmethod
    def is_member(db: Session, workspace_id: int, user_id: int) -> bool:
        """Check if user is a member of workspace."""
        member = (
            db.query(workspace_members)
            .filter(
                workspace_members.c.workspace_id == workspace_id,
                workspace_members.c.user_id == user_id,
            )
            .first()
        )
        return member is not None

    @staticmethod
    def is_owner(db: Session, workspace_id: int, user_id: int) -> bool:
        """Check if user is the owner of workspace."""
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        return workspace and workspace.owner_id == user_id

    @staticmethod
    def has_access(db: Session, workspace_id: int, user_id: int) -> bool:
        """Check if user has access to workspace (owner or member)."""
        return (
            WorkspaceService.is_owner(db, workspace_id, user_id)
            or WorkspaceService.is_member(db, workspace_id, user_id)
        )