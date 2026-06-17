"""
QR Code Router
==============
POST /api/qr/{shortcode}    – Generate and store a QR code for a short URL
GET  /api/qr/{shortcode}    – Download the QR code image
"""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.database.collections import urls_collection
from app.services.qr_service import generate_qr_code

router = APIRouter(prefix="/api/qr", tags=["QR Codes"])


@router.post("/{shortcode}")
async def create_qr_code(shortcode: str):
    """
    Generate a QR code PNG for the given short URL and persist the file path in MongoDB.
    Idempotent: calling this multiple times returns the existing path.
    """
    doc = await urls_collection().find_one({"short_code": shortcode})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found.")

                                                        
    file_path = generate_qr_code(shortcode)

    await urls_collection().update_one(
        {"short_code": shortcode},
        {"$set": {"qr_path": file_path}},
    )

    return {
        "shortcode": shortcode,
        "qr_path": file_path,
        "download_url": f"/api/qr/{shortcode}/download",
    }


@router.get("/{shortcode}/download")
async def download_qr_code(shortcode: str):
    """
    Serve the QR code image as a downloadable PNG file.
    """
    doc = await urls_collection().find_one({"short_code": shortcode})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found.")

    qr_path = doc.get("qr_path")
    if not qr_path or not os.path.exists(qr_path):
        raise HTTPException(
            status_code=404,
            detail="QR code not yet generated. POST /api/qr/{shortcode} first.",
        )

    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"{shortcode}.png",
    )