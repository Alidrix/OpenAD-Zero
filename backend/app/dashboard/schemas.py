from datetime import datetime

from pydantic import BaseModel


class V2ScanCounters(BaseModel):
    total: int = 0
    active: int = 0
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    stopped: int = 0
    deleted: int = 0


class V2ParsedCounters(BaseModel):
    assets: int = 0
    services: int = 0
    findings: int = 0
    signals: int = 0
    diagnostics: int = 0


class V2SignalCounters(BaseModel):
    smb_open: int = 0
    ldap_open: int = 0
    kerberos_open: int = 0
    http_open: int = 0
    rdp_open: int = 0
    winrm_open: int = 0
    mssql_open: int = 0
    ssh_open: int = 0


class V2TopPort(BaseModel):
    port: int
    protocol: str
    count: int


class V2TopService(BaseModel):
    service_name: str
    count: int


class V2ServiceSummary(BaseModel):
    top_ports: list[V2TopPort] = []
    top_service_names: list[V2TopService] = []


class V2AssetCounters(BaseModel):
    windows_hosts: int = 0
    linux_hosts: int = 0
    unknown_hosts: int = 0


class V2AdSurfaceCounters(BaseModel):
    domain_controller_hints: int = 0
    smb_hosts: int = 0
    ldap_hosts: int = 0
    kerberos_hosts: int = 0
    winrm_hosts: int = 0
    rdp_hosts: int = 0


class V2RecentScan(BaseModel):
    id: str
    name: str
    status: str
    scan_type: str
    tool_name: str | None = None
    progress_percent: int
    created_at: datetime
    updated_at: datetime


class V2RecentDiagnostic(BaseModel):
    id: str
    scan_id: str
    level: str
    message: str
    source_type: str
    created_at: datetime


class V2DashboardSummary(BaseModel):
    scans: V2ScanCounters
    parsed: V2ParsedCounters
    signals: V2SignalCounters
    services: V2ServiceSummary
    assets: V2AssetCounters
    ad_surface: V2AdSurfaceCounters
    recent_scans: list[V2RecentScan] = []
    recent_diagnostics: list[V2RecentDiagnostic] = []
