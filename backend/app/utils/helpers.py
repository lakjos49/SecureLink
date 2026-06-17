import random
import string
from bson import ObjectId


def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


def serialize_doc(doc: dict) -> dict:
    """Recursively convert ObjectId fields to strings for JSON serialization."""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_doc(i) if isinstance(i, dict) else (str(i) if isinstance(i, ObjectId) else i)
                for i in value
            ]
        else:
            result[key] = value
    return result