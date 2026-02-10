from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import Response

logger = logging.getLogger(__name__)

from app.database import generate_id, now_iso
from app.models.paper import Category
from app.schemas import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperListResponse,
    ArxivImportRequest,
    DoiImportRequest,
    BulkImportRequest,
    BulkImportResponse,
    BulkImportResultItem,
    PaperSummaryData,
    PreviewImportRequest,
    PreviewItem,
    PreviewImportResponse,
    BulkImportWithCategoriesRequest,
    ScholarSearchResult,
    ScholarSearchResponse,
    ScholarAddRequest,
    RelatedPaperResult,
    RelatedPapersResponse,
    PdfMetadataResponse,
    ErrorResponse,
)
from app.services.arxiv_service import (
    get_arxiv_service,
    ArxivServiceError,
    InvalidArxivUrlError,
)
from app.services.doi_service import (
    get_doi_service,
    DoiServiceError,
    InvalidDoiUrlError,
)
from app.services.ollama_service import (
    get_ollama_service,
    OllamaServiceError,
)
from app.services.pdf_service import (
    get_pdf_service,
    PdfServiceError,
)
from app.services.scholar_service import (
    get_scholar_service,
    ScholarServiceError,
)
from app.services.semantic_scholar_service import (
    get_semantic_scholar_service,
    SemanticScholarError,
)
from app.services.paper_creation_service import (
    get_paper_creation_service,
    DuplicatePaperError,
)
from app.repositories.paper_repository import get_paper_repository

router = APIRouter()


@router.get("/years", response_model=List[int])
async def get_available_years():
    """Get list of years that have papers, sorted descending"""
    repo = get_paper_repository()
    return repo.get_years()


@router.get("/search-scholar", response_model=ScholarSearchResponse)
async def search_scholar(
    query: str = Query(..., description="Search query for Google Scholar"),
    limit: int = Query(5, ge=1, le=10, description="Number of results to return"),
):
    """Search Google Scholar for papers and return top results sorted by relevance"""
    scholar_service = get_scholar_service()

    try:
        results = await scholar_service.search(query, limit)

        return ScholarSearchResponse(
            query=query,
            results=[
                ScholarSearchResult(
                    title=r.title,
                    authors=r.authors,
                    abstract=r.abstract,
                    year=r.year,
                    url=r.url,
                    cited_by=r.cited_by,
                    pub_url=r.pub_url,
                )
                for r in results
            ]
        )
    except ScholarServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


async def _resolve_ss_paper_id(
    arxiv_id: Optional[str] = None,
    doi: Optional[str] = None,
    title: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve Semantic Scholar paper ID from identifiers.

    Priority: arxiv_id > doi > title search
    Returns SS paper ID string or None if not found.
    """
    if arxiv_id:
        return f"ArXiv:{arxiv_id}"
    if doi:
        return f"DOI:{doi}"
    if title:
        ss_service = get_semantic_scholar_service()
        try:
            ss_paper = await ss_service.search_by_title(title)
            if ss_paper:
                if ss_paper.arxiv_id:
                    return f"ArXiv:{ss_paper.arxiv_id}"
                if ss_paper.doi:
                    return f"DOI:{ss_paper.doi}"
                if ss_paper.ss_id:
                    return ss_paper.ss_id
        except SemanticScholarError:
            pass
    return None


def _build_related_papers_response(
    recommendations: list, paper_id: str, paper_title: str
) -> RelatedPapersResponse:
    """Build RelatedPapersResponse from SS recommendations"""
    return RelatedPapersResponse(
        paper_id=paper_id,
        paper_title=paper_title,
        results=[
            RelatedPaperResult(
                title=r.title,
                authors=r.authors,
                abstract=r.abstract,
                year=r.year,
                url=r.url,
                cited_by=r.citation_count,
                arxiv_id=r.arxiv_id,
                doi=r.doi,
            )
            for r in recommendations
        ],
    )


@router.get("/related/{paper_id}", response_model=RelatedPapersResponse)
async def get_related_papers(paper_id: str):
    """Find related papers for a paper in the collection using Semantic Scholar Recommendations API"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    ss_paper_id = await _resolve_ss_paper_id(
        arxiv_id=paper.get("arxiv_id"),
        doi=paper.get("doi"),
        title=paper.get("title"),
    )

    if not ss_paper_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot find this paper in Semantic Scholar. The paper needs an arXiv ID or DOI to find related papers.",
        )

    ss_service = get_semantic_scholar_service()
    try:
        recommendations = await ss_service.get_recommendations(ss_paper_id, limit=10)
        return _build_related_papers_response(recommendations, paper_id, paper["title"])
    except SemanticScholarError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/related-external", response_model=RelatedPapersResponse)
