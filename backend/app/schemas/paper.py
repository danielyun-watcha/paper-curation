from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.paper import Category


class TagBase(BaseModel):
    name: str


class TagInPaper(TagBase):
    id: UUID

    class Config:
        from_attributes = True


class PaperBase(BaseModel):
    title: str = Field(..., max_length=500)
    authors: List[str]
    abstract: str
    year: int = Field(..., ge=1900, le=2100)
    category: Category = Category.OTHER


class PaperCreate(PaperBase):
    """Schema for manually creating a paper"""
    tags: List[str] = Field(default_factory=list)


class ArxivImportRequest(BaseModel):
    """Schema for importing a paper from arXiv"""
    arxiv_url: str = Field(..., description="arXiv URL (e.g., https://arxiv.org/abs/2402.17152)")
    category: Category = Category.OTHER
    tags: List[str] = Field(default_factory=list)


class DoiImportRequest(BaseModel):
    """Schema for importing a paper from DOI (ACM, IEEE, etc.)"""
    url: str = Field(..., description="Paper URL (ACM, IEEE, or DOI URL)")
    category: Category = Category.OTHER
    tags: List[str] = Field(default_factory=list)
    # Optional manual overrides (for when API doesn't return data)
    title: Optional[str] = None
    abstract: Optional[str] = None


class PaperUpdate(BaseModel):
    """Schema for updating a paper"""
    title: Optional[str] = Field(None, max_length=500)
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    category: Optional[Category] = None
    tags: Optional[List[str]] = None


class PaperResponse(BaseModel):
    """Schema for paper response"""
    id: UUID
    title: str
    authors: List[str]
    abstract: str
    year: int
    arxiv_id: Optional[str] = None
    arxiv_url: Optional[str] = None
    doi: Optional[str] = None
    paper_url: Optional[str] = None  # For ACM, IEEE, etc.
    category: Category
    tags: List[TagInPaper]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    """Schema for paginated paper list response"""
    items: List[PaperResponse]
    total: int
    page: int
    limit: int
    pages: int
