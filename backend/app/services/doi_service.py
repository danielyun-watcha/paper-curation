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


class DoiServiceError(Exception):
    pass


class InvalidDoiUrlError(DoiServiceError):
    pass


class DoiService:
    CROSSREF_API = "https://api.crossref.org/works/"
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

    async def fetch_from_semantic_scholar(self, doi: str) -> Optional[dict]:
        """Try to fetch paper data from Semantic Scholar API"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.SEMANTIC_SCHOLAR_API}{doi}",
                    params={"fields": "title,authors,abstract,year"},
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def fetch_paper(self, url: str) -> DoiPaperData:
        """Fetch paper metadata from DOI"""
        doi, source = self.extract_doi(url)

        # IEEE uses different ID system, need to get DOI differently
        if source == "ieee":
            # For IEEE, we'll use a different approach or just store the URL
            # IEEE API requires authentication, so we'll do minimal metadata
            return DoiPaperData(
                title="",  # Will need manual input
                authors=[],
                abstract=None,
                year=0,
                doi=doi,
                url=url,
                source=source,
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.CROSSREF_API}{doi}",
                headers={"Accept": "application/json"},
            )

            if response.status_code == 404:
                raise DoiServiceError(f"DOI not found: {doi}")

            if response.status_code != 200:
                raise DoiServiceError(f"CrossRef API error: {response.status_code}")

            data = response.json()["message"]

            # Extract title
            title = data.get("title", [""])[0]

            # Extract authors
            authors = []
            for author in data.get("author", []):
                given = author.get("given", "")
                family = author.get("family", "")
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

            # Extract abstract (often not available from CrossRef)
            abstract = data.get("abstract")
            if abstract:
                # Remove HTML tags from abstract
                abstract = re.sub(r"<[^>]+>", "", abstract)

            # If no abstract from CrossRef, try Semantic Scholar
            if not abstract:
                ss_data = await self.fetch_from_semantic_scholar(doi)
                if ss_data and ss_data.get("abstract"):
                    abstract = ss_data["abstract"]

            # Extract year
            year = 0
            for date_field in ["published-print", "published-online", "created"]:
                if date_field in data and "date-parts" in data[date_field]:
                    date_parts = data[date_field]["date-parts"][0]
                    if date_parts and date_parts[0]:
                        year = date_parts[0]
                        break

            # Determine proper URL
            if source == "acm":
                paper_url = f"https://dl.acm.org/doi/{doi}"
            else:
                paper_url = url

            return DoiPaperData(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                doi=doi,
                url=paper_url,
                source=source,
            )


_doi_service: Optional[DoiService] = None


def get_doi_service() -> DoiService:
    global _doi_service
    if _doi_service is None:
        _doi_service = DoiService()
    return _doi_service
