from typing import List, Optional
import logging
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from auth.dependencies import get_current_user_flexible
from auth.models import User
from .models import Project
from .schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectListResponse,
)
from .services import ProjectService


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Create a new project"""
    try:
        project = ProjectService.create_project(db, current_user, project_data)
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:  # pragma: no cover – catch-all safeguards
        logging.getLogger(__name__).exception("Unexpected error while creating project")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the project.",
        ) from e


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    query: Optional[str] = Query(
        None, description="Search term for name or description"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """List user's projects with search and pagination"""
    projects, total = ProjectService.list_projects(
        db, current_user, query, None, page, page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return ProjectListResponse(
        projects=projects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get a specific project by ID"""
    project = ProjectService.get_project_by_id(db, current_user, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.get("/by-name/{project_name}", response_model=ProjectResponse)
async def get_project_by_name(
    project_name: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get a project by its name"""
    project = ProjectService.get_project_by_name(db, current_user, project_name)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Update a project's metadata"""
    try:
        project = ProjectService.update_project(
            db, current_user, project_id, project_data
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        return project
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).exception("Unexpected error while updating project")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the project.",
        ) from e


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Delete a project and all its prompts"""
    success = ProjectService.delete_project(db, current_user, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