async def get_related_papers_external(
    arxiv_id: Optional[str] = Query(None),
    doi: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
):
    """Find related papers for an external paper (not in collection) using Semantic Scholar"""
    if not (arxiv_id or doi or title):
        raise HTTPException(status_code=400, detail="Provide arxiv_id, doi, or title")

    ss_paper_id = await _resolve_ss_paper_id(arxiv_id=arxiv_id, doi=doi, title=title)

    if not ss_paper_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot find this paper in Semantic Scholar.",
        )

    ss_service = get_semantic_scholar_service()
    try:
        recommendations = await ss_service.get_recommendations(ss_paper_id, limit=10)
        return _build_related_papers_response(
            recommendations, "external", title or arxiv_id or doi or ""
        )
    except SemanticScholarError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/add-from-scholar",
    response_model=PaperResponse,
    responses={409: {"model": ErrorResponse, "description": "Paper already exists"}},
)
async def add_from_scholar(request: ScholarAddRequest):
    """Add a paper directly from Google Scholar search result.

    Delegates to PaperCreationService for metadata enrichment and paper creation.
    """
    try:
        service = get_paper_creation_service()
        paper = await service.create_from_search_result(
            title=request.title,
            authors=request.authors,
            url=request.url,
            abstract=request.abstract,
            year=request.year,
        )
        return paper
    except DuplicatePaperError as e:
        raise HTTPException(status_code=409, detail=str(e))


# Keywords for automatic category prediction
CATEGORY_KEYWORDS = {
    "recsys": ["recommendation", "recommender", "collaborative filtering", "matrix factorization",
               "click-through", "ctr", "user preference", "item embedding", "ranking"],
    "nlp": ["language model", "nlp", "text", "sentiment", "translation", "summarization",
            "question answering", "named entity", "parsing", "tokeniz",
            "llm", "gpt", "chatgpt", "large language", "bert", "transformer"],
    "cv": ["image", "vision", "object detection", "segmentation", "cnn", "convolutional",
           "visual", "pixel", "face recognition", "video"],
    "rl": ["reinforcement learning", "policy gradient", "q-learning", "actor-critic",
           "reward", "markov decision", "multi-armed bandit", "exploration"],
    "ml": ["classification", "regression", "clustering", "neural network", "deep learning",
           "optimization", "gradient descent", "backpropagation", "feature"],
}


def predict_category(title: str, abstract: str) -> str:
    """Predict category based on title and abstract content"""
    text = (title + " " + abstract).lower()

    category_scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            category_scores[category] = score

    if not category_scores:
        return "other"

    # Return category with highest score
    return max(category_scores.items(), key=lambda x: x[1])[0]


# Keywords for automatic tag prediction
TAG_KEYWORDS = {
    "CTR": ["click-through", "ctr prediction", "click prediction", "ctr"],
    "Diffusion": ["diffusion", "denoising", "score matching"],
    "GCN": ["graph convolution", "gcn", "graph neural", "gnn", "node embedding"],
    "KD": ["knowledge distillation", "distillation", "teacher-student"],
    "LLM": ["llm", "large language model", "gpt", "llama", "chatgpt", "language model"],
    "MoE": ["mixture of experts", "moe", "sparse expert"],
    "RL": ["reinforcement learning", "policy gradient", "q-learning", "actor-critic"],
    "Sequential": ["sequential", "sequence model", "user sequence", "session-based", "next-item"],
    "Transformer": ["transformer", "attention mechanism", "self-attention", "multi-head"],
    "VAE": ["vae", "variational autoencoder", "variational inference", "elbo"],
}

# Keywords that MUST trigger industrial tag
INDUSTRIAL_KEYWORDS = ["a/b", "deployed", "production", "billion users", "million users", "online experiment"]


def predict_tags(title: str, abstract: str, max_tags: int = 3, min_tags: int = 2) -> List[str]:
    """Predict tags based on title and abstract content. Ensures at least min_tags are returned."""
    text = (title + " " + abstract).lower()

    # Check for industrial keywords first
    has_industrial = any(kw in text for kw in INDUSTRIAL_KEYWORDS)

    tag_scores = {}
    for tag, keywords in TAG_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            tag_scores[tag] = score

    # Sort by score and return top tags
    sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

    # If industrial is required, reserve one slot for it
    if has_industrial:
        result = [tag for tag, _ in sorted_tags[:max_tags - 1]]
        result.append("Industrial")
    else:
        result = [tag for tag, _ in sorted_tags[:max_tags]]

    # Ensure minimum tags by adding fallback tags based on content
    if len(result) < min_tags:
        fallback_tags = _get_fallback_tags(text, exclude=result)
        result.extend(fallback_tags[:min_tags - len(result)])

    # Sort alphabetically
    return sorted(result)


