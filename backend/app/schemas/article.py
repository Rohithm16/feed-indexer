"""
Pydantic schemas for API input/output.
These are separate from SQLAlchemy models — models are for the DB,
schemas are for request/response validation and serialization.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ArticleOut(BaseModel):
    """Article data returned in API responses."""
    id: int
    title: str
    description: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    source_name: str
    category: Optional[str] = None
    country: Optional[str] = None

    model_config = {"from_attributes": True}
