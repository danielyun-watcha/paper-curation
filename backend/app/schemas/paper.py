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


class PaperSummaryData(BaseModel):
    """Schema for paper summary"""
    one_line: Optional[str] = None
    contribution: Optional[str] = None
    methodology: Optional[str] = None
    results: Optional[str] = None


class TranslationSection(BaseModel):
    """Schema for a translated section"""
    name: str
    original: str
    translated: str


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
    conference: Optional[str] = None  # Conference/venue name (e.g., ICML, NeurIPS)
    category: Category
    tags: List[TagInPaper]
    published_at: Optional[str] = None  # Publication date (YYYY-MM-DD)
    pdf_path: Optional[str] = None  # Uploaded PDF filename
    summary: Optional[PaperSummaryData] = None  # AI-generated summary
    translation: Optional[dict] = None  # Title/abstract translation
    full_translation: Optional[List[TranslationSection]] = None  # Full paper translation by sections
    full_summary: Optional[str] = None  # Full paper summary
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


class BulkImportRequest(BaseModel):
    """Schema for bulk importing papers"""
    urls: List[str] = Field(..., description="List of arXiv or DOI URLs")
    category: Optional[Category] = Field(None, description="Category for all papers (auto-predict if not provided)")


class PreviewImportRequest(BaseModel):
    """Schema for previewing papers before import"""
    urls: List[str] = Field(..., description="List of arXiv or DOI URLs")


class PreviewItem(BaseModel):
    """Preview item for a single paper"""
    url: str
    title: Optional[str] = None
    category: Category = Category.OTHER
    error: Optional[str] = None


class PreviewImportResponse(BaseModel):
    """Schema for preview import response"""
    previews: List[PreviewItem]


class BulkImportItem(BaseModel):
    """Single item for bulk import with category"""
    url: str
    category: Category


class BulkImportWithCategoriesRequest(BaseModel):
    """Schema for bulk importing papers with individual categories"""
    items: List[BulkImportItem]


class BulkImportResultItem(BaseModel):
    """Result for a single paper import"""
    url: str
    success: bool
    title: Optional[str] = None
    error: Optional[str] = None


class BulkImportResponse(BaseModel):
    """Schema for bulk import response"""
    total: int
    successful: int
    failed: int
    results: List[BulkImportResultItem]


class ScholarSearchResult(BaseModel):
    """Schema for a single Google Scholar search result"""
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    cited_by: int = 0
    pub_url: Optional[str] = None


class ScholarSearchResponse(BaseModel):
    """Schema for Google Scholar search response"""
    query: str
    results: List[ScholarSearchResult]


class ScholarAddRequest(BaseModel):
    """Schema for adding a paper from Scholar search result"""
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    category: Category = Category.OTHER


class RelatedPaperResult(BaseModel):
    """Schema for a single related paper from Semantic Scholar Recommendations"""
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    cited_by: int = 0
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None


class RelatedPapersResponse(BaseModel):
    """Schema for related papers response"""
    paper_id: str
    paper_title: str
    results: List[RelatedPaperResult]


class PdfMetadataResponse(BaseModel):
    """Schema for extracted PDF metadata"""
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    citation_count: int = 0
    source: str = "pdf"  # "pdf" or "semantic_scholar"


class ErrorResponse(BaseModel):
    """Standard error response schema for API documentation"""
    detail: str = Field(..., description="Human-readable error message")

    class Config:
        json_schema_extra = {
            "example": {"detail": "Paper not found"}
        }
