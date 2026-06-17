"""
Redirect Router
===============
GET /r/{shortcode}              – Redirect gateway (with risk check)
GET /api/preview/{shortcode}    – Preview info before redirect
"""

from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.database.collections import urls_collection
from app.schemas.url_schema import URLPreviewResponse
from app.services.analytics_service import record_click
from app.utils.helpers import serialize_doc

router = APIRouter(tags=["Redirect"])

SAFE_CLASSIFICATIONS = {"SAFE", "LOW_RISK"}


@router.get("/r/{shortcode}")
async def redirect_shortcode(shortcode: str, request: Request):
    """
    Redirect gateway.

    - SAFE / LOW_RISK  → 302 redirect to destination.
    - SUSPICIOUS / HIGH_RISK → return a JSON warning payload instead of redirecting.
    """
    doc = await urls_collection().find_one({"short_code": shortcode})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found.")

                  
    if doc.get("expires_at") and doc["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This short URL has expired.")

                             
    await urls_collection().update_one(
        {"short_code": shortcode},
        {"$inc": {"clicks": 1}},
    )

                                                    
    ip = request.headers.get("x-forwarded-for", request.client.host)
    ua = request.headers.get("user-agent", "")
    await record_click(str(doc["_id"]), ip, ua)

    classification = doc.get("classification", "SAFE")
    original_url = doc["original_url"]

    if classification in SAFE_CLASSIFICATIONS:
        return RedirectResponse(url=original_url, status_code=302)

                                                                         
    return JSONResponse(
        status_code=200,
        content={
            "warning": True,
            "risk_score": doc["risk_score"],
            "classification": classification,
            "destination": original_url,
            "message": (
                "This URL has been flagged as potentially unsafe. "
                "Proceed only if you trust the destination."
            ),
        },
    )


@router.get("/api/preview/{shortcode}", response_model=URLPreviewResponse)
async def preview_url(shortcode: str):
    """
    Return metadata about a short URL without triggering a redirect or recording a click.
    """
    doc = await urls_collection().find_one({"short_code": shortcode})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    parsed = urlparse(doc["original_url"])
    domain = parsed.netloc or parsed.path

    return URLPreviewResponse(
        domain=domain,
        risk_score=doc["risk_score"],
        classification=doc["classification"],
        clicks=doc["clicks"],
        created_at=doc["created_at"],
    )