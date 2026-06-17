"""
Analytics Router
================
GET /api/analytics/{url_id}  – Full click analytics for a shortened URL
"""

from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId

from app.database.collections import urls_collection
from app.services.analytics_service import get_analytics_for_url

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/{url_id}")
async def get_url_analytics(url_id: str):
    """
    Return click analytics for a URL identified by its MongoDB ObjectId.

    Response includes:
    - total_clicks
    - click_history (last 100 events)
    - browser_breakdown
    - device_breakdown
    - daily_counts
    """
    try:
        oid = ObjectId(url_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid URL id format.")

    doc = await urls_collection().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="URL not found.")

    return await get_analytics_for_url(url_id)