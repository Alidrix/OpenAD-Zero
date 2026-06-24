from datetime import datetime
from pydantic import BaseModel

class ReportGenerateRequest(BaseModel):
    include_sections: list[str] | None = None

class ReportResponse(BaseModel):
    id: str
    mission_id: str
    status: str
    title: str
    markdown_path: str | None
    html_path: str | None
    metadata_path: str | None
    sections_json: dict | None
    generated_at: datetime

class ReportPreviewResponse(BaseModel):
    format: str
    content: str
    truncated: bool = False
