from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.workspaces import router as workspaces_router
from app.api.routes.projects import router as projects_router
from app.api.routes.tasks import router as tasks_router

# For convenience in imports
__all__ = [
    "auth_router",
    "users_router",
    "workspaces_router",
    "projects_router",
    "tasks_router",
]