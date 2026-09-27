"""
FastAPI Application for Shapir Recordings System
Phase 1, 2, & 3: Foundation + Authentication + Upload + Summarization
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging
import os

from config import settings
from database import init_db, get_db
from routes.auth import router as auth_router
from routes.recordings import router as recordings_router
from routes.templates import router as templates_router
from routes.summaries import router as summaries_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting Shapir Recordings API (Phase 3)...")
    try:
        init_db()
        logger.info("Database initialized successfully")

        # Seed default templates if needed
        from database import SessionLocal
        from services.template import template_service
        db = SessionLocal()
        try:
            count = template_service.seed_default_templates(db, admin_user_id=None)
            if count > 0:
                logger.info(f"Seeded {count} default templates")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Shapir Recordings API...")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description="Speech-to-text and summarization platform for Shapir Engineering",
    version="3.0.0",  # Phase 3 version
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(recordings_router)
app.include_router(templates_router)
app.include_router(summaries_router)


# Health check endpoint
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint - verify API and database connectivity"""
    try:
        # Try a simple database query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "api_version": "3.0.0",
            "database": "connected",
            "phase": "3 - Summarization"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "api": settings.API_TITLE,
        "version": "3.0.0",
        "phase": "3 - Summarization & Templates",
        "status": "running",
        "features": [
            "User Authentication (AD/LDAP)",
            "Audio File Upload",
            "Whisper Transcription",
            "GPT-4 Summarization",
            "Template Management",
            "Document Generation (PDF/DOCX/XLSX/TXT)",
            "Audit Logging"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "auth": "/api/auth",
            "recordings": "/api/recordings",
            "templates": "/api/templates",
            "summaries": "/api/summaries"
        }
    }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main_phase3:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
