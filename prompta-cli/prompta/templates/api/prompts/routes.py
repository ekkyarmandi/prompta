from typing import List, Optional
import math
import io
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from auth.dependencies import get_current_user_flexible
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


# Prompt CRUD Operations
@router.post("/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
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
async def list_prompts(
    query: Optional[str] = Query(
        None, description="Search term for name, description, or location"
    ),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    location: Optional[str] = Query(None, description="Filter by location pattern"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """List user's prompts with search and pagination"""
    search_params = PromptSearchParams(
        query=query, tags=tags, location=location, page=page, page_size=page_size
    )

    prompts, total = PromptService.list_prompts(db, current_user, search_params)
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
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Search prompts by content in their current versions"""
    prompts, total = PromptService.search_prompts_by_content(
        db, current_user, q, page, page_size
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PromptListResponse(
        prompts=prompts,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/by-location", response_model=PromptResponse)
async def get_prompt_by_location(
    location: str = Query(..., description="File location path"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get prompt by its file location"""
    prompt = PromptService.get_prompt_by_location(db, current_user, location)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prompt not found at this location",
        )
    return prompt


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get a specific prompt by ID"""
    prompt = PromptService.get_prompt_by_id(db, current_user, prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
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
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Download prompts filtered by project_name, directory, or tags"""
    download_params = PromptDownloadParams(
        project_name=project_name,
        directory=directory,
        tags=tags,
        include_content=include_content,
        format=format,
    )

    try:
        prompts, total, filters_applied = PromptService.download_prompts(
            db, current_user, download_params
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


@router.get("/download/zip")
async def download_prompts_zip(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    directory: Optional[str] = Query(None, description="Filter by directory pattern"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Download prompts as a ZIP file filtered by project_name, directory, or tags"""
    download_params = PromptDownloadParams(
        project_name=project_name,
        directory=directory,
        tags=tags,
        include_content=True,
        format="zip",
    )

    try:
        prompts, total, filters_applied = PromptService.download_prompts(
            db, current_user, download_params
        )

        if not prompts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No prompts found matching the criteria",
            )

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for prompt in prompts:
                if prompt.current_version and prompt.current_version.content:
                    # Create a safe filename
                    safe_name = "".join(
                        c for c in prompt.name if c.isalnum() or c in (" ", "-", "_")
                    ).rstrip()
                    filename = f"{safe_name}.txt"

                    # Add metadata as comment
                    metadata = f"""# Prompt: {prompt.name}
# Description: {prompt.description or 'No description'}
# Location: {prompt.location}
# Tags: {', '.join(prompt.tags) if prompt.tags else 'No tags'}
# Project: {prompt.project.name if prompt.project else 'No project'}
# Created: {prompt.created_at}
# Updated: {prompt.updated_at}
# Version: {prompt.current_version.version_number}

"""
                    content = metadata + prompt.current_version.content
                    zip_file.writestr(filename, content)

        zip_buffer.seek(0)

        # Generate filename based on filters
        filename_parts = []
        if project_name:
            filename_parts.append(f"project-{project_name}")
        if directory:
            filename_parts.append(f"dir-{directory.replace('/', '-')}")
        if tags:
            filename_parts.append(f"tags-{'-'.join(tags)}")

        if not filename_parts:
            filename_parts.append("all-prompts")

        filename = f"prompta-prompts-{'-'.join(filename_parts)}.zip"

        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
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
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Download all prompts from a specific project"""
    download_params = PromptDownloadParams(
        project_name=project_name,
        include_content=include_content,
        format="json",
    )

    try:
        prompts, total, filters_applied = PromptService.download_prompts(
            db, current_user, download_params
        )

        return PromptDownloadResponse(
            prompts=prompts,
            total=total,
            download_format="json",
            filters_applied=filters_applied,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/download/by-directory", response_model=PromptDownloadResponse)
async def download_prompts_by_directory(
    directory: str = Query(..., description="Directory pattern to filter by"),
    include_content: bool = Query(
        True, description="Include prompt content in response"
    ),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Download all prompts from a specific directory pattern"""
    download_params = PromptDownloadParams(
        directory=directory,
        include_content=include_content,
        format="json",
    )

    try:
        prompts, total, filters_applied = PromptService.download_prompts(
            db, current_user, download_params
        )

        return PromptDownloadResponse(
            prompts=prompts,
            total=total,
            download_format="json",
            filters_applied=filters_applied,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/download/by-tags", response_model=PromptDownloadResponse)
async def download_prompts_by_tags(
    tags: List[str] = Query(..., description="Tags to filter by"),
    include_content: bool = Query(
        True, description="Include prompt content in response"
    ),
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Download all prompts matching specific tags"""
    download_params = PromptDownloadParams(
        tags=tags,
        include_content=include_content,
        format="json",
    )

    try:
        prompts, total, filters_applied = PromptService.download_prompts(
            db, current_user, download_params
        )

        return PromptDownloadResponse(
            prompts=prompts,
            total=total,
            download_format="json",
            filters_applied=filters_applied,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