# Fallback tags with broader keywords for minimum tag guarantee
FALLBACK_TAG_KEYWORDS = {
    "Deep Learning": ["neural", "deep", "network", "layer", "embedding", "model", "learning"],
    "Recommendation": ["recommend", "user", "item", "rating", "preference", "personali"],
    "Graph": ["graph", "node", "edge", "network", "neighbor", "topology"],
    "Optimization": ["optim", "loss", "gradient", "convergence", "training", "parameter"],
    "Representation": ["representation", "embedding", "feature", "latent", "vector", "encoding"],
    "Contrastive": ["contrastive", "self-supervised", "augment", "negative sample"],
    "Attention": ["attention", "query", "key", "value", "context"],
    "Meta-Learning": ["meta", "few-shot", "transfer", "adaptation", "cold-start"],
}


def _get_fallback_tags(text: str, exclude: List[str]) -> List[str]:
    """Get fallback tags based on broader keyword matching"""
    tag_scores = {}
    for tag, keywords in FALLBACK_TAG_KEYWORDS.items():
        if tag in exclude:
            continue
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            tag_scores[tag] = score

    sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags]


def detect_url_type(url: str) -> str:
    """Detect if URL is arXiv or DOI"""
    url_lower = url.lower()
    if "arxiv.org" in url_lower or url_lower.strip().startswith("arxiv:"):
        return "arxiv"
    # Check for raw arXiv ID pattern (e.g., 2402.17152)
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", url.strip()):
        return "arxiv"
    return "doi"


def _build_doi_paper(paper_data, category: str, tags: list) -> dict:
    """Build paper dict from DOI paper data (shared by bulk import endpoints)"""
    now = now_iso()
    return {
        "id": generate_id(),
        "title": paper_data.title,
        "authors": paper_data.authors,
        "abstract": paper_data.abstract or "",
        "year": paper_data.year or 0,
        "arxiv_id": paper_data.arxiv_id,
        "arxiv_url": f"https://arxiv.org/abs/{paper_data.arxiv_id}" if paper_data.arxiv_id else None,
        "doi": paper_data.doi,
        "paper_url": paper_data.url,
        "conference": paper_data.conference,
        "category": category,
        "tags": tags,
        "published_at": paper_data.published_at,
        "created_at": now,
        "updated_at": now,
    }


def _build_arxiv_paper(paper_data, category: str, tags: list) -> dict:
    """Build paper dict from arXiv paper data (shared by bulk import endpoints)"""
    now = now_iso()
    return {
        "id": generate_id(),
        "title": paper_data.title,
        "authors": paper_data.authors,
        "abstract": paper_data.abstract,
        "year": paper_data.year,
        "arxiv_id": paper_data.arxiv_id,
        "arxiv_url": paper_data.arxiv_url,
        "conference": paper_data.conference,
        "category": category,
        "tags": tags,
        "published_at": paper_data.published_at,
        "created_at": now,
        "updated_at": now,
    }


async def _import_single_url(
    url: str,
    repo,
    arxiv_service,
    doi_service,
    category: Optional[str] = None,
) -> tuple[Optional[dict], Optional[str]]:
    """
    Import a single paper from URL.

    Args:
        url: arXiv or DOI URL
        repo: PaperRepository instance
        arxiv_service: ArxivService instance
        doi_service: DoiService instance
        category: Explicit category, or None to auto-predict

    Returns:
        (paper_dict, None) on success, or (None, error_message) on failure
    """
    url_type = detect_url_type(url)

    if url_type == "arxiv":
        paper_data = await arxiv_service.fetch_paper(url)
        if repo.exists_by_arxiv_id(paper_data.arxiv_id):
            return None, f"Duplicate: arXiv ID {paper_data.arxiv_id}"
        final_category = category or predict_category(paper_data.title, paper_data.abstract)
        tags = repo.get_or_create_tags(predict_tags(paper_data.title, paper_data.abstract))
        paper = _build_arxiv_paper(paper_data, final_category, tags)
    else:
        paper_data = await doi_service.fetch_paper(url)
        if paper_data.doi and repo.exists_by_doi(paper_data.doi):
            return None, f"Duplicate: DOI {paper_data.doi}"
        if not paper_data.title:
            return None, "Could not fetch paper title"
        abstract = paper_data.abstract or ""
        final_category = category or predict_category(paper_data.title, abstract)
        tags = repo.get_or_create_tags(predict_tags(paper_data.title, abstract) if abstract else [])
        paper = _build_doi_paper(paper_data, final_category, tags)

    return paper, None


