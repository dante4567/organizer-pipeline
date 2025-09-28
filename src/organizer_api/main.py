"""
Main FastAPI application with security, monitoring, and proper architecture.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
import uvicorn

from organizer_core.config import get_settings, Settings
from organizer_core.config.security import SecurityConfig
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.security import SecurityMiddleware
from .routers import calendar, tasks, contacts, llm, files
from .database.connection import init_database, close_database
from .services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.version}")

    # Initialize database
    await init_database()
    logger.info("Database initialized")

    # Initialize LLM service
    llm_service = LLMService()
    await llm_service.initialize()
    app.state.llm_service = llm_service
    logger.info(f"LLM service initialized with provider: {settings.llm.provider}")

    yield

    # Cleanup
    await close_database()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Secure personal assistant with LLM integration",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )

    # Security middleware
    app.add_middleware(SecurityMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=SecurityConfig.validate_cors_origins(settings.security.allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.add_middleware(RateLimitMiddleware)

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"]
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {process_time:.3f}s"
        )
        return response

    # Include routers
    app.include_router(calendar.router, prefix="/api/v1/calendar", tags=["Calendar"])
    app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
    app.include_router(contacts.router, prefix="/api/v1/contacts", tags=["Contacts"])
    app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
    app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM"])

    # Health check endpoint
    @app.get("/health", response_model=Dict[str, Any])
    async def health_check():
        """Health check endpoint."""
        settings = get_settings()
        return {
            "status": "healthy",
            "version": settings.version,
            "timestamp": time.time(),
            "environment": "development" if settings.debug else "production"
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        settings = get_settings()
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.version,
            "docs": "/docs" if settings.debug else "Documentation disabled in production"
        }

    # Global exception handler
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Internal server error",
                    "status_code": 500,
                    "path": str(request.url.path)
                }
            }
        )

    return app


# Create the application instance
app = create_app()


def run_server():
    """Run the server with proper configuration."""
    settings = get_settings()

    uvicorn.run(
        "organizer_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    run_server()