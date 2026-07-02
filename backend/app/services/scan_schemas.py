from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scan_type: str = Field(min_length=1, max_length=120)
    tool_name: str | None = Field(default=None, max_length=120)
    mission_id: str | None = None


class ScanRename(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ScanStepRead(_Orm):
    id: str
    scan_id: str
    order: int
    name: str
    status: str
    progress_percent: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ScanEventRead(_Orm):
    id: str
    scan_id: str
    event_type: str
    message: str
    payload_json: dict | None
    created_at: datetime


class ScanArtifactRead(_Orm):
    id: str
    scan_id: str
    artifact_type: str
    path: str
    sha256: str | None
    size_bytes: int | None
    created_at: datetime


class ScanListItem(_Orm):
    id: str
    mission_id: str | None
    name: str
    scan_type: str
    tool_name: str | None
    status: str
    progress_percent: int
    current_step: str | None
    rq_job_id: str | None
    started_at: datetime | None
    finished_at: datetime | None
    stopped_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    renamed_at: datetime | None


class ScanRead(ScanListItem):
    steps: list[ScanStepRead] = []
    events: list[ScanEventRead] = []
    artifacts: list[ScanArtifactRead] = []
