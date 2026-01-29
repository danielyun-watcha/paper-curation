from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from app.database import load_data, save_data, generate_id
from app.schemas import TagCreate, TagResponse, TagWithCountResponse

router = APIRouter()


@router.get("", response_model=List[TagWithCountResponse])
async def list_tags():
    """List all tags with paper count, sorted by usage frequency"""
    data = load_data()

    # Count papers per tag
    tag_counts = {}
    for paper in data["papers"]:
        for tag in paper["tags"]:
            tag_id = tag["id"]
            if tag_id not in tag_counts:
                tag_counts[tag_id] = {"id": tag["id"], "name": tag["name"], "paper_count": 0}
            tag_counts[tag_id]["paper_count"] += 1

    # Add tags with no papers
    for tag in data["tags"]:
        if tag["id"] not in tag_counts:
            tag_counts[tag["id"]] = {"id": tag["id"], "name": tag["name"], "paper_count": 0}

    # Sort by paper_count descending, then by name
    result = sorted(tag_counts.values(), key=lambda t: (-t["paper_count"], t["name"]))

    return result


@router.post("", response_model=TagResponse)
async def create_tag(tag_in: TagCreate):
    """Create a new tag"""
    data = load_data()
    name = tag_in.name.strip().lower()

    # Check for duplicate
    if any(t["name"] == name for t in data["tags"]):
        raise HTTPException(status_code=409, detail=f"Tag '{name}' already exists")

    tag = {"id": generate_id(), "name": name}
    data["tags"].append(tag)
    save_data(data)

    return tag


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str):
    """Delete a tag"""
    data = load_data()
    tag_idx = next((i for i, t in enumerate(data["tags"]) if t["id"] == tag_id), None)

    if tag_idx is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    data["tags"].pop(tag_idx)

    # Remove tag from all papers
    for paper in data["papers"]:
        paper["tags"] = [t for t in paper["tags"] if t["id"] != tag_id]

    save_data(data)

    return {"message": "Tag deleted successfully"}
