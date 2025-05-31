from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @validator("username")
    def validate_username(cls, v):
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


# API Key Schemas
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: Optional[str] = None  # Only returned on creation
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


# Response Models
class APIKeyListResponse(BaseModel):
    api_keys: List[APIKeyResponse]
    total: int
