import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import papers, tags
from app.services.cache_service import start_cache_cleanup_scheduler
from app.utils.http_client import HttpClientManager

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks on app startup"""
    # Initialize SQLite database
    init_db()

    asyncio.create_task(start_cache_cleanup_scheduler())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown"""
    await HttpClientManager.close_all()

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers.router, prefix="/api/papers", tags=["papers"])
app.include_router(tags.router, prefix="/api/tags", tags=["tags"])


@app.get("/")
async def root():
    return {"message": "Paper Curation API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