@router.post("/bulk", response_model=BulkImportResponse)
async def bulk_import(request: BulkImportRequest):
    """Bulk import papers from arXiv or DOI URLs with auto category/tag prediction"""
    arxiv_service = get_arxiv_service()
    doi_service = get_doi_service()
    repo = get_paper_repository()

    results = []
    successful = 0
    failed = 0
    papers_to_add = []

    for url in request.urls:
        url = url.strip()
        if not url:
            continue

        try:
            paper, error = await _import_single_url(
                url, repo, arxiv_service, doi_service, category=request.category
            )
            if error:
                results.append(BulkImportResultItem(url=url, success=False, error=error))
                failed += 1
            else:
                papers_to_add.append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper.get("title")))
                successful += 1
        except Exception as e:
            results.append(BulkImportResultItem(url=url, success=False, error=str(e)))
            failed += 1

    if papers_to_add:
        repo.add_bulk(papers_to_add)

    return BulkImportResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.post("/preview", response_model=PreviewImportResponse)
async def preview_import(request: PreviewImportRequest):
    """Preview papers before import - fetch titles and predict categories"""
    arxiv_service = get_arxiv_service()
    doi_service = get_doi_service()

    previews = []

    for url in request.urls:
        url = url.strip()
        if not url:
            continue

        try:
            url_type = detect_url_type(url)

            if url_type == "arxiv":
                paper_data = await arxiv_service.fetch_paper(url)
                category = predict_category(paper_data.title, paper_data.abstract)
                previews.append(PreviewItem(
                    url=url,
                    title=paper_data.title,
                    category=category,
                    error=None,
                ))
            else:
                paper_data = await doi_service.fetch_paper(url)
                if not paper_data.title:
                    previews.append(PreviewItem(
                        url=url,
                        title=None,
                        category="other",
                        error="Could not fetch paper title",
                    ))
                else:
                    abstract = paper_data.abstract or ""
                    category = predict_category(paper_data.title, abstract)
                    previews.append(PreviewItem(
                        url=url,
                        title=paper_data.title,
                        category=category,
                        error=None,
                    ))

        except Exception as e:
            previews.append(PreviewItem(
                url=url,
                title=None,
                category="other",
                error=str(e),
            ))

    return PreviewImportResponse(previews=previews)


@router.post("/bulk-with-categories", response_model=BulkImportResponse)
async def bulk_import_with_categories(request: BulkImportWithCategoriesRequest):
    """Bulk import papers with individual categories (no auto-prediction)"""
    arxiv_service = get_arxiv_service()
    doi_service = get_doi_service()
    repo = get_paper_repository()

    results = []
    successful = 0
    failed = 0
    papers_to_add = []

    for item in request.items:
        url = item.url.strip()
        if not url:
            continue

        try:
            paper, error = await _import_single_url(
                url, repo, arxiv_service, doi_service, category=item.category
            )
            if error:
                results.append(BulkImportResultItem(url=url, success=False, error=error))
                failed += 1
            else:
                papers_to_add.append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper.get("title")))
                successful += 1
        except Exception as e:
            results.append(BulkImportResultItem(url=url, success=False, error=str(e)))
            failed += 1

    if papers_to_add:
        repo.add_bulk(papers_to_add)

    return BulkImportResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=results,
    )


@router.post(
    "/arxiv",
    response_model=PaperResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid arXiv URL"},
        409: {"model": ErrorResponse, "description": "Paper already exists"},
        502: {"model": ErrorResponse, "description": "arXiv API error"},
    },
)
async def import_from_arxiv(request: ArxivImportRequest):
    """Import a paper from arXiv URL"""
    arxiv_service = get_arxiv_service()
    repo = get_paper_repository()

    try:
        paper_data = await arxiv_service.fetch_paper(request.arxiv_url)
    except InvalidArxivUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ArxivServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Check for duplicate
    if repo.exists_by_arxiv_id(paper_data.arxiv_id):
        raise HTTPException(
            status_code=409,
            detail=f"Paper with arXiv ID {paper_data.arxiv_id} already exists",
        )

    # Auto-predict category if not specified (default is "other")
    category = request.category
    if category == Category.OTHER:
        category = predict_category(paper_data.title, paper_data.abstract)

    # Auto-predict tags if none provided
    tag_names = request.tags if request.tags else predict_tags(paper_data.title, paper_data.abstract)
    tags = repo.get_or_create_tags(tag_names)

    paper = _build_arxiv_paper(paper_data, category, tags)
    return repo.add(paper)


