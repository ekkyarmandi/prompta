from datetime import datetime, timedelta
from typing import Optional, Union
import secrets
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from .models import User, APIKey
from .schemas import TokenData


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> Union[User, bool]:
    """Authenticate a user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
        return token_data
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a new API key"""
    return f"prompta_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(db: Session, api_key: str) -> Optional[User]:
    """Verify an API key and return the associated user"""
    key_hash = hash_api_key(api_key)

    api_key_obj = (
        db.query(APIKey)
        .filter(APIKey.key_hash == key_hash, APIKey.is_active == True)
        .first()
    )

    if not api_key_obj:
        return None

    # Check if key has expired
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.utcnow():
        return None

    # Update last used timestamp
    api_key_obj.last_used_at = datetime.utcnow()
    db.commit()

    return api_key_obj.user


def create_api_key(
    db: Session, user_id: str, name: str, expires_at: Optional[datetime] = None
) -> tuple[APIKey, str]:
    """Create a new API key for a user"""
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    db_api_key = APIKey(
        user_id=user_id, key_hash=key_hash, name=name, expires_at=expires_at
    )

    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    return db_api_key, api_key
