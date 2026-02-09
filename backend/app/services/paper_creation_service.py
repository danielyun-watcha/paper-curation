"""Service for paper creation with unified logic"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.database import generate_id, now_iso
from app.repositories.paper_repository import get_paper_repository
from app.services.arxiv_service import get_arxiv_service, ArxivServiceError, InvalidArxivUrlError
from app.services.doi_service import get_doi_service, DoiServiceError, InvalidDoiUrlError
from app.services.semantic_scholar_service import get_semantic_scholar_service, SemanticScholarError


class PaperCreationError(Exception):
    """Base exception for paper creation errors"""
    pass


class DuplicatePaperError(PaperCreationError):
    """Raised when paper already exists"""
    pass


class MetadataFetchError(PaperCreationError):
    """Raised when metadata cannot be fetched"""
    pass


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

# Fallback tags for minimum tag guarantee
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

INDUSTRIAL_KEYWORDS = ["a/b", "deployed", "production", "billion users", "million users", "online experiment"]


class PaperCreationService:
    """
    Unified service for creating papers from various sources.
    Handles metadata fetching, duplicate checking, and auto-prediction.
    """

    def __init__(self):
        self.repo = get_paper_repository()
        self.arxiv_service = get_arxiv_service()
        self.doi_service = get_doi_service()
        self.ss_service = get_semantic_scholar_service()

    def predict_category(self, title: str, abstract: str) -> str:
        """Predict category based on title and abstract content"""
        text = (title + " " + abstract).lower()

        category_scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score

        if not category_scores:
            return "other"

        return max(category_scores.items(), key=lambda x: x[1])[0]

    def predict_tags(self, title: str, abstract: str, max_tags: int = 3, min_tags: int = 2) -> List[str]:
        """Predict tags based on title and abstract content"""
        text = (title + " " + abstract).lower()

        # Check for industrial keywords
        has_industrial = any(kw in text for kw in INDUSTRIAL_KEYWORDS)

        tag_scores = {}
        for tag, keywords in TAG_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                tag_scores[tag] = score

        sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)

        if has_industrial:
            result = [tag for tag, _ in sorted_tags[:max_tags - 1]]
            result.append("Industrial")
        else:
            result = [tag for tag, _ in sorted_tags[:max_tags]]

        # Ensure minimum tags
        if len(result) < min_tags:
            fallback = self._get_fallback_tags(text, exclude=result)
            result.extend(fallback[:min_tags - len(result)])

        return sorted(result)

    def _get_fallback_tags(self, text: str, exclude: List[str]) -> List[str]:
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

    async def create_from_arxiv(
        self,
        arxiv_url: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """
        Create paper from arXiv URL.

        Args:
            arxiv_url: arXiv URL or ID
            category: Explicit category or None for auto-prediction
            tags: Explicit tags or None for auto-prediction

        Returns:
            Created paper dict

        Raises:
            DuplicatePaperError: If paper already exists
            MetadataFetchError: If metadata cannot be fetched
        """
        try:
            paper_data = await self.arxiv_service.fetch_paper(arxiv_url)
        except (InvalidArxivUrlError, ArxivServiceError) as e:
            raise MetadataFetchError(str(e))

        # Check duplicate
        if self.repo.exists_by_arxiv_id(paper_data.arxiv_id):
            raise DuplicatePaperError(f"Paper with arXiv ID {paper_data.arxiv_id} already exists")

        # Auto-predict if not provided
        final_category = category if category and category != "other" else self.predict_category(
            paper_data.title, paper_data.abstract
        )
        final_tags = tags if tags else self.predict_tags(paper_data.title, paper_data.abstract)
        tag_objects = self.repo.get_or_create_tags(final_tags)

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
            "category": final_category,
            "tags": tag_objects,
            "published_at": paper_data.published_at,
            "created_at": now,
            "updated_at": now,
        }

        return self.repo.add(paper)

    async def create_from_doi(
        self,
        doi_url: str,
        title: Optional[str] = None,
        abstract: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> dict:
        """
        Create paper from DOI URL.

        Args:
            doi_url: DOI URL
            title: Override title (if API fails)
            abstract: Override abstract
            category: Explicit category or None for auto-prediction
            tags: Explicit tags or None for auto-prediction

        Returns:
            Created paper dict

        Raises:
            DuplicatePaperError: If paper already exists
            MetadataFetchError: If metadata cannot be fetched
        """
        try:
            paper_data = await self.doi_service.fetch_paper(doi_url)
        except (InvalidDoiUrlError, DoiServiceError) as e:
            raise MetadataFetchError(str(e))

        # Check duplicate
        if paper_data.doi and self.repo.exists_by_doi(paper_data.doi):
            raise DuplicatePaperError(f"Paper with DOI {paper_data.doi} already exists")

        # Use overrides or API data
        final_title = title or paper_data.title
        final_abstract = abstract or paper_data.abstract or ""

        if not final_title:
            raise MetadataFetchError("Title is required but could not be fetched")

        # Auto-predict if not provided
        final_category = category if category and category != "other" else (
            self.predict_category(final_title, final_abstract) if final_abstract else "other"
        )
        final_tags = tags if tags else (
            self.predict_tags(final_title, final_abstract) if final_abstract else []
        )
        tag_objects = self.repo.get_or_create_tags(final_tags)

        now = now_iso()
        paper = {
            "id": generate_id(),
            "title": final_title,
            "authors": paper_data.authors,
            "abstract": final_abstract,
            "year": paper_data.year or 0,
            "arxiv_id": paper_data.arxiv_id,
            "arxiv_url": f"https://arxiv.org/abs/{paper_data.arxiv_id}" if paper_data.arxiv_id else None,
            "doi": paper_data.doi,
            "paper_url": paper_data.url,
            "conference": paper_data.conference,
            "category": final_category,
            "tags": tag_objects,
            "published_at": paper_data.published_at,
            "created_at": now,
            "updated_at": now,
        }

        return self.repo.add(paper)

    async def create_from_search_result(
        self,
        title: str,
        authors: List[str],
        url: Optional[str] = None,
        abstract: Optional[str] = None,
        year: Optional[int] = None,
    ) -> dict:
        """
        Create paper from search result (Google Scholar, etc.).
        Enriches with data from arXiv/Semantic Scholar/DOI if possible.

        Args:
            title: Paper title
            authors: Paper authors
            url: Paper URL (may contain arXiv/DOI info)
            abstract: Paper abstract
            year: Publication year

        Returns:
            Created paper dict

        Raises:
            DuplicatePaperError: If paper already exists
        """
        # Check duplicate by title
        if self.repo.exists_by_title(title):
            raise DuplicatePaperError(f"Paper with title '{title}' already exists")

        final_title = title
        final_authors = authors
        final_abstract = abstract or ""
        final_year = year
        arxiv_id = None
        arxiv_url = None
        doi = None
        published_at = None
        conference = None

        url = url or ""

        # Try arXiv if URL contains arxiv.org
        if "arxiv.org" in url.lower():
            try:
                paper_data = await self.arxiv_service.fetch_paper(url)
                final_title = paper_data.title
                final_authors = paper_data.authors
                final_abstract = paper_data.abstract
                final_year = paper_data.year
                arxiv_id = paper_data.arxiv_id
                arxiv_url = paper_data.arxiv_url
                published_at = paper_data.published_at
                conference = paper_data.conference

                if self.repo.exists_by_arxiv_id(arxiv_id):
                    raise DuplicatePaperError(f"Paper with arXiv ID {arxiv_id} already exists")
            except (InvalidArxivUrlError, ArxivServiceError):
                pass

        # Try DOI if URL contains doi.org
        if "doi.org/" in url.lower() and not arxiv_id:
            try:
                extracted_doi, _ = self.doi_service.extract_doi(url)
                doi = extracted_doi
            except InvalidDoiUrlError:
                pass

        # Enrich with Semantic Scholar if no arXiv
        if not arxiv_id:
            try:
                ss_paper = await self.ss_service.search_by_title(final_title)
                if ss_paper and ss_paper.abstract:
                    if len(ss_paper.abstract) > len(final_abstract):
                        final_abstract = ss_paper.abstract
                    if ss_paper.authors and len(ss_paper.authors) > len(final_authors):
                        final_authors = ss_paper.authors
                    if ss_paper.year:
                        final_year = ss_paper.year
                    if ss_paper.doi:
                        doi = ss_paper.doi
                    # If arXiv found, fetch full data
                    if ss_paper.arxiv_id:
                        try:
                            arxiv_data = await self.arxiv_service.fetch_paper(
                                f"https://arxiv.org/abs/{ss_paper.arxiv_id}"
                            )
                            final_title = arxiv_data.title
                            final_authors = arxiv_data.authors
                            final_abstract = arxiv_data.abstract
                            final_year = arxiv_data.year
                            arxiv_id = arxiv_data.arxiv_id
                            arxiv_url = arxiv_data.arxiv_url
                            published_at = arxiv_data.published_at

                            if self.repo.exists_by_arxiv_id(arxiv_id):
                                raise DuplicatePaperError(f"Paper with arXiv ID {arxiv_id} already exists")
                        except (InvalidArxivUrlError, ArxivServiceError):
                            arxiv_id = ss_paper.arxiv_id
                            arxiv_url = f"https://arxiv.org/abs/{ss_paper.arxiv_id}"
            except SemanticScholarError:
                pass

        # Get conference from DOI if available
        if doi and not conference:
            try:
                doi_data = await self.doi_service.fetch_paper(f"https://doi.org/{doi}")
                if doi_data.conference:
                    conference = doi_data.conference
                if doi_data.published_at and not published_at:
                    published_at = doi_data.published_at
            except (DoiServiceError, InvalidDoiUrlError):
                pass

        # Auto-predict category and tags
        category = self.predict_category(final_title, final_abstract)
        tag_names = self.predict_tags(final_title, final_abstract) if final_abstract else []
        tag_objects = self.repo.get_or_create_tags(tag_names)

        now = now_iso()
        paper = {
            "id": generate_id(),
            "title": final_title,
            "authors": final_authors,
            "abstract": final_abstract,
            "year": final_year or 2024,
            "arxiv_id": arxiv_id,
            "arxiv_url": arxiv_url,
            "doi": doi,
            "paper_url": url if not arxiv_url else None,
            "conference": conference,
            "category": category,
            "tags": tag_objects,
            "published_at": published_at,
            "created_at": now,
            "updated_at": now,
        }

        return self.repo.add(paper)


# Singleton instance
_paper_creation_service: Optional[PaperCreationService] = None


def get_paper_creation_service() -> PaperCreationService:
    """Get singleton PaperCreationService instance"""
    global _paper_creation_service
    if _paper_creation_service is None:
        _paper_creation_service = PaperCreationService()
    return _paper_creation_service
