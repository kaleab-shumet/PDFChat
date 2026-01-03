from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from ..core.database import get_db
from ..models.project import Project
from ..schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from ..schemas.response import (
    success_response,
    project_not_found_error,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """Create a new project."""
    user_id = request.state.user_id
    request_id = getattr(request.state, "request_id", None)

    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_user_id=user_id,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    project_response = ProjectResponse.model_validate(db_project)

    return success_response(
        data=project_response.model_dump(),
        message="Project created successfully",
        request_id=request_id,
    )


@router.get("/")
async def list_projects(request: Request, db: AsyncSession = Depends(get_db)):
    """List all projects owned by the current user."""
    user_id = request.state.user_id
    request_id = getattr(request.state, "request_id", None)

    result = await db.execute(select(Project).where(Project.owner_user_id == user_id))
    db_projects = result.scalars().all()

    projects_response = [
        ProjectResponse.model_validate(project).model_dump() for project in db_projects
    ]

    return success_response(
        data=projects_response,
        message="Projects retrieved successfully",
        request_id=request_id,
    )


@router.get("/{project_id}")
async def get_project(
    project_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Get a specific project by ID."""
    user_id = request.state.user_id
    request_id = getattr(request.state, "request_id", None)

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid, Project.owner_user_id == user_id
        )
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    project_response = ProjectResponse.model_validate(db_project)

    return success_response(
        data=project_response.model_dump(),
        message="Project retrieved successfully",
        request_id=request_id,
    )


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update a project."""
    user_id = request.state.user_id
    request_id = getattr(request.state, "request_id", None)

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid, Project.owner_user_id == user_id
        )
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    # Update fields that were provided
    if project_data.name is not None:
        db_project.name = project_data.name
    if project_data.description is not None:
        db_project.description = project_data.description

    await db.commit()
    await db.refresh(db_project)

    project_response = ProjectResponse.model_validate(db_project)

    return success_response(
        data=project_response.model_dump(),
        message="Project updated successfully",
        request_id=request_id,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """Delete a project."""
    user_id = request.state.user_id
    request_id = getattr(request.state, "request_id", None)

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    result = await db.execute(
        select(Project).where(
            Project.id == project_uuid, Project.owner_user_id == user_id
        )
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=project_not_found_error(request_id),
        )

    await db.delete(db_project)
    await db.commit()

    return None
