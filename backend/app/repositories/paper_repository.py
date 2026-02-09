"""Repository layer for paper data access"""
from math import ceil
from typing import List, Optional, Dict, Any, Tuple

from app.database import load_data, save_data, generate_id, now_iso


class PaperRepository:
    """
    Repository for paper CRUD operations.
    Provides abstraction over JSON file storage with efficient lookups.
    """

    def __init__(self):
        self._data: Optional[dict] = None

    def _get_data(self) -> dict:
        """Get current data (lazy load)"""
        if self._data is None:
            self._data = load_data()
        return self._data

    def _save(self):
        """Save current data to storage"""
        if self._data is not None:
            save_data(self._data)

    def reload(self):
        """Force reload data from storage"""
        self._data = load_data()

    def get_raw_data(self) -> dict:
        """Get raw data dict for complex operations.

        WARNING: Use sparingly. Prefer specific repository methods.
        Caller is responsible for calling save_all() after modifications.
        """
        return self._get_data()

    # ============ Query Methods ============

    def find_all(self) -> List[dict]:
        """Get all papers"""
        return self._get_data()["papers"]

    def find_by_id(self, paper_id: str) -> Optional[dict]:
        """Find paper by ID"""
        return next(
            (p for p in self._get_data()["papers"] if p["id"] == paper_id),
            None
        )

    def find_by_arxiv_id(self, arxiv_id: str) -> Optional[dict]:
        """Find paper by arXiv ID"""
        return next(
            (p for p in self._get_data()["papers"] if p.get("arxiv_id") == arxiv_id),
            None
        )

    def find_by_doi(self, doi: str) -> Optional[dict]:
        """Find paper by DOI"""
        return next(
            (p for p in self._get_data()["papers"] if p.get("doi") == doi),
            None
        )

    def find_by_title(self, title: str, case_insensitive: bool = True) -> Optional[dict]:
        """Find paper by title"""
        if case_insensitive:
            title_lower = title.lower()
            return next(
                (p for p in self._get_data()["papers"] if p["title"].lower() == title_lower),
                None
            )
        return next(
            (p for p in self._get_data()["papers"] if p["title"] == title),
            None
        )

    def get_years(self) -> List[int]:
        """Get list of years that have papers, sorted descending"""
        years = set(p["year"] for p in self._get_data()["papers"] if p.get("year"))
        return sorted(years, reverse=True)

    def find_all_filtered(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        year: Optional[int] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[dict], int, int]:
        """
        Find papers with filters and pagination.

        Returns: (papers, total_count, total_pages)
        """
        papers = self._get_data()["papers"]

        # Apply filters
        if search:
            search_lower = search.lower()
            papers = [
                p for p in papers
                if search_lower in p["title"].lower()
                or search_lower in p.get("abstract", "").lower()
                or (p.get("conference") and search_lower in p["conference"].lower())
            ]

        if category:
            papers = [p for p in papers if p["category"] == category]

        if year:
            papers = [p for p in papers if p["year"] == year]

        if tags:
            tag_names = [t.lower() for t in tags]
            papers = [
                p for p in papers
                if any(t["name"].lower() in tag_names for t in p.get("tags", []))
            ]

        # Sort by updated_at descending
        papers = sorted(papers, key=lambda p: p.get("updated_at", ""), reverse=True)

        total = len(papers)
        pages = ceil(total / limit) if total > 0 else 0

        # Paginate
        start = (page - 1) * limit
        end = start + limit
        papers = papers[start:end]

        return papers, total, pages

    def count(self) -> int:
        """Count total papers"""
        return len(self._get_data()["papers"])

    # ============ Existence Checks ============

    def exists_by_id(self, paper_id: str) -> bool:
        """Check if paper exists by ID"""
        return self.find_by_id(paper_id) is not None

    def exists_by_arxiv_id(self, arxiv_id: str) -> bool:
        """Check if paper exists by arXiv ID"""
        return self.find_by_arxiv_id(arxiv_id) is not None

    def exists_by_doi(self, doi: str) -> bool:
        """Check if paper exists by DOI"""
        return self.find_by_doi(doi) is not None

    def exists_by_title(self, title: str) -> bool:
        """Check if paper exists by title (case-insensitive)"""
        return self.find_by_title(title) is not None

    # ============ Mutation Methods ============

    def add(self, paper: dict) -> dict:
        """Add a new paper. Generates ID and timestamps if not present."""
        if "id" not in paper:
            paper["id"] = generate_id()
        now = now_iso()
        if "created_at" not in paper:
            paper["created_at"] = now
        if "updated_at" not in paper:
            paper["updated_at"] = now

        self._get_data()["papers"].append(paper)
        self._save()
        return paper

    def update(self, paper_id: str, updates: Dict[str, Any]) -> Optional[dict]:
        """Update a paper by ID. Returns updated paper or None if not found."""
        paper = self.find_by_id(paper_id)
        if paper is None:
            return None

        updates["updated_at"] = now_iso()
        paper.update(updates)
        self._save()
        return paper

    def delete(self, paper_id: str) -> bool:
        """Delete a paper by ID. Returns True if deleted, False if not found."""
        data = self._get_data()
        original_len = len(data["papers"])
        data["papers"] = [p for p in data["papers"] if p["id"] != paper_id]

        if len(data["papers"]) < original_len:
            self._save()
            return True
        return False

    def save_all(self):
        """Explicitly save all changes"""
        self._save()

    def add_bulk(self, papers: List[dict]) -> List[dict]:
        """Add multiple papers at once. More efficient than individual adds."""
        now = now_iso()
        data = self._get_data()

        for paper in papers:
            if "id" not in paper:
                paper["id"] = generate_id()
            if "created_at" not in paper:
                paper["created_at"] = now
            if "updated_at" not in paper:
                paper["updated_at"] = now
            data["papers"].append(paper)

        self._save()
        return papers

    def update_field(self, paper_id: str, field: str, value: Any) -> Optional[dict]:
        """Update a single field on a paper"""
        paper = self.find_by_id(paper_id)
        if paper is None:
            return None

        paper[field] = value
        paper["updated_at"] = now_iso()
        self._save()
        return paper

    # ============ Tag Methods ============

    def get_all_tags(self) -> List[dict]:
        """Get all tags"""
        return self._get_data()["tags"]

    def get_or_create_tag(self, name: str) -> dict:
        """Get existing tag or create new one (case-insensitive match)"""
        data = self._get_data()
        name = name.strip()
        if not name:
            raise ValueError("Tag name cannot be empty")

        # Find existing tag
        existing = next(
            (t for t in data["tags"] if t["name"].lower() == name.lower()),
            None
        )
        if existing:
            return existing

        # Create new tag
        new_tag = {"id": generate_id(), "name": name}
        data["tags"].append(new_tag)
        return new_tag

    def get_or_create_tags(self, tag_names: List[str]) -> List[dict]:
        """Get or create multiple tags, sorted alphabetically"""
        result = []
        for name in sorted(tag_names):
            name = name.strip()
            if name:
                result.append(self.get_or_create_tag(name))
        return result


# Singleton instance
_paper_repository: Optional[PaperRepository] = None


def get_paper_repository() -> PaperRepository:
    """Get singleton PaperRepository instance"""
    global _paper_repository
    if _paper_repository is None:
        _paper_repository = PaperRepository()
    return _paper_repository
