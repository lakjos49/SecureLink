"""
Abuse Report Router
===================
POST /api/reports   – Submit an abuse report for a URL
GET  /api/reports   – List all reports (optionally filter by url_id)
"""

from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from bson.errors import InvalidId
from typing import Optional

from app.database.collections import reports_collection, urls_collection
from app.schemas.report_schema import ReportCreateRequest, ReportResponse
from app.utils.helpers import serialize_doc

router = APIRouter(prefix="/api/reports", tags=["Reports"])


def _build_report_response(doc: dict) -> ReportResponse:
    doc = serialize_doc(doc)
    return ReportResponse(
        id=doc["_id"],
        url_id=doc["url_id"],
        report_type=doc["report_type"],
        description=doc.get("description"),
        created_at=doc["created_at"],
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(payload: ReportCreateRequest):
    """
    Submit an abuse report for a shortened URL.
    The url_id must correspond to an existing URL document.
    """
    try:
        url_oid = ObjectId(payload.url_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid url_id format.")

    url_doc = await urls_collection().find_one({"_id": url_oid})
    if not url_doc:
        raise HTTPException(status_code=404, detail="URL not found.")

    doc = {
        "url_id": url_oid,
        "report_type": payload.report_type,
        "description": payload.description,
        "created_at": datetime.now(timezone.utc),
    }

    result = await reports_collection().insert_one(doc)
    created = await reports_collection().find_one({"_id": result.inserted_id})
    return _build_report_response(created)


@router.get("", response_model=list[ReportResponse])
async def list_reports(url_id: Optional[str] = Query(default=None)):
    """
    List all abuse reports. Optionally filter by url_id query param.
    """
    query = {}
    if url_id:
        try:
            query["url_id"] = ObjectId(url_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="Invalid url_id format.")

    cursor = reports_collection().find(query).sort("created_at", -1)
    docs = await cursor.to_list(length=200)
    return [_build_report_response(d) for d in docs]