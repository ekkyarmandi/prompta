from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from .config import settings
from .database import create_tables
from auth.routes import router as auth_router
from prompts.routes import router as prompts_router
from prompts.project_routes import router as projects_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Prompta - Prompt Management API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request timing and logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log response
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")

    return response


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Prompta API",
        "version": settings.app_version,
        "docs_url": (
            "/docs" if settings.debug else "Documentation disabled in production"
        ),
    }


# Include routers
app.include_router(auth_router)
app.include_router(prompts_router)
app.include_router(projects_router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    logger.info("Starting up Prompta API...")
    create_tables()
    logger.info("Database tables created/verified")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Prompta API...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
