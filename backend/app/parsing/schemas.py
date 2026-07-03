from datetime import datetime
from pydantic import BaseModel, ConfigDict

class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class ParsedAssetRead(_Orm):
    id: str; scan_id: str; source_type: str; source_id: str | None = None; ip_address: str
    hostname: str | None = None; fqdn: str | None = None; mac_address: str | None = None
    os_family: str | None = None; os_name: str | None = None; confidence: float; tags_json: dict | None = None
    created_at: datetime; updated_at: datetime

class ParsedServiceRead(_Orm):
    id: str; scan_id: str; asset_id: str | None = None; source_type: str; source_id: str | None = None
    ip_address: str; port: int; protocol: str; service_name: str | None = None; product: str | None = None
    version: str | None = None; state: str; confidence: float; tags_json: dict | None = None
    created_at: datetime; updated_at: datetime

class ParsedFindingRead(_Orm):
    id: str; scan_id: str; asset_id: str | None = None; service_id: str | None = None; source_type: str
    source_id: str | None = None; title: str; description: str; severity: str; confidence: float
    tags_json: dict | None = None; created_at: datetime; updated_at: datetime

class ParsedSignalRead(_Orm):
    id: str; scan_id: str; asset_id: str | None = None; service_id: str | None = None; finding_id: str | None = None
    source_type: str; source_id: str | None = None; signal: str; value: str; confidence: float; created_at: datetime

class ParseDiagnosticRead(_Orm):
    id: str; scan_id: str; source_type: str; source_id: str | None = None; level: str; message: str
    details_json: dict | None = None; created_at: datetime

class ParsePersistedResult(BaseModel):
    scan_id: str
    assets_created: int
    services_created: int
    findings_created: int
    signals_created: int
    diagnostics_created: int
    status: str
