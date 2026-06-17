from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator


class URLCreateRequest(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator("original_url")
    @classmethod
    def must_be_valid_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_alias")
    @classmethod
    def alias_alphanumeric(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.replace("-", "").replace("_", "").isalnum():
                raise ValueError("Custom alias must be alphanumeric (hyphens and underscores allowed).")
            if len(v) < 3 or len(v) > 30:
                raise ValueError("Custom alias must be between 3 and 30 characters.")
        return v


class URLResponse(BaseModel):
    id: str
    original_url: str
    short_code: str
    short_url: str
    risk_score: int
    classification: str
    status: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    qr_path: Optional[str] = None


class URLPreviewResponse(BaseModel):
    domain: str
    risk_score: int
    classification: str
    clicks: int
    created_at: datetime