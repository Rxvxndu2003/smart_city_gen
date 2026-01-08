"""
FastAPI main application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import sys

from app.config import settings
from app.database import check_db_connection, init_db
from app.routers import (
    auth,
    users,
    roles,
    projects,
    layouts,
    approvals,
    ml_models,
    generation,
    validation,
    exports,
    admin,
    notifications,
    uploads,
    websocket,
    city_generator,
    blockchain,
    assistant,
    mobile,
    energy,
    structural,
    green_space
)

# Ensure logs directory exists
if settings.LOG_FILE:
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE) if settings.LOG_FILE else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Check database connection
    if not check_db_connection():
        logger.error("Database connection failed! Application may not work correctly.")
    else:
        logger.info("Database connection successful")
    
    # Initialize database tables (in production, use Alembic migrations instead)
    if settings.DEBUG:
        logger.info("Debug mode: Initializing database tables")
        try:
            init_db()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered urban planning and design system for Sri Lanka with UDA compliance",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error" if not settings.DEBUG else str(exc)}
    )


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "unhealthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_status else "disconnected"
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "disabled",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_PREFIX}/users", tags=["Users"])
app.include_router(roles.router, prefix=f"{settings.API_V1_PREFIX}/roles", tags=["Roles"])
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["Projects"])
app.include_router(layouts.router, prefix=f"{settings.API_V1_PREFIX}/layouts", tags=["Layouts"])
app.include_router(approvals.router, prefix=f"{settings.API_V1_PREFIX}/approvals", tags=["Approvals"])
app.include_router(ml_models.router, prefix=f"{settings.API_V1_PREFIX}/ml", tags=["ML Models"])
from app.routers import text_to_3d
app.include_router(text_to_3d.router, prefix=f"{settings.API_V1_PREFIX}/generation", tags=["3D Generation"])
from app.routers import floor_plan
app.include_router(floor_plan.router, prefix=f"{settings.API_V1_PREFIX}/generation", tags=["Floor Plan"])
app.include_router(generation.router, prefix=f"{settings.API_V1_PREFIX}/generation", tags=["3D Generation"])
app.include_router(validation.router, prefix=f"{settings.API_V1_PREFIX}/validation", tags=["Validation"])
app.include_router(exports.router, prefix=f"{settings.API_V1_PREFIX}/exports", tags=["Exports"])
app.include_router(city_generator.router, tags=["City Generator"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_PREFIX}/notifications", tags=["Notifications"])
app.include_router(admin.router, prefix=f"{settings.API_V1_PREFIX}/admin", tags=["Admin"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_PREFIX}/uploads", tags=["Uploads"])
app.include_router(blockchain.router, prefix=f"{settings.API_V1_PREFIX}/blockchain", tags=["Blockchain"])
app.include_router(assistant.router, prefix=f"{settings.API_V1_PREFIX}/assistant", tags=["AI Assistant"])
app.include_router(mobile.router, tags=["Mobile API"])
app.include_router(energy.router, tags=["Energy Efficiency"])
app.include_router(structural.router, tags=["Structural Integrity"])
app.include_router(green_space.router, tags=["Green Space Optimization"])
from app.routers import agents
app.include_router(agents.router, prefix=f"{settings.API_V1_PREFIX}/agents", tags=["AI Agents"])
from app.routers import interior_customization
app.include_router(interior_customization.router, prefix=f"{settings.API_V1_PREFIX}", tags=["Interior Customization"])
from app.routers import getfloorplan
app.include_router(getfloorplan.router, prefix=f"{settings.API_V1_PREFIX}", tags=["GetFloorPlan AI"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# Mount static files for serving uploaded files, exports, and 3D models
STORAGE_PATH = Path("storage")
STORAGE_PATH.mkdir(exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(STORAGE_PATH)), name="storage")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
