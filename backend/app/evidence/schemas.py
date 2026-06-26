from datetime import datetime

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: str
    mission_id: str
    label: str
    category: str
    description: str | None
    filename: str
    stored_path: str
    sha256: str
    size_bytes: int
    mime_type: str | None
    source: str
    preview_available: bool
    metadata_json: dict | None
    created_at: datetime


class EvidenceLinkCreate(BaseModel):
    target_type: str
    target_id: str


class EvidenceLinkResponse(BaseModel):
    id: str
    mission_id: str
    evidence_id: str
    target_type: str
    target_id: str
    created_at: datetime
