"""
URL Router
==========
POST /api/urls/create   – Shorten + analyze a URL
GET  /api/urls          – List all shortened URLs
GET  /api/urls/{id}     – Get a single URL by MongoDB _id
DELETE /api/urls/{id}   – Delete a URL
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId

from app.database.collections import urls_collection
from app.schemas.url_schema import URLCreateRequest, URLResponse
from app.services.security.url_analyzer import analyze_url
from app.utils.helpers import generate_short_code, serialize_doc
from app.core.config import settings

router = APIRouter(prefix="/api/urls", tags=["URLs"])


def _build_response(doc: dict) -> URLResponse:
    doc = serialize_doc(doc)
    return URLResponse(
        id=doc["_id"],
        original_url=doc["original_url"],
        short_code=doc["short_code"],
        short_url=f"{settings.BASE_URL}/r/{doc['short_code']}",
        risk_score=doc["risk_score"],
        classification=doc["classification"],
        status=doc["status"],
        clicks=doc["clicks"],
        created_at=doc["created_at"],
        expires_at=doc.get("expires_at"),
        qr_path=doc.get("qr_path"),
    )


@router.post("/create", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(payload: URLCreateRequest):
    """
    Submit a URL to be shortened and analyzed.
    Optionally supply a custom alias and/or expiry datetime.
    """
    collection = urls_collection()

                          
    if payload.custom_alias:
        existing = await collection.find_one({"short_code": payload.custom_alias})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Alias '{payload.custom_alias}' is already taken.",
            )
        short_code = payload.custom_alias
    else:
                                        
        for _ in range(10):
            candidate = generate_short_code()
            if not await collection.find_one({"short_code": candidate}):
                short_code = candidate
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate a unique short code. Try again.",
            )

                       
    analysis = analyze_url(payload.original_url)

    doc = {
        "original_url": payload.original_url,
        "short_code": short_code,
        "risk_score": analysis["risk_score"],
        "classification": analysis["classification"],
        "analysis_details": analysis["details"],
        "status": "active",
        "clicks": 0,
        "created_at": datetime.now(timezone.utc),
        "expires_at": payload.expires_at,
        "qr_path": None,
    }

    result = await collection.insert_one(doc)
    created = await collection.find_one({"_id": result.inserted_id})
    return _build_response(created)


@router.get("", response_model=list[URLResponse])
async def list_urls(skip: int = 0, limit: int = 50):
    """Return all shortened URLs, newest first."""
    cursor = urls_collection().find().sort("created_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)
    return [_build_response(d) for d in docs]


@router.get("/{id}", response_model=URLResponse)
async def get_url(id: str):
    """Fetch a single URL document by its MongoDB ObjectId."""
    try:
        oid = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid URL id format.")

    doc = await urls_collection().find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="URL not found.")
    return _build_response(doc)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(id: str):
    """Permanently delete a shortened URL."""
    try:
        oid = ObjectId(id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid URL id format.")

    result = await urls_collection().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="URL not found.")