@router.post(
    "/doi",
    response_model=PaperResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid DOI URL"},
        409: {"model": ErrorResponse, "description": "Paper already exists"},
        502: {"model": ErrorResponse, "description": "DOI API error"},
    },
)
async def import_from_doi(request: DoiImportRequest):
    """Import a paper from DOI URL (ACM, IEEE, etc.)"""
    doi_service = get_doi_service()
    repo = get_paper_repository()

    try:
        paper_data = await doi_service.fetch_paper(request.url)
    except InvalidDoiUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoiServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Check for duplicate
    if paper_data.doi and repo.exists_by_doi(paper_data.doi):
        raise HTTPException(
            status_code=409,
            detail=f"Paper with DOI {paper_data.doi} already exists",
        )

    # Use manual overrides if provided, or fall back to API data
    title = request.title or paper_data.title
    abstract = request.abstract or paper_data.abstract or ""

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Title is required. Please provide it manually as the API couldn't fetch it.",
        )

    # Auto-predict category if not specified (default is "other")
    category = request.category
    if category == Category.OTHER and abstract:
        category = predict_category(title, abstract)

    # Auto-predict tags if none provided
    tag_names = request.tags
    if not tag_names and abstract:
        tag_names = predict_tags(title, abstract)

    tags = repo.get_or_create_tags(tag_names)
    now = now_iso()

    paper = {
        "id": generate_id(),
        "title": title,
        "authors": paper_data.authors,
        "abstract": abstract,
        "year": paper_data.year or 0,
        "arxiv_id": paper_data.arxiv_id,
        "arxiv_url": f"https://arxiv.org/abs/{paper_data.arxiv_id}" if paper_data.arxiv_id else None,
        "doi": paper_data.doi,
        "paper_url": paper_data.url,
        "conference": paper_data.conference,
        "category": category,
        "tags": tags,
        "published_at": paper_data.published_at,
        "created_at": now,
        "updated_at": now,
    }

    return repo.add(paper)


@router.post("", response_model=PaperResponse)
async def create_paper(paper_in: PaperCreate):
    """Manually create a paper"""
    repo = get_paper_repository()

    # Auto-predict tags if none provided
    tag_names = paper_in.tags
    if not tag_names:
        tag_names = predict_tags(paper_in.title, paper_in.abstract)

    tags = repo.get_or_create_tags(tag_names)
    now = now_iso()

    paper = {
        "id": generate_id(),
        "title": paper_in.title,
        "authors": paper_in.authors,
        "abstract": paper_in.abstract,
        "year": paper_in.year,
        "arxiv_id": None,
        "arxiv_url": None,
        "category": paper_in.category,
        "tags": tags,
        "created_at": now,
        "updated_at": now,
    }

    return repo.add(paper)


