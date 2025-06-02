from typing import List, Optional
import math
import io
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from auth.dependencies import get_current_user_flexible, get_current_user_optional
from auth.models import User
from .models import Prompt, PromptVersion
from .schemas import (
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    PromptListResponse,
    PromptVersionCreate,
    PromptVersionResponse,
    PromptVersionUpdate,
    PromptVersionListResponse,
    PromptSearchParams,
    VersionDiffResponse,
    RestoreVersionRequest,
    PromptDownloadParams,
    PromptDownloadResponse,
)
from .services import PromptService


router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_prompt(
    prompt_data: PromptCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Create a new prompt with initial version"""
    try:
        prompt = PromptService.create_prompt(db, current_user, prompt_data)
        return prompt
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=PromptListResponse)
@router.get("", response_model=PromptListResponse, include_in_schema=False)
async def list_prompts(
    query: Optional[str] = Query(
        None, description="Search term for name, description, or location"
    ),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    location: Optional[str] = Query(None, description="Filter by location pattern"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_auth: tuple[Optional[User], bool] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """List prompts with search and pagination

    - If no authentication: shows only public prompts
    - If authenticated with ACCESS_TOKEN: shows only user's own prompts
    - If authenticated with API_KEY: shows both public prompts and user's private prompts
    """
    user, is_api_key_auth = user_auth

    search_params = PromptSearchParams(
        query=query, tags=tags, location=location, page=page, page_size=page_size
    )

    # Include private prompts only if authenticated with API key
    include_private = bool(user and is_api_key_auth)

    prompts, total = PromptService.list_prompts(
        db, user, search_params, include_private
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PromptListResponse(
        prompts=prompts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/search", response_model=PromptListResponse)
async def search_prompts_by_content(
    q: str = Query(..., description="Search term for prompt content"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    user_auth: tuple[Optional[User], bool] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Search prompts by content in their current versions

    - If no authentication: searches only public prompts
    - If authenticated with ACCESS_TOKEN: searches only user's own prompts
    - If authenticated with API_KEY: searches both public prompts and user's private prompts
    """
    user, is_api_key_auth = user_auth

    # Include private prompts only if authenticated with API key
    include_private = bool(user and is_api_key_auth)

    prompts, total = PromptService.search_prompts_by_content(
        db, user, q, page, page_size, include_private
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PromptListResponse(
        prompts=prompts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    db: Session = Depends(get_db),
    user_auth: tuple[Optional[User], bool] = Depends(get_current_user_optional),
):
    """
    Get a specific prompt by ID.
    - If the prompt is public, anyone can access.
    - If the prompt is private, only the owner (authenticated) can access.
    """
    user, is_api_key_auth = user_auth

    prompt = PromptService.get_prompt_public_or_private(db, prompt_id, user)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found or not accessible",
        )
    return prompt


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    prompt_data: PromptUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Update a prompt's metadata"""
    try:
        prompt = PromptService.update_prompt(db, current_user, prompt_id, prompt_data)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
            )
        return prompt
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Delete a prompt and all its versions"""
    success = PromptService.delete_prompt(db, current_user, prompt_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )


# Version Management
@router.post(
    "/{prompt_id}/versions",
    response_model=PromptVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_version(
    prompt_id: str,
    version_data: PromptVersionCreate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Create a new version for a prompt"""
    version = PromptService.create_version(db, current_user, prompt_id, version_data)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )
    return version


