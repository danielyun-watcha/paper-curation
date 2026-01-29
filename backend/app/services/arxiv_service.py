from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import httpx
from defusedxml import ElementTree as ET


@dataclass
class ArxivPaperData:
    """Data class for arXiv paper metadata"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    year: int
    arxiv_url: str
    published_at: str  # ISO date string (e.g., "2025-06-12")
    conference: Optional[str] = None  # Conference/venue name from Semantic Scholar


class ArxivServiceError(Exception):
    """Base exception for arXiv service errors"""
    pass


class InvalidArxivUrlError(ArxivServiceError):
    """Raised when the arXiv URL is invalid"""
    pass


class ArxivFetchError(ArxivServiceError):
    """Raised when fetching from arXiv API fails"""
    pass


class ArxivParseError(ArxivServiceError):
    """Raised when parsing arXiv response fails"""
    pass


class ArxivService:
    """Service for fetching paper metadata from arXiv API"""

    ARXIV_API_URL = "https://export.arxiv.org/api/query"
    SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/arXiv:"
    ARXIV_URL_PATTERNS = [
        r"arxiv\.org/abs/(\d{4}\.\d{4,5})(v\d+)?",  # https://arxiv.org/abs/2402.17152
        r"arxiv\.org/pdf/(\d{4}\.\d{4,5})(v\d+)?",  # https://arxiv.org/pdf/2402.17152
        r"^(\d{4}\.\d{4,5})(v\d+)?$",  # Just the ID: 2402.17152
    ]

    # XML namespaces used by arXiv API
    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    def extract_arxiv_id(self, url_or_id: str) -> str:
        """Extract arXiv ID from URL or validate raw ID"""
        url_or_id = url_or_id.strip()

        for pattern in self.ARXIV_URL_PATTERNS:
            match = re.search(pattern, url_or_id)
            if match:
                return match.group(1)  # Return ID without version

        raise InvalidArxivUrlError(f"Invalid arXiv URL or ID: {url_or_id}")

    async def fetch_paper(self, url_or_id: str) -> ArxivPaperData:
        """Fetch paper metadata from arXiv API"""
        arxiv_id = self.extract_arxiv_id(url_or_id)

        try:
            response = await self.client.get(
                self.ARXIV_API_URL,
                params={"id_list": arxiv_id},
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ArxivFetchError(f"Failed to fetch from arXiv API: {e}")

        paper_data = self._parse_response(response.text, arxiv_id)

        # Try to get conference info from Semantic Scholar
        conference = await self._fetch_conference(arxiv_id)
        paper_data.conference = conference

        return paper_data

    async def _fetch_conference(self, arxiv_id: str) -> Optional[str]:
        """Fetch conference/venue info from Semantic Scholar API"""
        try:
            response = await self.client.get(
                f"{self.SEMANTIC_SCHOLAR_API}{arxiv_id}",
                params={"fields": "venue,publicationVenue,year"},
            )
            if response.status_code != 200:
                return None

            data = response.json()
            year = data.get("year")
            year_suffix = f"'{str(year)[-2:]}" if year else ""

            # Try publicationVenue first - prefer abbreviation from alternate_names
            pub_venue = data.get("publicationVenue")
            if pub_venue:
                # Look for short abbreviation in alternate_names (e.g., "ICML", "NeurIPS")
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
            if venue:
                return f"{venue}{year_suffix}"

            return None
        except Exception:
            return None

    def _parse_response(self, xml_content: str, arxiv_id: str) -> ArxivPaperData:
        """Parse arXiv API XML response"""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ArxivParseError(f"Failed to parse XML: {e}")

        # Find the entry element
        entry = root.find("atom:entry", self.NAMESPACES)
        if entry is None:
            raise ArxivParseError("No entry found in arXiv response")

        # Check if paper exists (arXiv returns empty entry for invalid IDs)
        title_elem = entry.find("atom:title", self.NAMESPACES)
        if title_elem is None or not title_elem.text:
            raise ArxivParseError(f"Paper not found: {arxiv_id}")

        # Extract title (clean up whitespace)
        title = " ".join(title_elem.text.split())

        # Extract authors
        authors = []
        for author in entry.findall("atom:author", self.NAMESPACES):
            name = author.find("atom:name", self.NAMESPACES)
            if name is not None and name.text:
                authors.append(name.text)

        if not authors:
            raise ArxivParseError("No authors found")

        # Extract abstract (clean up whitespace)
        abstract_elem = entry.find("atom:summary", self.NAMESPACES)
        if abstract_elem is None or not abstract_elem.text:
            raise ArxivParseError("No abstract found")
        abstract = " ".join(abstract_elem.text.split())

        # Extract publication date and year
        published_elem = entry.find("atom:published", self.NAMESPACES)
        if published_elem is None or not published_elem.text:
            raise ArxivParseError("No publication date found")
        published_at = published_elem.text[:10]  # "2025-06-12T..."" -> "2025-06-12"
        year = int(published_at[:4])

        # Construct arXiv URL
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

        return ArxivPaperData(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            arxiv_url=arxiv_url,
            published_at=published_at,
        )


# Singleton instance
_arxiv_service: Optional[ArxivService] = None


def get_arxiv_service() -> ArxivService:
    """Get or create arXiv service instance"""
    global _arxiv_service
    if _arxiv_service is None:
        _arxiv_service = ArxivService()
    return _arxiv_service
