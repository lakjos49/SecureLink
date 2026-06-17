"""
QR Code Generation Service
===========================
Generates a QR code PNG for a given short URL and saves it to disk.
"""

import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from app.core.config import settings


def generate_qr_code(short_code: str) -> str:
    """
    Generate a QR code image for the short URL.

    Parameters
    ----------
    short_code : str
        The unique short code for the URL.

    Returns
    -------
    str
        Relative file path to the saved QR image (e.g. "storage/qr/aX7pQ2.png").
    """
    redirect_url = f"{settings.BASE_URL}/r/{short_code}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(redirect_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    os.makedirs(settings.QR_STORAGE_PATH, exist_ok=True)
    file_path = os.path.join(settings.QR_STORAGE_PATH, f"{short_code}.png")
    img.save(file_path)

    return file_path