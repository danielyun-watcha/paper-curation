"""Google Scholar search service using scholarly library"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from scholarly import scholarly


class ScholarServiceError(Exception):
    """Base exception for Scholar service errors"""
    pass


@dataclass
class ScholarResult:
    """Search result from Google Scholar"""
    title: str
    authors: List[str]
    abstract: Optional[str]
    year: Optional[int]
    url: Optional[str]
    cited_by: int
    pub_url: Optional[str]  # Publication URL


class ScholarService:
    """Service for searching Google Scholar"""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=1)

    def _search_sync(self, query: str, limit: int = 5) -> List[ScholarResult]:
        """Synchronous search (scholarly is blocking)"""
        results = []
        try:
            search_query = scholarly.search_pubs(query)

            for i, result in enumerate(search_query):
                if i >= limit:
                    break

                # Extract data from result
                bib = result.get('bib', {})

                # Get authors
                authors = bib.get('author', [])
                if isinstance(authors, str):
                    authors = [a.strip() for a in authors.split(' and ')]

                # Get year
                year = bib.get('pub_year')
                if year:
                    try:
                        year = int(year)
                    except ValueError:
                        year = None

                # Get abstract
                abstract = bib.get('abstract', '')

                # Get URL
                url = result.get('pub_url') or result.get('eprint_url')
                pub_url = result.get('pub_url')

                # Get citation count
                cited_by = result.get('num_citations', 0)

                results.append(ScholarResult(
                    title=bib.get('title', 'Unknown Title'),
                    authors=authors,
                    abstract=abstract if abstract else None,
                    year=year,
                    url=url,
                    cited_by=cited_by,
                    pub_url=pub_url,
                ))
        except Exception as e:
            raise ScholarServiceError(f"Failed to search Google Scholar: {str(e)}")

        return results

    async def search(self, query: str, limit: int = 5) -> List[ScholarResult]:
        """Search Google Scholar asynchronously with timeout"""
        loop = asyncio.get_event_loop()
        try:
            # Add 30 second timeout to prevent hanging
            return await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    self._search_sync,
                    query,
                    limit
                ),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise ScholarServiceError(
                "Google Scholar search timed out. Google may be blocking requests. "
                "Please try again in a few minutes or use a VPN."
            )


# Singleton instance
_scholar_service: Optional[ScholarService] = None


def get_scholar_service() -> ScholarService:
    """Get singleton Scholar service instance"""
    global _scholar_service
    if _scholar_service is None:
        _scholar_service = ScholarService()
    return _scholar_service
