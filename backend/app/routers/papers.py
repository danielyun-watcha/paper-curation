from __future__ import annotations

from typing import List, Optional
from math import ceil

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import Response
import os
import shutil

from app.database import load_data, save_data, generate_id, now_iso
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

router = APIRouter()


@router.get("/years", response_model=List[int])
async def get_available_years():
    """Get list of years that have papers, sorted descending"""
    data = load_data()
    years = sorted(set(p["year"] for p in data["papers"] if p.get("year")), reverse=True)
    return years


# Keywords for automatic category prediction
CATEGORY_KEYWORDS = {
    "recsys": ["recommendation", "recommender", "collaborative filtering", "matrix factorization",
               "click-through", "ctr", "user preference", "item embedding", "ranking"],
    "nlp": ["language model", "nlp", "text", "sentiment", "translation", "summarization",
            "question answering", "named entity", "parsing", "tokeniz"],
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


def detect_url_type(url: str) -> str:
    """Detect if URL is arXiv or DOI"""
    url_lower = url.lower()
    if "arxiv.org" in url_lower or url_lower.strip().startswith("arxiv:"):
        return "arxiv"
    # Check for raw arXiv ID pattern (e.g., 2402.17152)
    import re
    if re.match(r"^\d{4}\.\d{4,5}(v\d+)?$", url.strip()):
        return "arxiv"
    return "doi"


@router.post("/bulk", response_model=BulkImportResponse)
async def bulk_import(request: BulkImportRequest):
    """Bulk import papers from arXiv or DOI URLs with auto category/tag prediction"""
    arxiv_service = get_arxiv_service()
    doi_service = get_doi_service()
    data = load_data()

    results = []
    successful = 0
    failed = 0

    for url in request.urls:
        url = url.strip()
        if not url:
            continue

        try:
            url_type = detect_url_type(url)

            if url_type == "arxiv":
                # Import from arXiv
                paper_data = await arxiv_service.fetch_paper(url)

                # Check for duplicate
                if any(p.get("arxiv_id") == paper_data.arxiv_id for p in data["papers"]):
                    results.append(BulkImportResultItem(
                        url=url, success=False, error=f"Duplicate: arXiv ID {paper_data.arxiv_id}"
                    ))
                    failed += 1
                    continue

                # Use provided category or auto-predict
                category = request.category or predict_category(paper_data.title, paper_data.abstract)
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
                    "category": category,
                    "tags": tags,
                    "published_at": paper_data.published_at,
                    "created_at": now,
                    "updated_at": now,
                }
                data["papers"].append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper_data.title))
                successful += 1

            else:
                # Import from DOI
                paper_data = await doi_service.fetch_paper(url)

                # Check for duplicate
                if paper_data.doi and any(p.get("doi") == paper_data.doi for p in data["papers"]):
                    results.append(BulkImportResultItem(
                        url=url, success=False, error=f"Duplicate: DOI {paper_data.doi}"
                    ))
                    failed += 1
                    continue

                if not paper_data.title:
                    results.append(BulkImportResultItem(
                        url=url, success=False, error="Could not fetch paper title"
                    ))
                    failed += 1
                    continue

                abstract = paper_data.abstract or ""

                # Use provided category or auto-predict
                category = request.category or predict_category(paper_data.title, abstract)
                tag_names = predict_tags(paper_data.title, abstract) if abstract else []
                tags = get_or_create_tags(data, tag_names)
                now = now_iso()

                paper = {
                    "id": generate_id(),
                    "title": paper_data.title,
                    "authors": paper_data.authors,
                    "abstract": abstract,
                    "year": paper_data.year or 0,
                    "arxiv_id": None,
                    "arxiv_url": None,
                    "doi": paper_data.doi,
                    "paper_url": paper_data.url,
                    "conference": paper_data.conference,
                    "category": category,
                    "tags": tags,
                    "published_at": paper_data.published_at,
                    "created_at": now,
                    "updated_at": now,
                }
                data["papers"].append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper_data.title))
                successful += 1

        except Exception as e:
            results.append(BulkImportResultItem(url=url, success=False, error=str(e)))
            failed += 1

    # Save all imported papers
    if successful > 0:
        save_data(data)

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
    """Bulk import papers with individual categories"""
    arxiv_service = get_arxiv_service()
    doi_service = get_doi_service()
    data = load_data()

    results = []
    successful = 0
    failed = 0

    for item in request.items:
        url = item.url.strip()
        category = item.category

        if not url:
            continue

        try:
            url_type = detect_url_type(url)

            if url_type == "arxiv":
                paper_data = await arxiv_service.fetch_paper(url)

                # Check for duplicate
                if any(p.get("arxiv_id") == paper_data.arxiv_id for p in data["papers"]):
                    results.append(BulkImportResultItem(
                        url=url, success=False, error=f"Duplicate: arXiv ID {paper_data.arxiv_id}"
                    ))
                    failed += 1
                    continue

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
                    "category": category,
                    "tags": tags,
                    "published_at": paper_data.published_at,
                    "created_at": now,
                    "updated_at": now,
                }
                data["papers"].append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper_data.title))
                successful += 1

            else:
                paper_data = await doi_service.fetch_paper(url)

                # Check for duplicate
                if paper_data.doi and any(p.get("doi") == paper_data.doi for p in data["papers"]):
                    results.append(BulkImportResultItem(
                        url=url, success=False, error=f"Duplicate: DOI {paper_data.doi}"
                    ))
                    failed += 1
                    continue

                if not paper_data.title:
                    results.append(BulkImportResultItem(
                        url=url, success=False, error="Could not fetch paper title"
                    ))
                    failed += 1
                    continue

                abstract = paper_data.abstract or ""
                tag_names = predict_tags(paper_data.title, abstract) if abstract else []
                tags = get_or_create_tags(data, tag_names)
                now = now_iso()

                paper = {
                    "id": generate_id(),
                    "title": paper_data.title,
                    "authors": paper_data.authors,
                    "abstract": abstract,
                    "year": paper_data.year or 0,
                    "arxiv_id": None,
                    "arxiv_url": None,
                    "doi": paper_data.doi,
                    "paper_url": paper_data.url,
                    "conference": paper_data.conference,
                    "category": category,
                    "tags": tags,
                    "published_at": paper_data.published_at,
                    "created_at": now,
                    "updated_at": now,
                }
                data["papers"].append(paper)
                results.append(BulkImportResultItem(url=url, success=True, title=paper_data.title))
                successful += 1

        except Exception as e:
            results.append(BulkImportResultItem(url=url, success=False, error=str(e)))
            failed += 1

    # Save all imported papers
    if successful > 0:
        save_data(data)

    return BulkImportResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=results,
    )


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


