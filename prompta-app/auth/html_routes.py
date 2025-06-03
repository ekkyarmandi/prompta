from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.config import settings
from .models import User, APIKey
from .schemas import UserCreate, UserLogin
from .security import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_token,
)
from .dependencies import get_current_user_from_token


# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create router for HTML auth endpoints
router = APIRouter(prefix="/auth/html", tags=["html-authentication"])


def get_user_from_cookie(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from access token stored in cookie."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None

    try:
        token_data = verify_token(access_token)
        if token_data is None:
            return None

        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None or not user.is_active:
            return None

        return user
    except Exception:
        return None


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Display the login page."""
    # Check if user is already logged in
    user = get_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_user_html(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process login form submission and set cookie."""
    try:
        # Authenticate user
        user = authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        # Create response and set cookie
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=settings.access_token_expire_minutes * 60,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
        )

        return response

    except HTTPException as e:
        # Return error response
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": e.detail},
            status_code=e.status_code,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "An unexpected error occurred"},
            status_code=500,
        )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Display the registration page."""
    # Check if user is already logged in
    user = get_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register_user_html(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process registration form submission."""
    try:
        # Check if username or email already exists
        existing_user = (
            db.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )

        if existing_user:
            if existing_user.username == username:
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
        hashed_password = get_password_hash(password)
        db_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Return success response
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "success": "Account created successfully! Please login.",
            },
            status_code=201,
        )

    except HTTPException as e:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": e.detail},
            status_code=e.status_code,
        )
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "User with this username or email already exists",
            },
            status_code=400,
        )
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "An unexpected error occurred"},
            status_code=500,
        )


@router.post("/logout")
async def logout_user_html(request: Request):
    """Process logout and clear cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response


# Dependency to get current user for HTML routes
async def get_current_user_html(
    request: Request, db: Session = Depends(get_db)
) -> User:
    """Get current user from cookie or redirect to login."""
    user = get_user_from_cookie(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )
    return user
