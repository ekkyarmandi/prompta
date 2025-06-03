from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from auth.html_routes import get_user_from_cookie
from auth.models import User, APIKey
from prompts.models import Prompt, Project


# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create router for HTML pages
router = APIRouter(tags=["html-pages"])


@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Home page - dashboard if authenticated, redirect to login if not."""
    # Check if user is authenticated via cookie
    user = get_user_from_cookie(request, db)

    if not user:
        # Redirect to login if not authenticated
        return RedirectResponse(url="/auth/html/login", status_code=302)

    # Get user stats for dashboard
    prompt_count = db.query(Prompt).filter(Prompt.user_id == user.id).count()
    project_count = db.query(Project).filter(Project.user_id == user.id).count()
    api_key_count = (
        db.query(APIKey)
        .filter(APIKey.user_id == user.id, APIKey.is_active == True)
        .count()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "prompt_count": prompt_count,
            "project_count": project_count,
            "api_key_count": api_key_count,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_redirect(request: Request):
    """Redirect to the proper login page."""
    return RedirectResponse(url="/auth/html/login", status_code=302)


@router.get("/register", response_class=HTMLResponse)
async def register_redirect(request: Request):
    """Redirect to the proper registration page."""
    return RedirectResponse(url="/auth/html/register", status_code=302)
