from fastapi import APIRouter
from api.v1.routes import health, auth, projects

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
