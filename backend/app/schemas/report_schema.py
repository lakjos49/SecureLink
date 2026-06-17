from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel

ReportType = Literal["phishing", "malware", "spam", "scam"]


class ReportCreateRequest(BaseModel):
    url_id: str
    report_type: ReportType
    description: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    url_id: str
    report_type: str
    description: Optional[str]
    created_at: datetime