@router.get("", response_model=PaperListResponse)
async def list_papers(
    search: Optional[str] = Query(None),
    category: Optional[Category] = Query(None),
    tags: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List papers with search and filters"""
    repo = get_paper_repository()

    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    papers, total, pages = repo.find_all_filtered(
        search=search,
        category=category.value if category else None,
        year=year,
        tags=tag_list,
        page=page,
        limit=limit,
    )

    return {
        "items": papers,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/{paper_id}",
    response_model=PaperResponse,
    responses={404: {"model": ErrorResponse, "description": "Paper not found"}},
)
async def get_paper(paper_id: str):
    """Get a paper by ID"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper


@router.put(
    "/{paper_id}",
    response_model=PaperResponse,
    responses={404: {"model": ErrorResponse, "description": "Paper not found"}},
)
async def update_paper(paper_id: str, paper_in: PaperUpdate):
    """Update a paper"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Build updates dict
    updates = {}
    if paper_in.title is not None:
        updates["title"] = paper_in.title
    if paper_in.authors is not None:
        updates["authors"] = paper_in.authors
    if paper_in.abstract is not None:
        updates["abstract"] = paper_in.abstract
    if paper_in.year is not None:
        updates["year"] = paper_in.year
    if paper_in.category is not None:
        updates["category"] = paper_in.category
    if paper_in.tags is not None:
        updates["tags"] = repo.get_or_create_tags(paper_in.tags)

    return repo.update(paper_id, updates)


@router.delete(
    "/{paper_id}",
    responses={404: {"model": ErrorResponse, "description": "Paper not found"}},
)
async def delete_paper(paper_id: str):
    """Delete a paper"""
    repo = get_paper_repository()

    if not repo.delete(paper_id):
        raise HTTPException(status_code=404, detail="Paper not found")

    return {"message": "Paper deleted successfully"}


@router.post("/{paper_id}/summary", response_model=PaperSummaryData)
async def generate_summary(paper_id: str):
    """Generate AI summary for a paper using Ollama"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check if abstract exists
    if not paper.get("abstract"):
        raise HTTPException(status_code=400, detail="Paper has no abstract to summarize")

    ollama_service = get_ollama_service()

    try:
        summary = await ollama_service.generate_summary(
            title=paper["title"],
            abstract=paper["abstract"],
        )

        # Save summary to paper
        summary_data = {
            "one_line": summary.one_line,
            "contribution": summary.contribution,
            "methodology": summary.methodology,
            "results": summary.results,
        }
        repo.update(paper_id, {"summary": summary_data})

        return summary_data

    except OllamaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{paper_id}/translate")
async def translate_paper(paper_id: str):
    """Translate paper title and abstract to Korean using Ollama"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.get("abstract"):
        raise HTTPException(status_code=400, detail="Paper has no abstract to translate")

    ollama_service = get_ollama_service()

    try:
        translation = await ollama_service.translate_to_korean(
            title=paper["title"],
            abstract=paper["abstract"],
        )

        # Save translation to paper
        repo.update(paper_id, {"translation": translation})

        return {
            "paper_id": paper_id,
            "original_title": paper["title"],
            "original_abstract": paper["abstract"],
            "translated_title": translation.get("title", ""),
            "translated_abstract": translation.get("abstract", ""),
        }

    except OllamaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{paper_id}/translate-full")
async def translate_full_paper(paper_id: str):
    """Translate full paper PDF to Korean using PyMuPDF + DeepL"""
    from app.services.deepl_service import get_deepl_service, DeepLServiceError

    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    arxiv_id = paper.get("arxiv_id")
    pdf_path = paper.get("pdf_path")

    if not arxiv_id and not pdf_path:
        raise HTTPException(status_code=400, detail="No PDF source available for this paper")

    pdf_service = get_pdf_service()
    deepl_service = get_deepl_service()
    ollama_service = get_ollama_service()

    if deepl_service is None:
        raise HTTPException(status_code=500, detail="DeepL API key not configured")

    try:
        # Extract text from PDF using improved PyMuPDF extraction
        paper_text = await pdf_service.get_paper_text(arxiv_id=arxiv_id, pdf_path=pdf_path)

        # Parse sections using improved parser
        sections = ollama_service._parse_paper_sections(paper_text)

        # Filter and translate each section with DeepL
        translated_sections = []
        for section in sections:
            name = section.get("name", "")
            content = section.get("content", "")

            # Skip empty or reference sections
            if not content.strip() or len(content) < 50:
                continue

            if name.lower() in ["references", "bibliography", "acknowledgments", "appendix"]:
                translated_sections.append({
                    "name": name,
                    "original": content,
                    "translated": "[참고문헌 생략]" if "reference" in name.lower() else "[생략]"
                })
                continue

            # Filter tables/figures before translation
            filtered_content = ollama_service._filter_tables_and_figures(content)

            if not filtered_content.strip():
                continue

            try:
                translated = await deepl_service.translate(filtered_content)
                translated_sections.append({
                    "name": name,
                    "original": content,
                    "translated": translated
                })
            except DeepLServiceError as e:
                translated_sections.append({
                    "name": name,
                    "original": content,
                    "translated": f"[번역 실패: {str(e)}]"
                })

        # Save full translation to paper
        repo.update(paper_id, {"full_translation": translated_sections})

        return {
            "paper_id": paper_id,
            "sections": translated_sections,
        }

    except PdfServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except DeepLServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{paper_id}/summarize-full")
async def summarize_full_paper(paper_id: str):
    """Summarize full paper PDF in Korean using Ollama"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    arxiv_id = paper.get("arxiv_id")
    paper_url = paper.get("paper_url")

    if not arxiv_id and not paper_url:
        raise HTTPException(status_code=400, detail="No PDF source available for this paper")

    pdf_service = get_pdf_service()
    ollama_service = get_ollama_service()

    try:
        # Extract text from PDF
        paper_text = await pdf_service.get_paper_text(arxiv_id=arxiv_id, paper_url=paper_url)

        # Summarize with Ollama
        summary = await ollama_service.summarize_full_paper(paper_text)

        # Note: Summary is NOT saved to backend anymore
        # Frontend saves it to localStorage for per-browser storage

        return {
            "paper_id": paper_id,
            "summary": summary,
        }

    except PdfServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except OllamaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{paper_id}/pdf")
async def get_paper_pdf(paper_id: str):
    """Proxy PDF for a paper to avoid CORS issues"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Check for uploaded PDF first
    pdf_path = paper.get("pdf_path")
    if pdf_path:
        full_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "uploads",
            pdf_path
        )
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                pdf_bytes = f.read()
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename={paper_id}.pdf",
                    "Access-Control-Allow-Origin": "*",
                }
            )

    arxiv_id = paper.get("arxiv_id")
    paper_url = paper.get("paper_url")

    if not arxiv_id and not paper_url:
        raise HTTPException(status_code=400, detail="No PDF source available")

    pdf_service = get_pdf_service()

    try:
        pdf_bytes = await pdf_service.download_pdf(
            f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else paper_url
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename={paper_id}.pdf",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except PdfServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


# PDF upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extract_doi_from_text(text: str) -> Optional[str]:
    """Try to extract a DOI from text (e.g. URL containing doi.org or 10.xxxx pattern)"""
    # Match DOI pattern: 10.xxxx/xxxxx
    match = re.search(r'(10\.\d{4,}/[^\s,]+)', text)
    if match:
        return match.group(1).rstrip('.')
    return None


def _ss_paper_to_response(ss_paper) -> PdfMetadataResponse:
    return PdfMetadataResponse(
        title=ss_paper.title,
        authors=ss_paper.authors,
        abstract=ss_paper.abstract,
        year=ss_paper.year,
        url=ss_paper.url,
        doi=ss_paper.doi,
        arxiv_id=ss_paper.arxiv_id,
        citation_count=ss_paper.citation_count,
        source="semantic_scholar",
    )


@router.post("/extract-pdf-metadata", response_model=PdfMetadataResponse)
async def extract_pdf_metadata(
    pdf: UploadFile = File(...),
):
    """Extract metadata from a PDF file using title extraction and Semantic Scholar lookup"""
    if not pdf.filename or not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    pdf_content = await pdf.read()

    # Extract title from PDF
    pdf_service = get_pdf_service()
    extracted_title = pdf_service.extract_title_from_pdf(pdf_content)

    if not extracted_title:
        # Fallback to filename
        extracted_title = pdf.filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')

    ss_service = get_semantic_scholar_service()

    # If extracted title contains a DOI, try DOI lookup first
    doi = _extract_doi_from_text(extracted_title)
    if doi:
        try:
            ss_paper = await ss_service.get_by_doi(doi)
            if ss_paper:
                return _ss_paper_to_response(ss_paper)
        except SemanticScholarError:
            pass
        # DOI lookup failed, use filename as title instead
        extracted_title = pdf.filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')

    # Search Semantic Scholar by title
    try:
        ss_paper = await ss_service.search_by_title(extracted_title)
        if ss_paper:
            return _ss_paper_to_response(ss_paper)
    except SemanticScholarError:
        pass  # Fall back to PDF-only data

    return PdfMetadataResponse(
        title=extracted_title,
        source="pdf",
    )


@router.post("/upload-pdf", response_model=PaperResponse)
async def upload_pdf_paper(
    pdf: UploadFile = File(...),
    title: str = Form(""),  # Optional - will extract from PDF if not provided
    authors: str = Form(""),  # Comma-separated
    abstract: str = Form(""),
    year: int = Form(2024),
    category: str = Form("other"),
    tags: str = Form(""),  # Comma-separated
):
    """Create a paper from uploaded PDF file"""
    # Validate file type
    if not pdf.filename or not pdf.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Read PDF content
    pdf_content = await pdf.read()
    await pdf.seek(0)  # Reset for later saving

    # Extract title from PDF if not provided
    pdf_service = get_pdf_service()
    final_title = title.strip()
    if not final_title:
        extracted_title = pdf_service.extract_title_from_pdf(pdf_content)
        if extracted_title:
            final_title = extracted_title
        else:
            # Fallback to filename
            final_title = pdf.filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')

    repo = get_paper_repository()

    # Parse authors and tags
    author_list = [a.strip() for a in authors.split(",") if a.strip()] if authors else []
    tag_names = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Auto-predict tags if not provided
    if not tag_names and abstract:
        tag_names = predict_tags(final_title, abstract)

    tags_data = repo.get_or_create_tags(tag_names)
    now = now_iso()

    # Generate paper ID
    paper_id = generate_id()

    # Save PDF file
    pdf_filename = f"{paper_id}.pdf"
    pdf_path_full = os.path.join(UPLOAD_DIR, pdf_filename)

    try:
        with open(pdf_path_full, "wb") as buffer:
            buffer.write(pdf_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save PDF: {str(e)}")

    # Auto-predict category if not provided or "other"
    cat = category if category in [c.value for c in Category] else "other"
    if cat == "other" and abstract:
        cat = predict_category(final_title, abstract)

    paper = {
        "id": paper_id,
        "title": final_title,
        "authors": author_list,
        "abstract": abstract,
        "year": year,
        "arxiv_id": None,
        "arxiv_url": None,
        "doi": None,
        "paper_url": None,
        "pdf_path": pdf_filename,  # Store relative path
        "conference": None,
        "category": cat,
        "tags": tags_data,
        "published_at": None,
        "created_at": now,
        "updated_at": now,
    }

    return repo.add(paper)


@router.get("/{paper_id}/pdf-file")
async def get_uploaded_pdf(paper_id: str):
    """Get uploaded PDF file for a paper"""
    repo = get_paper_repository()
    paper = repo.find_by_id(paper_id)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_path = paper.get("pdf_path")
    if not pdf_path:
        raise HTTPException(status_code=404, detail="No uploaded PDF for this paper")

    # Sanitize path to prevent directory traversal
    pdf_path = os.path.basename(pdf_path)
    full_path = os.path.join(UPLOAD_DIR, pdf_path)
    if not full_path.startswith(os.path.abspath(UPLOAD_DIR)) or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    with open(full_path, "rb") as f:
        pdf_bytes = f.read()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={paper_id}.pdf",
            "Access-Control-Allow-Origin": "*",
        }
    )


SEMANTIC_SCHOLAR_DELAY = 3.5  # Semantic Scholar: ~100 req/5min without API key


@router.post("/refresh-conferences")
async def refresh_conferences():
    """Refresh conference info for papers with missing or 'arXiv' conference using Semantic Scholar API"""
    repo = get_paper_repository()
    arxiv_service = get_arxiv_service()
    data = repo.get_raw_data()

    papers_to_update = [
        p for p in data["papers"]
        if p.get("arxiv_id") and (
            not p.get("conference")
            or p.get("conference", "").lower().startswith("arxiv")
        )
    ]

    updated = 0
    errors = 0

    for paper in papers_to_update:
        try:
            conference = await arxiv_service._fetch_conference(paper["arxiv_id"])
            if conference:
                paper["conference"] = conference
                paper["updated_at"] = now_iso()
                updated += 1
            await asyncio.sleep(SEMANTIC_SCHOLAR_DELAY)
        except Exception as e:
            logger.warning(f"Failed to refresh conference for {paper.get('arxiv_id')}: {e}")
            errors += 1

    if updated > 0:
        repo.save_all()

    return {
        "total_checked": len(papers_to_update),
        "updated": updated,
        "errors": errors,
    }


@router.post("/refresh-arxiv-ids")
async def refresh_arxiv_ids():
    """Find and fill arXiv IDs for DOI papers using Semantic Scholar API"""
    repo = get_paper_repository()
    data = repo.get_raw_data()

    papers_to_update = [
        p for p in data["papers"]
        if p.get("doi") and not p.get("arxiv_id")
    ]

    updated = 0
    errors = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        for paper in papers_to_update:
            try:
                response = await client.get(
                    f"https://api.semanticscholar.org/graph/v1/paper/DOI:{paper['doi']}",
                    params={"fields": "externalIds"},
                )
                if response.status_code == 429:
                    logger.warning("Semantic Scholar rate limit hit, waiting 60s...")
                    await asyncio.sleep(60)
                    continue
                if response.status_code == 200:
                    ext_ids = response.json().get("externalIds") or {}
                    arxiv_id = ext_ids.get("ArXiv")
                    if arxiv_id:
                        paper["arxiv_id"] = arxiv_id
                        paper["arxiv_url"] = f"https://arxiv.org/abs/{arxiv_id}"
                        paper["updated_at"] = now_iso()
                        updated += 1
                await asyncio.sleep(SEMANTIC_SCHOLAR_DELAY)
            except Exception as e:
                logger.warning(f"Failed to refresh arxiv_id for DOI {paper.get('doi')}: {e}")
                errors += 1

    if updated > 0:
        repo.save_all()

    return {
        "total_checked": len(papers_to_update),
        "updated": updated,
        "errors": errors,
    }


# ============================================
# Text Translation (for selected text)
# ============================================

from pydantic import BaseModel

class TranslateTextRequest(BaseModel):
    text: str
    target_lang: str = "KO"

class TranslateTextResponse(BaseModel):
    original: str
    translated: str

@router.post("/translate-text", response_model=TranslateTextResponse)
async def translate_text(request: TranslateTextRequest):
    """Translate selected text using DeepL API"""
    from app.services.deepl_service import get_deepl_service, DeepLServiceError

    deepl_service = get_deepl_service()

    if deepl_service is None:
        raise HTTPException(status_code=500, detail="DeepL API key not configured")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    # Limit text length to prevent abuse
    if len(request.text) > 10000:
        raise HTTPException(status_code=400, detail="Text too long (max 10000 characters)")

    try:
        translated = await deepl_service.translate(request.text, target_lang=request.target_lang)
        return TranslateTextResponse(
            original=request.text,
            translated=translated
        )
    except DeepLServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
