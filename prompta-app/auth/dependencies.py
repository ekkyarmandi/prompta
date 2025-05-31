from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from .models import User
from .security import verify_token, verify_api_key


# Security schemes
security = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_current_user_from_api_key(
    api_key: str = Security(api_key_header), db: Session = Depends(get_db)
) -> User:
    """Get current user from API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    user = verify_api_key(db, api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user


async def get_current_user(
    token_user: User = Depends(get_current_user_from_token),
    api_key_user: User = Depends(get_current_user_from_api_key),
) -> User:
    """Get current user from either JWT token or API key"""
    # Try token first, then API key
    if token_user:
        return token_user
    elif api_key_user:
        return api_key_user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )


# Alternative dependency that tries both methods
async def get_current_user_flexible(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    api_key: Optional[str] = Security(api_key_header),
) -> User:
    """Get current user from either JWT token or API key (flexible approach)"""
    user = None

    # Try JWT token first
    if credentials:
        token_data = verify_token(credentials.credentials)
        if token_data:
            user = db.query(User).filter(User.username == token_data.username).first()

    # Try API key if token didn't work
    if not user and api_key:
        user = verify_api_key(db, api_key)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    return user
