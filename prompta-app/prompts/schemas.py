from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# Project Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    directory: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)

    @validator("name")
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @validator("directory")
    def validate_directory(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @validator("tags")
    def validate_tags(cls, v):
        if v:
            v = [tag.strip().lower() for tag in v if tag.strip()]
            v = list(set(v))  # Remove duplicates
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    directory: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    directory: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty")
        return v

    @validator("directory")
    def validate_directory(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            v = [tag.strip().lower() for tag in v if tag.strip()]
            v = list(set(v))  # Remove duplicates
        return v


# Prompt Version Schemas
class PromptVersionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    commit_message: Optional[str] = None


class PromptVersionResponse(BaseModel):
    id: str
    version_number: int
    content: str
    commit_message: Optional[str]
    created_at: datetime
    is_current: bool

    class Config:
        from_attributes = True


class PromptVersionUpdate(BaseModel):
    commit_message: Optional[str] = None


# Prompt Schemas
class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location: str = Field(..., min_length=1, max_length=500)
    project_id: Optional[str] = None  # Optional project association
    tags: List[str] = Field(default_factory=list)
    content: str = Field(..., min_length=1)  # Initial version content
    commit_message: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        # Remove any leading/trailing whitespace and ensure it's not empty
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    @validator("location")
    def validate_location(cls, v):
        # Basic path validation
        v = v.strip()
        if not v:
            raise ValueError("Location cannot be empty")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        # Ensure tags are unique and not empty
        if v:
            v = [tag.strip().lower() for tag in v if tag.strip()]
            v = list(set(v))  # Remove duplicates
        return v


class PromptResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    location: str
    project_id: Optional[str]
    project: Optional[ProjectResponse]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    current_version: Optional[PromptVersionResponse]

    class Config:
        from_attributes = True


class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    project_id: Optional[str] = None
    tags: Optional[List[str]] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Name cannot be empty")
        return v

    @validator("location")
    def validate_location(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Location cannot be empty")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            v = [tag.strip().lower() for tag in v if tag.strip()]
            v = list(set(v))  # Remove duplicates
        return v


# List Response Schemas
class PromptListResponse(BaseModel):
    prompts: List[PromptResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PromptVersionListResponse(BaseModel):
    versions: List[PromptVersionResponse]
    total: int


# Search and Filter Schemas
class PromptSearchParams(BaseModel):
    query: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    directory: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @validator("tags")
    def validate_tags(cls, v):
        if v:
            v = [tag.strip().lower() for tag in v if tag.strip()]
        return v


# Download Schemas
class PromptDownloadParams(BaseModel):
    project_name: Optional[str] = None
    directory: Optional[str] = None
    tags: Optional[List[str]] = None
    include_content: bool = Field(default=True, description="Include prompt content in response")
    format: str = Field(default="json", description="Response format: json, zip")

    @validator("tags")
    def validate_tags(cls, v):
        if v:
            v = [tag.strip().lower() for tag in v if tag.strip()]
        return v

    @validator("format")
    def validate_format(cls, v):
        if v not in ["json", "zip"]:
            raise ValueError("Format must be 'json' or 'zip'")
        return v


class PromptDownloadResponse(BaseModel):
    prompts: List[PromptResponse]
    total: int
    download_format: str
    filters_applied: dict


# Version Comparison Schema
class VersionDiffResponse(BaseModel):
    prompt_id: str
    version1: PromptVersionResponse
    version2: PromptVersionResponse
    diff: str  # Text diff between versions


# Restore Version Schema
class RestoreVersionRequest(BaseModel):
    version_number: int = Field(..., ge=1)
    commit_message: Optional[str] = "Restored from version {version_number}"
