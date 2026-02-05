from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import httpx


@dataclass
class DoiPaperData:
    title: str
    authors: List[str]
    abstract: Optional[str]
    year: int
    doi: str
    url: str
    source: str  # "acm", "ieee", "other"
    published_at: Optional[str] = None  # ISO date string
    conference: Optional[str] = None  # Conference abbreviation (e.g., KDD, WWW)
    arxiv_id: Optional[str] = None  # arXiv ID if available


class DoiServiceError(Exception):
    pass


class InvalidDoiUrlError(DoiServiceError):
    pass


class DoiService:
    SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/DOI:"

    # URL patterns for DOI extraction
    DOI_PATTERNS = [
        # ACM: https://dl.acm.org/doi/10.1145/xxxxx
        (r"dl\.acm\.org/doi/(10\.\d+/[^\s?#]+)", "acm"),
        # IEEE: https://ieeexplore.ieee.org/document/xxxxx
        (r"ieeexplore\.ieee\.org/document/(\d+)", "ieee"),
        # Direct DOI URL: https://doi.org/10.xxxx/xxxxx
        (r"doi\.org/(10\.\d+/[^\s?#]+)", "doi"),
        # Generic DOI pattern in URL
        (r"(10\.\d+/[^\s?#]+)", "other"),
    ]

    def extract_doi(self, url: str) -> tuple[str, str]:
        """Extract DOI from URL and determine source"""
        for pattern, source in self.DOI_PATTERNS:
            match = re.search(pattern, url)
            if match:
                doi = match.group(1)
                return doi, source

        raise InvalidDoiUrlError(f"Could not extract DOI from URL: {url}")

    async def fetch_paper(self, url: str) -> DoiPaperData:
        """Fetch paper metadata from Semantic Scholar API"""
        doi, source = self.extract_doi(url)

        # IEEE uses document ID, not DOI - need manual input
        if source == "ieee":
            return DoiPaperData(
                title="",
                authors=[],
                abstract=None,
                year=0,
                doi=doi,
                url=url,
                source=source,
            )

        # Use Semantic Scholar API (has title, authors, abstract, year, publicationDate, venue)
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.SEMANTIC_SCHOLAR_API}{doi}",
                params={"fields": "title,authors,abstract,year,publicationDate,venue,publicationVenue,externalIds"},
            )

            if response.status_code == 404:
                raise DoiServiceError(f"Paper not found in Semantic Scholar: {doi}")

            if response.status_code != 200:
                raise DoiServiceError(f"Semantic Scholar API error: {response.status_code}")

            data = response.json()

            # Extract authors
            authors = [a.get("name", "") for a in data.get("authors", []) if a.get("name")]

            # Extract conference abbreviation
            conference = self._extract_conference(data)

            # Determine proper URL
            if source == "acm":
                paper_url = f"https://dl.acm.org/doi/{doi}"
            else:
                paper_url = url

            # Extract arXiv ID from externalIds
            external_ids = data.get("externalIds") or {}
            arxiv_id = external_ids.get("ArXiv")

            return DoiPaperData(
                title=data.get("title", ""),
                authors=authors,
                abstract=data.get("abstract"),
                year=data.get("year") or 0,
                doi=doi,
                url=paper_url,
                source=source,
                published_at=data.get("publicationDate"),  # "2025-09-07" format
                conference=conference,
                arxiv_id=arxiv_id,
            )

    def _extract_conference(self, data: dict) -> Optional[str]:
        """Extract conference abbreviation from Semantic Scholar response"""
        year = data.get("year")
        year_suffix = f"'{str(year)[-2:]}" if year else ""

        # Try publicationVenue first - prefer abbreviation from alternate_names
        pub_venue = data.get("publicationVenue")
        if pub_venue:
            # Look for short abbreviation in alternate_names (e.g., "KDD", "WWW")
            alt_names = pub_venue.get("alternate_names", [])
            for name in alt_names:
                # Prefer short uppercase abbreviations
                if name.isupper() and len(name) <= 10:
                    return f"{name}{year_suffix}"
            # Fall back to first alternate name or full name
            if alt_names:
                return f"{alt_names[0]}{year_suffix}"
            if pub_venue.get("name"):
                return f"{pub_venue['name']}{year_suffix}"

        # Fall back to venue string
        venue = data.get("venue")
        if venue and venue.lower() not in ("arxiv", "arxiv.org"):
            return f"{venue}{year_suffix}"

        return None


_doi_service: Optional[DoiService] = None


def get_doi_service() -> DoiService:
    global _doi_service
    if _doi_service is None:
        _doi_service = DoiService()
    return _doi_service
