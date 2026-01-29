from uuid import UUID

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """Schema for creating a tag"""
    name: str = Field(..., min_length=1, max_length=50)


class TagResponse(BaseModel):
    """Schema for tag response"""
    id: UUID
    name: str

    class Config:
        from_attributes = True


class TagWithCountResponse(TagResponse):
    """Schema for tag with paper count"""
    paper_count: int
