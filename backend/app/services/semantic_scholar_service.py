"""Semantic Scholar API service for fetching paper metadata"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


class SemanticScholarError(Exception):
    """Base exception for Semantic Scholar service errors"""
    pass


@dataclass
class SemanticScholarPaper:
    """Paper data from Semantic Scholar"""
    title: str
    authors: List[str]
    abstract: Optional[str]
    year: Optional[int]
    url: Optional[str]
    doi: Optional[str]
    arxiv_id: Optional[str]
    citation_count: int = 0
    ss_id: Optional[str] = None  # Semantic Scholar paper ID (SHA hash)


class SemanticScholarService:
    """Service for fetching paper info from Semantic Scholar API"""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    async def search_by_title(self, title: str) -> Optional[SemanticScholarPaper]:
        """Search for a paper by title and return the best match"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Search for papers
                response = await client.get(
                    f"{self.BASE_URL}/paper/search",
                    params={
                        "query": title,
                        "limit": 1,
                        "fields": "title,authors,abstract,year,url,externalIds"
                    }
                )

                if response.status_code == 429:
                    raise SemanticScholarError("Rate limited by Semantic Scholar API")

                response.raise_for_status()
                data = response.json()

                if not data.get("data"):
                    return None

                paper = data["data"][0]

                # Extract authors
                authors = [a.get("name", "") for a in paper.get("authors", [])]

                # Extract external IDs
                external_ids = paper.get("externalIds") or {}
                doi = external_ids.get("DOI")
                arxiv_id = external_ids.get("ArXiv")

                return SemanticScholarPaper(
                    title=paper.get("title", ""),
                    authors=authors,
                    abstract=paper.get("abstract"),
                    year=paper.get("year"),
                    url=paper.get("url"),
                    doi=doi,
                    arxiv_id=arxiv_id,
                    ss_id=paper.get("paperId"),
                )

        except httpx.HTTPStatusError as e:
            raise SemanticScholarError(f"API error: {e.response.status_code}")
        except Exception as e:
            raise SemanticScholarError(f"Failed to fetch from Semantic Scholar: {str(e)}")

    async def get_recommendations(self, paper_id: str, limit: int = 5) -> List[SemanticScholarPaper]:
        """Get recommended papers using Semantic Scholar Recommendations API.

        paper_id can be: "ArXiv:{arxiv_id}", "DOI:{doi}", or a Semantic Scholar paper ID.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paper_id}",
                    params={
                        "limit": limit,
                        "fields": "title,authors,abstract,year,url,externalIds,citationCount",
                        "from": "all-cs",
                    },
                )

                if response.status_code == 404:
                    raise SemanticScholarError("Paper not found in Semantic Scholar")
                if response.status_code == 429:
                    raise SemanticScholarError("Rate limited by Semantic Scholar API")
                response.raise_for_status()

                data = response.json()
                recommended = data.get("recommendedPapers", [])

                results = []
                for paper in recommended:
                    authors = [a.get("name", "") for a in paper.get("authors", [])]
                    external_ids = paper.get("externalIds") or {}

                    results.append(SemanticScholarPaper(
                        title=paper.get("title", ""),
                        authors=authors,
                        abstract=paper.get("abstract"),
                        year=paper.get("year"),
                        url=paper.get("url"),
                        doi=external_ids.get("DOI"),
                        arxiv_id=external_ids.get("ArXiv"),
                        citation_count=paper.get("citationCount", 0),
                    ))

                return results

        except SemanticScholarError:
            raise
        except httpx.HTTPStatusError as e:
            raise SemanticScholarError(f"API error: {e.response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to get recommendations for {paper_id}: {e}")
            raise SemanticScholarError(f"Failed to get recommendations: {str(e)}")

    async def get_by_doi(self, doi: str) -> Optional[SemanticScholarPaper]:
        """Get paper info by DOI"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.BASE_URL}/paper/DOI:{doi}",
                    params={
                        "fields": "title,authors,abstract,year,url,externalIds"
                    }
                )

                if response.status_code == 404:
                    return None
                if response.status_code == 429:
                    raise SemanticScholarError("Rate limited by Semantic Scholar API")

                response.raise_for_status()
                paper = response.json()

                # Extract authors
                authors = [a.get("name", "") for a in paper.get("authors", [])]

                # Extract external IDs
                external_ids = paper.get("externalIds") or {}
                arxiv_id = external_ids.get("ArXiv")

                return SemanticScholarPaper(
                    title=paper.get("title", ""),
                    authors=authors,
                    abstract=paper.get("abstract"),
                    year=paper.get("year"),
                    url=paper.get("url"),
                    doi=doi,
                    arxiv_id=arxiv_id,
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise SemanticScholarError(f"API error: {e.response.status_code}")
        except Exception as e:
            raise SemanticScholarError(f"Failed to fetch from Semantic Scholar: {str(e)}")


# Singleton instance
_semantic_scholar_service: Optional[SemanticScholarService] = None


def get_semantic_scholar_service() -> SemanticScholarService:
    """Get singleton Semantic Scholar service instance"""
    global _semantic_scholar_service
    if _semantic_scholar_service is None:
        _semantic_scholar_service = SemanticScholarService()
    return _semantic_scholar_service
