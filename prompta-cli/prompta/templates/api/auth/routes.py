from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.config import settings
from .models import User, APIKey
from .schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    Token,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyUpdate,
    APIKeyListResponse,
)
from .security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    create_api_key,
)
from .dependencies import get_current_user_from_token, get_current_user_flexible


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username or email already exists
    existing_user = (
        db.query(User)
        .filter((User.username == user_data.username) | (User.email == user_data.email))
        .first()
    )

    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists",
        )

    return db_user


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_flexible),
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Update current user information"""
    if user_update.email:
        # Check if email is already taken by another user
        existing_user = (
            db.query(User)
            .filter(User.email == user_update.email, User.id != current_user.id)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        current_user.email = user_update.email

    if user_update.password:
        current_user.password_hash = get_password_hash(user_update.password)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    return current_user


@router.post(
    "/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED
)
async def create_user_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
):
    """Create a new API key for the current user"""
    # Check if user already has an API key with this name
    existing_key = (
        db.query(APIKey)
        .filter(
            APIKey.user_id == current_user.id,
            APIKey.name == api_key_data.name,
            APIKey.is_active == True,
        )
        .first()
    )

    if existing_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key with this name already exists",
        )

    db_api_key, api_key = create_api_key(
        db=db,
        user_id=current_user.id,
        name=api_key_data.name,
        expires_at=api_key_data.expires_at,
    )

    # Return the API key with the actual key value (only on creation)
    response = APIKeyResponse.model_validate(db_api_key)
    response.key = api_key
    return response


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_user_api_keys(
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """List all API keys for the current user"""
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()

    return APIKeyListResponse(
        api_keys=[APIKeyResponse.model_validate(key) for key in api_keys],
        total=len(api_keys),
    )


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Get a specific API key"""
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    return api_key


@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    api_key_update: APIKeyUpdate,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Update an API key"""
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    if api_key_update.name is not None:
        # Check if another active key with this name exists
        existing_key = (
            db.query(APIKey)
            .filter(
                APIKey.user_id == current_user.id,
                APIKey.name == api_key_update.name,
                APIKey.id != key_id,
                APIKey.is_active == True,
            )
            .first()
        )

        if existing_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="API key with this name already exists",
            )

        api_key.name = api_key_update.name

    if api_key_update.is_active is not None:
        api_key.is_active = api_key_update.is_active

    db.commit()
    db.refresh(api_key)

    return api_key


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user_flexible),
    db: Session = Depends(get_db),
):
    """Delete (deactivate) an API key"""
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # Soft delete by deactivating
    api_key.is_active = False
    db.commit()

    return None
