from datetime import datetime

from pydantic import BaseModel, ConfigDict


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ParsedAssetRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    ip_address: str
    hostname: str | None = None
    fqdn: str | None = None
    mac_address: str | None = None
    os_family: str | None = None
    os_name: str | None = None
    confidence: float
    tags_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class ParsedServiceRead(_Orm):
    id: str
    scan_id: str
    asset_id: str | None = None
    source_type: str
    source_id: str | None = None
    ip_address: str
    port: int
    protocol: str
    service_name: str | None = None
    product: str | None = None
    version: str | None = None
    state: str
    confidence: float
    tags_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class ParsedFindingRead(_Orm):
    id: str
    scan_id: str
    asset_id: str | None = None
    service_id: str | None = None
    source_type: str
    source_id: str | None = None
    title: str
    description: str
    severity: str
    confidence: float
    tags_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class ParsedSignalRead(_Orm):
    id: str
    scan_id: str
    asset_id: str | None = None
    service_id: str | None = None
    finding_id: str | None = None
    source_type: str
    source_id: str | None = None
    signal: str
    value: str
    confidence: float
    created_at: datetime


class ParseDiagnosticRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    level: str
    message: str
    details_json: dict | None = None
    created_at: datetime


class ParsePersistedResult(BaseModel):
    scan_id: str
    assets_created: int
    services_created: int
    findings_created: int
    signals_created: int
    diagnostics_created: int
    status: str


class NormalizationResultRead(BaseModel):
    scan_id: str
    source_type: str | None = None
    source_id: str | None = None
    assets_created: int = 0
    services_created: int = 0
    findings_created: int = 0
    signals_created: int = 0
    ad_objects_created: int = 0
    ad_relations_created: int = 0
    attack_paths_created: int = 0
    credential_risks_created: int = 0
    diagnostics_created: int = 0
    errors: list[str] = []
    warnings: list[str] = []


class NormalizedSummaryRead(BaseModel):
    scan_id: str
    assets_count: int
    services_count: int
    findings_count: int
    signals_count: int
    diagnostics_count: int
    ad_objects_count: int
    high_value_targets_count: int
    ad_relations_count: int
    attack_paths_count: int
    credential_risks_count: int
    critical_findings_count: int
    exposed_services_count: int


class ParsedADObjectRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    object_id: str | None = None
    object_type: str
    name: str | None = None
    domain: str | None = None
    distinguished_name: str | None = None
    sam_account_name: str | None = None
    sid: str | None = None
    enabled: bool | None = None
    high_value: bool
    owned: bool
    properties_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class ParsedADRelationRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    source_object_id: str
    target_object_id: str
    relation_type: str
    is_abusable: bool
    risk_level: str
    properties_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class ParsedAttackPathRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    path_type: str
    source_object_id: str | None = None
    target_object_id: str | None = None
    target_label: str | None = None
    risk_level: str
    length: int
    nodes_json: list | None = None
    edges_json: list | None = None
    summary: str | None = None
    created_at: datetime
    updated_at: datetime


class ParsedCredentialRiskRead(_Orm):
    id: str
    scan_id: str
    source_type: str
    source_id: str | None = None
    risk_type: str
    principal: str | None = None
    asset_ip: str | None = None
    domain: str | None = None
    risk_level: str
    evidence: str | None = None
    properties_json: dict | None = None
    created_at: datetime
    updated_at: datetime
