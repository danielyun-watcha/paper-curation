from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import papers, tags

settings = get_settings()

app = FastAPI(title=settings.app_name)

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
