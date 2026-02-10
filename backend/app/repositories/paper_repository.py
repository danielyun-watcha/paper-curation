"""Repository layer for paper data access using SQLite"""
import json
import uuid
from datetime import datetime
from math import ceil
from typing import List, Optional, Dict, Any, Tuple

from app.db.connection import get_db


def generate_id() -> str:
    """Generate a new UUID"""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Get current time in ISO format"""
    return datetime.now().isoformat()


class PaperRepository:
    """
    Repository for paper CRUD operations using SQLite.
    Provides the same interface as the previous JSON-based implementation.
    """

    # ============ Helper Methods ============

    def _row_to_dict(self, row) -> dict:
        """Convert SQLite row to paper dict with tags."""
        if row is None:
            return None

        paper = dict(row)

        # Parse JSON fields
        paper["authors"] = json.loads(paper["authors"]) if paper["authors"] else []

        # Parse summary object
        if any(paper.get(f"summary_{k}") for k in ["one_line", "contribution", "methodology", "results"]):
            paper["summary"] = {
                "one_line": paper.pop("summary_one_line"),
                "contribution": paper.pop("summary_contribution"),
                "methodology": paper.pop("summary_methodology"),
                "results": paper.pop("summary_results"),
            }
        else:
            paper.pop("summary_one_line", None)
            paper.pop("summary_contribution", None)
            paper.pop("summary_methodology", None)
            paper.pop("summary_results", None)

        # Parse translation JSON
        if paper.get("translation"):
            paper["translation"] = json.loads(paper["translation"])

        return paper

    def _get_paper_tags(self, conn, paper_id: str) -> List[dict]:
        """Get tags for a paper."""
        cursor = conn.execute("""
            SELECT t.id, t.name
            FROM tags t
            JOIN paper_tags pt ON t.id = pt.tag_id
            WHERE pt.paper_id = ?
            ORDER BY t.name
        """, (paper_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _paper_with_tags(self, conn, row) -> Optional[dict]:
        """Convert row to dict and attach tags."""
        if row is None:
            return None
        paper = self._row_to_dict(row)
        paper["tags"] = self._get_paper_tags(conn, paper["id"])
        return paper

    # ============ Query Methods ============

    def find_all(self) -> List[dict]:
        """Get all papers with tags."""
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM papers ORDER BY updated_at DESC")
            papers = []
            for row in cursor.fetchall():
                paper = self._paper_with_tags(conn, row)
                papers.append(paper)
            return papers

    def find_by_id(self, paper_id: str) -> Optional[dict]:
        """Find paper by ID."""
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
            row = cursor.fetchone()
            return self._paper_with_tags(conn, row)

    def find_by_arxiv_id(self, arxiv_id: str) -> Optional[dict]:
        """Find paper by arXiv ID."""
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,))
            row = cursor.fetchone()
            return self._paper_with_tags(conn, row)

    def find_by_doi(self, doi: str) -> Optional[dict]:
        """Find paper by DOI."""
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM papers WHERE doi = ?", (doi,))
            row = cursor.fetchone()
            return self._paper_with_tags(conn, row)

    def find_by_title(self, title: str, case_insensitive: bool = True) -> Optional[dict]:
        """Find paper by title."""
        with get_db() as conn:
            if case_insensitive:
                cursor = conn.execute(
                    "SELECT * FROM papers WHERE LOWER(title) = LOWER(?)",
                    (title,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM papers WHERE title = ?",
                    (title,)
                )
            row = cursor.fetchone()
            return self._paper_with_tags(conn, row)

    def get_years(self) -> List[int]:
        """Get list of years that have papers, sorted descending."""
        with get_db() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT year FROM papers
                WHERE year IS NOT NULL
                ORDER BY year DESC
            """)
            return [row["year"] for row in cursor.fetchall()]

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
        with get_db() as conn:
            # Build query
            conditions = []
            params = []

            if search:
                conditions.append("""
                    (LOWER(title) LIKE ? OR LOWER(abstract) LIKE ? OR LOWER(conference) LIKE ?)
                """)
                search_pattern = f"%{search.lower()}%"
                params.extend([search_pattern, search_pattern, search_pattern])

            if category:
                conditions.append("category = ?")
                params.append(category)

            if year:
                conditions.append("year = ?")
                params.append(year)

            # Base query
            where_clause = " AND ".join(conditions) if conditions else "1=1"

            if tags:
                # Filter by tags using subquery
                tag_placeholders = ",".join("?" * len(tags))
                tag_conditions = f"""
                    id IN (
                        SELECT pt.paper_id FROM paper_tags pt
                        JOIN tags t ON pt.tag_id = t.id
                        WHERE LOWER(t.name) IN ({tag_placeholders})
                    )
                """
                where_clause = f"({where_clause}) AND {tag_conditions}"
                params.extend([t.lower() for t in tags])

            # Get total count
            count_query = f"SELECT COUNT(*) as cnt FROM papers WHERE {where_clause}"
            cursor = conn.execute(count_query, params)
            total = cursor.fetchone()["cnt"]

            # Calculate pagination
            pages = ceil(total / limit) if total > 0 else 0
            offset = (page - 1) * limit

            # Get paginated results
            query = f"""
                SELECT * FROM papers
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(query, params + [limit, offset])

            papers = []
            for row in cursor.fetchall():
                paper = self._paper_with_tags(conn, row)
                papers.append(paper)

            return papers, total, pages

    def count(self) -> int:
        """Count total papers."""
        with get_db() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM papers")
            return cursor.fetchone()["cnt"]

    # ============ Existence Checks ============

    def exists_by_id(self, paper_id: str) -> bool:
        """Check if paper exists by ID."""
        with get_db() as conn:
            cursor = conn.execute("SELECT 1 FROM papers WHERE id = ?", (paper_id,))
            return cursor.fetchone() is not None

    def exists_by_arxiv_id(self, arxiv_id: str) -> bool:
        """Check if paper exists by arXiv ID."""
        with get_db() as conn:
            cursor = conn.execute("SELECT 1 FROM papers WHERE arxiv_id = ?", (arxiv_id,))
            return cursor.fetchone() is not None

    def exists_by_doi(self, doi: str) -> bool:
        """Check if paper exists by DOI."""
        with get_db() as conn:
            cursor = conn.execute("SELECT 1 FROM papers WHERE doi = ?", (doi,))
            return cursor.fetchone() is not None

    def exists_by_title(self, title: str) -> bool:
        """Check if paper exists by title (case-insensitive)."""
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM papers WHERE LOWER(title) = LOWER(?)",
                (title,)
            )
            return cursor.fetchone() is not None

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

        with get_db() as conn:
            # Extract tags before insert
            tags = paper.pop("tags", [])

            # Prepare summary fields
            summary = paper.pop("summary", None)
            summary_one_line = summary.get("one_line") if summary else None
            summary_contribution = summary.get("contribution") if summary else None
            summary_methodology = summary.get("methodology") if summary else None
            summary_results = summary.get("results") if summary else None

            # Serialize JSON fields
            authors_json = json.dumps(paper.get("authors", []))
            translation_json = json.dumps(paper.get("translation")) if paper.get("translation") else None

            conn.execute("""
                INSERT INTO papers (
                    id, title, authors, abstract, year, arxiv_id, arxiv_url,
                    doi, paper_url, conference, category, published_at, pdf_path,
                    summary_one_line, summary_contribution, summary_methodology, summary_results,
                    full_summary, translation, full_translation, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                paper["id"],
                paper["title"],
                authors_json,
                paper.get("abstract"),
                paper.get("year"),
                paper.get("arxiv_id"),
                paper.get("arxiv_url"),
                paper.get("doi"),
                paper.get("paper_url"),
                paper.get("conference"),
                paper.get("category", "other"),
                paper.get("published_at"),
                paper.get("pdf_path"),
                summary_one_line,
                summary_contribution,
                summary_methodology,
                summary_results,
                paper.get("full_summary"),
                translation_json,
                paper.get("full_translation"),
                paper["created_at"],
                paper["updated_at"],
            ))

            # Add tags
            for tag in tags:
                self._ensure_tag(conn, tag)
                conn.execute(
                    "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
                    (paper["id"], tag["id"])
                )

            # Return complete paper with tags
            paper["tags"] = tags
            if summary:
                paper["summary"] = summary
            return paper

    def _ensure_tag(self, conn, tag: dict):
        """Ensure tag exists in database."""
        conn.execute(
            "INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)",
            (tag["id"], tag["name"])
        )

    def update(self, paper_id: str, updates: Dict[str, Any]) -> Optional[dict]:
        """Update a paper by ID. Returns updated paper or None if not found."""
        if not self.exists_by_id(paper_id):
            return None

        updates["updated_at"] = now_iso()

        with get_db() as conn:
            # Handle tags separately
            new_tags = updates.pop("tags", None)

            # Handle summary object
            if "summary" in updates:
                summary = updates.pop("summary")
                if summary:
                    updates["summary_one_line"] = summary.get("one_line")
                    updates["summary_contribution"] = summary.get("contribution")
                    updates["summary_methodology"] = summary.get("methodology")
                    updates["summary_results"] = summary.get("results")

            # Serialize JSON fields if present
            if "authors" in updates:
                updates["authors"] = json.dumps(updates["authors"])
            if "translation" in updates:
                updates["translation"] = json.dumps(updates["translation"]) if updates["translation"] else None

            # Build UPDATE query
            if updates:
                set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
                values = list(updates.values()) + [paper_id]
                conn.execute(
                    f"UPDATE papers SET {set_clause} WHERE id = ?",
                    values
                )

            # Update tags if provided
            if new_tags is not None:
                # Remove old tags
                conn.execute("DELETE FROM paper_tags WHERE paper_id = ?", (paper_id,))
                # Add new tags
                for tag in new_tags:
                    self._ensure_tag(conn, tag)
                    conn.execute(
                        "INSERT OR IGNORE INTO paper_tags (paper_id, tag_id) VALUES (?, ?)",
                        (paper_id, tag["id"])
                    )

        return self.find_by_id(paper_id)

    def delete(self, paper_id: str) -> bool:
        """Delete a paper by ID. Returns True if deleted, False if not found."""
        with get_db() as conn:
            cursor = conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
            return cursor.rowcount > 0

    def save_all(self):
        """No-op for SQLite (auto-commit). Kept for interface compatibility."""
        pass

    def add_bulk(self, papers: List[dict]) -> List[dict]:
        """Add multiple papers at once."""
        result = []
        for paper in papers:
            result.append(self.add(paper))
        return result

    def update_field(self, paper_id: str, field: str, value: Any) -> Optional[dict]:
        """Update a single field on a paper."""
        return self.update(paper_id, {field: value})

    # ============ Tag Methods ============

    def get_all_tags(self) -> List[dict]:
        """Get all tags."""
        with get_db() as conn:
            cursor = conn.execute("SELECT id, name FROM tags ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_or_create_tag(self, name: str) -> dict:
        """Get existing tag or create new one (case-insensitive match)."""
        name = name.strip()
        if not name:
            raise ValueError("Tag name cannot be empty")

        with get_db() as conn:
            # Find existing tag
            cursor = conn.execute(
                "SELECT id, name FROM tags WHERE LOWER(name) = LOWER(?)",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            # Create new tag
            new_tag = {"id": generate_id(), "name": name}
            conn.execute(
                "INSERT INTO tags (id, name) VALUES (?, ?)",
                (new_tag["id"], new_tag["name"])
            )
            return new_tag

    def get_or_create_tags(self, tag_names: List[str]) -> List[dict]:
        """Get or create multiple tags, sorted alphabetically."""
        result = []
        for name in sorted(tag_names):
            name = name.strip()
            if name:
                result.append(self.get_or_create_tag(name))
        return result


# Singleton instance
_paper_repository: Optional[PaperRepository] = None


def get_paper_repository() -> PaperRepository:
    """Get singleton PaperRepository instance."""
    global _paper_repository
    if _paper_repository is None:
        _paper_repository = PaperRepository()
    return _paper_repository