@router.get("/{prompt_id}/versions", response_model=PromptVersionListResponse)
async def list_versions(
    prompt_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """List all versions of a prompt"""
    versions = PromptService.list_versions(db, current_user, prompt_id)
    return PromptVersionListResponse(versions=versions, total=len(versions))


@router.get(
    "/{prompt_id}/versions/{version_number}", response_model=PromptVersionResponse
)
async def get_version(
    prompt_id: str,
    version_number: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get a specific version of a prompt"""
    version = PromptService.get_version(db, current_user, prompt_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found"
        )
    return version


@router.put(
    "/{prompt_id}/versions/{version_number}", response_model=PromptVersionResponse
)
async def update_version(
    prompt_id: str,
    version_number: int,
    version_data: PromptVersionUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Update a version's commit message"""
    version = PromptService.get_version(db, current_user, prompt_id, version_number)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Version not found"
        )

    if version_data.commit_message is not None:
        version.commit_message = version_data.commit_message
        db.commit()
        db.refresh(version)

    return version


@router.post(
    "/{prompt_id}/restore/{version_number}", response_model=PromptVersionResponse
)
async def restore_version(
    prompt_id: str,
    version_number: int,
    restore_data: Optional[RestoreVersionRequest] = None,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Restore a prompt to a specific version by creating a new version"""
    commit_message = None
    if restore_data and restore_data.commit_message:
        commit_message = restore_data.commit_message.format(
            version_number=version_number
        )

    new_version = PromptService.restore_version(
        db, current_user, prompt_id, version_number, commit_message
    )
    if not new_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt or version not found"
        )
    return new_version


@router.get("/{prompt_id}/diff/{version1}/{version2}")
async def compare_versions(
    prompt_id: str,
    version1: int,
    version2: int,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Compare two versions and return a diff"""
    diff = PromptService.compare_versions(
        db, current_user, prompt_id, version1, version2
    )
    if diff is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both versions not found",
        )

    # Get the version objects for the response
    v1 = PromptService.get_version(db, current_user, prompt_id, version1)
    v2 = PromptService.get_version(db, current_user, prompt_id, version2)

    return VersionDiffResponse(prompt_id=prompt_id, version1=v1, version2=v2, diff=diff)


# Download Endpoints
@router.get("/download", response_model=PromptDownloadResponse)
async def download_prompts(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    directory: Optional[str] = Query(None, description="Filter by directory pattern"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    include_content: bool = Query(
        True, description="Include prompt content in response"
    ),
    format: str = Query("json", description="Response format: json, zip"),
    user_auth: tuple[Optional[User], bool] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Download prompts filtered by project_name, directory, or tags

    - If no authentication: downloads only public prompts
    - If authenticated with ACCESS_TOKEN: downloads only user's own prompts
    - If authenticated with API_KEY: downloads both public prompts and user's private prompts
    """
    user, is_api_key_auth = user_auth

    download_params = PromptDownloadParams(
        project_name=project_name,
        directory=directory,
        tags=tags,
        include_content=include_content,
        format=format,
    )

    try:
        # Include private prompts only if authenticated with API key
        include_private = bool(user and is_api_key_auth)

        prompts, total, filters_applied = PromptService.download_prompts(
            db, user, download_params, include_private
        )

        if format == "json":
            return PromptDownloadResponse(
                prompts=prompts,
                total=total,
                download_format=format,
                filters_applied=filters_applied,
            )
        else:
            # This will be handled by the zip endpoint
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /download/zip endpoint for zip format",
            )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/download/by-project/{project_name}", response_model=PromptDownloadResponse
)
async def download_prompts_by_project(
    project_name: str,
    include_content: bool = Query(
        True, description="Include prompt content in response"
    ),
    user_auth: tuple[Optional[User], bool] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Download all prompts from a specific project

    - If no authentication: downloads only public prompts from the project
    - If authenticated with ACCESS_TOKEN: downloads only user's own prompts from the project
    - If authenticated with API_KEY: downloads both public and user's private prompts from the project
    """
    user, is_api_key_auth = user_auth

    download_params = PromptDownloadParams(
        project_name=project_name,
        include_content=include_content,
        format="json",
    )

    try:
        # Include private prompts only if authenticated with API key
        include_private = bool(user and is_api_key_auth)

        prompts, total, filters_applied = PromptService.download_prompts(
            db, user, download_params, include_private
        )

        return PromptDownloadResponse(
            prompts=prompts,
            total=total,
            download_format="json",
            filters_applied=filters_applied,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