@router.post("/{paper_id}/summary", response_model=PaperSummaryData)
async def generate_summary(paper_id: str):
    """Generate AI summary for a paper using Ollama"""
    data = load_data()
    paper_idx = next((i for i, p in enumerate(data["papers"]) if p["id"] == paper_id), None)

    if paper_idx is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = data["papers"][paper_idx]

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
        paper["summary"] = {
            "one_line": summary.one_line,
            "contribution": summary.contribution,
            "methodology": summary.methodology,
            "results": summary.results,
        }
        paper["updated_at"] = now_iso()
        save_data(data)

        return paper["summary"]

    except OllamaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{paper_id}/translate")
async def translate_paper(paper_id: str):
    """Translate paper title and abstract to Korean using Ollama"""
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

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
        paper["translation"] = translation
        paper["updated_at"] = now_iso()
        save_data(data)

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
    """Translate full paper PDF to Korean using Ollama"""
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

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

        # Translate with Ollama (section by section)
        translated_sections = await ollama_service.translate_full_paper(paper_text)

        # Save full translation to paper
        paper["full_translation"] = translated_sections
        paper["updated_at"] = now_iso()
        save_data(data)

        return {
            "paper_id": paper_id,
            "sections": translated_sections,
        }

    except PdfServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except OllamaServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/{paper_id}/summarize-full")
async def summarize_full_paper(paper_id: str):
    """Summarize full paper PDF in Korean using Ollama"""
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

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

        # Save full summary to paper
        paper["full_summary"] = summary
        paper["updated_at"] = now_iso()
        save_data(data)

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
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

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

    data = load_data()

    # Parse authors and tags
    author_list = [a.strip() for a in authors.split(",") if a.strip()] if authors else []
    tag_names = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Auto-predict tags if not provided
    if not tag_names and abstract:
        tag_names = predict_tags(final_title, abstract)

    tags_data = get_or_create_tags(data, tag_names)
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

    data["papers"].append(paper)
    save_data(data)

    return paper


@router.get("/{paper_id}/pdf-file")
async def get_uploaded_pdf(paper_id: str):
    """Get uploaded PDF file for a paper"""
    data = load_data()
    paper = next((p for p in data["papers"] if p["id"] == paper_id), None)

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    pdf_path = paper.get("pdf_path")
    if not pdf_path:
        raise HTTPException(status_code=404, detail="No uploaded PDF for this paper")

    full_path = os.path.join(UPLOAD_DIR, pdf_path)
    if not os.path.exists(full_path):
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
