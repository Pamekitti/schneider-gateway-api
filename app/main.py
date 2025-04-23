from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import router as api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
    )
    
    # Add CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    application.include_router(api_router)
    
    return application

app = create_application()

@app.on_event("startup")
async def startup_event():
    """Log when the application starts."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    """Log when the application shuts down."""
    logger.info(f"Shutting down {settings.APP_NAME}")

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
