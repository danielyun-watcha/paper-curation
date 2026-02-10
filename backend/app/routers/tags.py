from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.db.connection import get_db
from app.repositories.paper_repository import get_paper_repository, generate_id
from app.schemas import TagCreate, TagResponse, TagWithCountResponse

router = APIRouter()


@router.get("", response_model=List[TagWithCountResponse])
async def list_tags():
    """List all tags with paper count, sorted by usage frequency"""
    with get_db() as conn:
        # Get all tags with paper counts using SQL
        cursor = conn.execute("""
            SELECT t.id, t.name, COUNT(pt.paper_id) as paper_count
            FROM tags t
            LEFT JOIN paper_tags pt ON t.id = pt.tag_id
            GROUP BY t.id, t.name
            ORDER BY paper_count DESC, t.name ASC
        """)

        result = [
            {"id": row["id"], "name": row["name"], "paper_count": row["paper_count"]}
            for row in cursor.fetchall()
        ]

    return result


@router.post("", response_model=TagResponse)
async def create_tag(tag_in: TagCreate):
    """Create a new tag"""
    name = tag_in.name.strip()

    with get_db() as conn:
        # Check for duplicate (case-insensitive)
        cursor = conn.execute(
            "SELECT id, name FROM tags WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        existing = cursor.fetchone()

        if existing:
            raise HTTPException(status_code=409, detail=f"Tag '{name}' already exists")

        tag = {"id": generate_id(), "name": name}
        conn.execute(
            "INSERT INTO tags (id, name) VALUES (?, ?)",
            (tag["id"], tag["name"])
        )

    return tag


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    """Delete a tag"""
    with get_db() as conn:
        # Check if tag exists
        cursor = conn.execute("SELECT id FROM tags WHERE id = ?", (tag_id,))
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Delete tag (CASCADE will remove paper_tags entries)
        conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))

    return {"message": "Tag deleted successfully"}
