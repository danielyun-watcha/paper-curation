from __future__ import annotations

from typing import List, Optional
from math import ceil

from fastapi import APIRouter, HTTPException, Query

from app.database import load_data, save_data, generate_id, now_iso
from app.models.paper import Category
from app.schemas import (
    PaperCreate,
    PaperUpdate,
    PaperResponse,
    PaperListResponse,
    ArxivImportRequest,
    DoiImportRequest,
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

router = APIRouter()

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


def predict_tags(title: str, abstract: str, max_tags: int = 3) -> List[str]:
    """Predict tags based on title and abstract content"""
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

    # Sort alphabetically
    return sorted(result)


def get_or_create_tags(data: dict, tag_names: List[str]) -> List[dict]:
    """Get existing tags or create new ones, sorted alphabetically"""
    result_tags = []
    for name in sorted(tag_names):  # Sort alphabetically
        name = name.strip()
        if not name:
            continue

        # Find existing tag (case-insensitive search)
        existing = next((t for t in data["tags"] if t["name"].lower() == name.lower()), None)
        if existing:
            result_tags.append(existing)
        else:
            # Create new tag
            new_tag = {"id": generate_id(), "name": name}
            data["tags"].append(new_tag)
            result_tags.append(new_tag)

    return result_tags


@router.post("/arxiv", response_model=PaperResponse)
async def import_from_arxiv(request: ArxivImportRequest):
    """Import a paper from arXiv URL"""
    arxiv_service = get_arxiv_service()

    try:
        paper_data = await arxiv_service.fetch_paper(request.arxiv_url)
    except InvalidArxivUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ArxivServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    data = load_data()

    # Check for duplicate
    if any(p.get("arxiv_id") == paper_data.arxiv_id for p in data["papers"]):
        raise HTTPException(
            status_code=409,
            detail=f"Paper with arXiv ID {paper_data.arxiv_id} already exists",
        )

    # Auto-predict tags if none provided
    tag_names = request.tags
    if not tag_names:
        tag_names = predict_tags(paper_data.title, paper_data.abstract)

    tags = get_or_create_tags(data, tag_names)
    now = now_iso()

    paper = {
        "id": generate_id(),
        "title": paper_data.title,
        "authors": paper_data.authors,
        "abstract": paper_data.abstract,
        "year": paper_data.year,
        "arxiv_id": paper_data.arxiv_id,
        "arxiv_url": paper_data.arxiv_url,
        "conference": paper_data.conference,
        "category": request.category,
        "tags": tags,
        "published_at": paper_data.published_at,
        "created_at": now,
        "updated_at": now,
    }

    data["papers"].append(paper)
    save_data(data)

    return paper


@router.post("/doi", response_model=PaperResponse)
async def import_from_doi(request: DoiImportRequest):
    """Import a paper from DOI URL (ACM, IEEE, etc.)"""
    doi_service = get_doi_service()

    try:
        paper_data = await doi_service.fetch_paper(request.url)
    except InvalidDoiUrlError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DoiServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    data = load_data()

    # Check for duplicate
    if paper_data.doi and any(p.get("doi") == paper_data.doi for p in data["papers"]):
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

    # Auto-predict tags if none provided
    tag_names = request.tags
    if not tag_names and abstract:
        tag_names = predict_tags(title, abstract)

    tags = get_or_create_tags(data, tag_names)
    now = now_iso()

    paper = {
        "id": generate_id(),
        "title": title,
        "authors": paper_data.authors,
        "abstract": abstract,
        "year": paper_data.year or 0,
        "arxiv_id": None,
        "arxiv_url": None,
        "doi": paper_data.doi,
        "paper_url": paper_data.url,
        "conference": paper_data.conference,
        "category": request.category,
        "tags": tags,
        "published_at": paper_data.published_at,
        "created_at": now,
        "updated_at": now,
    }

    data["papers"].append(paper)
    save_data(data)

    return paper


@router.post("", response_model=PaperResponse)
async def create_paper(paper_in: PaperCreate):
    """Manually create a paper"""
    data = load_data()

    # Auto-predict tags if none provided
    tag_names = paper_in.tags
    if not tag_names:
        tag_names = predict_tags(paper_in.title, paper_in.abstract)

    tags = get_or_create_tags(data, tag_names)
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

    data["papers"].append(paper)
    save_data(data)

    return paper


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
    data = load_data()
    papers = data["papers"]

    # Apply filters
    if search:
        search_lower = search.lower()
        papers = [
            p for p in papers
            if search_lower in p["title"].lower()
            or search_lower in p["abstract"].lower()
            or (p.get("conference") and search_lower in p["conference"].lower())
        ]

    if category:
        papers = [p for p in papers if p["category"] == category]

    if year:
        papers = [p for p in papers if p["year"] == year]

    if tags:
        tag_names = [t.strip().lower() for t in tags.split(",") if t.strip()]
        if tag_names:
            papers = [
                p for p in papers
                if any(t["name"].lower() in tag_names for t in p["tags"])
            ]

    # Sort by updated_at descending (most recent first)
    papers = sorted(papers, key=lambda p: p["updated_at"], reverse=True)

    total = len(papers)
    pages = ceil(total / limit) if total > 0 else 0

    # Paginate
    start = (page - 1) * limit
    end = start + limit
    papers = papers[start:end]

    return {
        "items": papers,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str):
    """Get a paper by ID"""
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    return paper


@router.put("/{paper_id}", response_model=PaperResponse)
async def update_paper(paper_id: str, paper_in: PaperUpdate):
    """Update a paper"""
    data = load_data()
    paper_idx = next((i for i, p in enumerate(data["papers"]) if p["id"] == paper_id), None)

    if paper_idx is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = data["papers"][paper_idx]

    # Update fields
    if paper_in.title is not None:
        paper["title"] = paper_in.title
    if paper_in.authors is not None:
        paper["authors"] = paper_in.authors
    if paper_in.abstract is not None:
        paper["abstract"] = paper_in.abstract
    if paper_in.year is not None:
        paper["year"] = paper_in.year
    if paper_in.category is not None:
        paper["category"] = paper_in.category
    if paper_in.tags is not None:
        paper["tags"] = get_or_create_tags(data, paper_in.tags)

    paper["updated_at"] = now_iso()
    save_data(data)

    return paper


@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    """Delete a paper"""
    data = load_data()
    paper_idx = next((i for i, p in enumerate(data["papers"]) if p["id"] == paper_id), None)

    if paper_idx is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    data["papers"].pop(paper_idx)
    save_data(data)

    return {"message": "Paper deleted successfully"}
