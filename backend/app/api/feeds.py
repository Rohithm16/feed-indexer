"""
Feeds API — exposes the list of registered providers for the settings UI.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

from app.providers.registry import get_all_providers

router = APIRouter(prefix="/api/feeds", tags=["feeds"])


class FeedOut(BaseModel):
    provider_name: str
    feed_name: str
    url: str
    category: str
    country: str


class ProviderOut(BaseModel):
    name: str
    feeds: List[FeedOut]


@router.get("/", response_model=List[ProviderOut])
def list_providers():
    """
    Returns all registered providers and their feeds.
    Used by the settings page to let users pick trusted publishers.
    """
    result = []
    for provider in get_all_providers():
        result.append(ProviderOut(
            name=provider.name,
            feeds=[
                FeedOut(
                    provider_name=provider.name,
                    feed_name=feed.name,
                    url=feed.url,
                    category=feed.category,
                    country=feed.country,
                )
                for feed in provider.feeds
            ],
        ))
    return result
