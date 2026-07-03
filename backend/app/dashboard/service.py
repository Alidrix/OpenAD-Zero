from collections import Counter

from sqlalchemy.orm import Session

from app.dashboard.schemas import (
    V2AdSurfaceCounters,
    V2AssetCounters,
    V2DashboardSummary,
    V2ParsedCounters,
    V2RecentDiagnostic,
    V2RecentScan,
    V2ScanCounters,
    V2ServiceSummary,
    V2SignalCounters,
    V2TopPort,
    V2TopService,
)
from app.db.models import ParseDiagnostic, ParsedAsset, ParsedFinding, ParsedService, ParsedSignal, Scan

ACTIVE_STATUSES = {'queued', 'running', 'stopping'}
SIGNAL_NAMES = tuple(V2SignalCounters.model_fields.keys())
PORT_SIGNALS = {
    'smb_open': {445},
    'ldap_open': {389, 636},
    'kerberos_open': {88},
    'http_open': {80, 443, 8000, 8080, 8443},
    'rdp_open': {3389},
    'winrm_open': {5985, 5986},
    'mssql_open': {1433},
    'ssh_open': {22},
}


def _scope(query, scan_id: str | None):
    return query.filter_by(scan_id=scan_id) if scan_id else query


def _host_count(rows) -> int:
    return len({row.ip_address for row in rows if row.ip_address})


def build_v2_dashboard_summary(db: Session, *, include_deleted: bool = False, scan_id: str | None = None, limit_recent: int = 5) -> V2DashboardSummary:
    if scan_id and db.get(Scan, scan_id) is None:
        raise LookupError('scan_not_found')

    scan_query = db.query(Scan)
    if scan_id:
        scan_query = scan_query.filter(Scan.id == scan_id)
    elif not include_deleted:
        scan_query = scan_query.filter(Scan.deleted_at.is_(None), Scan.status != 'deleted')
    scans = scan_query.all()

    scan_counts = V2ScanCounters(
        total=len(scans),
        active=sum(1 for scan in scans if scan.status in ACTIVE_STATUSES),
        queued=sum(1 for scan in scans if scan.status == 'queued'),
        running=sum(1 for scan in scans if scan.status == 'running'),
        completed=sum(1 for scan in scans if scan.status == 'completed'),
        failed=sum(1 for scan in scans if scan.status == 'failed'),
        stopped=sum(1 for scan in scans if scan.status == 'stopped'),
        deleted=sum(1 for scan in scans if scan.status == 'deleted' or scan.deleted_at is not None),
    )

    assets = _scope(db.query(ParsedAsset), scan_id).all()
    services = _scope(db.query(ParsedService), scan_id).all()
    findings_count = _scope(db.query(ParsedFinding), scan_id).count()
    signals = _scope(db.query(ParsedSignal), scan_id).all()
    diagnostics = _scope(db.query(ParseDiagnostic), scan_id).all()

    parsed = V2ParsedCounters(assets=len(assets), services=len(services), findings=findings_count, signals=len(signals), diagnostics=len(diagnostics))

    signal_counter = Counter(row.signal for row in signals if row.signal in SIGNAL_NAMES)
    for service in services:
        if service.state == 'open':
            for signal_name, ports in PORT_SIGNALS.items():
                if service.port in ports:
                    signal_counter[signal_name] += 1
    signal_summary = V2SignalCounters(**{name: signal_counter[name] for name in SIGNAL_NAMES})

    top_ports = [V2TopPort(port=port, protocol=proto, count=count) for (port, proto), count in Counter((svc.port, svc.protocol or 'tcp') for svc in services).most_common(10)]
    top_names = [V2TopService(service_name=name, count=count) for name, count in Counter((svc.service_name or 'unknown') for svc in services).most_common(10)]

    windows_hosts = sum(1 for asset in assets if (asset.os_family or '').lower() == 'windows' or 'windows' in (asset.os_name or '').lower())
    linux_hosts = sum(1 for asset in assets if (asset.os_family or '').lower() == 'linux' or 'linux' in (asset.os_name or '').lower())
    asset_summary = V2AssetCounters(windows_hosts=windows_hosts, linux_hosts=linux_hosts, unknown_hosts=max(0, len(assets) - windows_hosts - linux_hosts))

    by_signal = {name: [row for row in signals if row.signal == name] for name in SIGNAL_NAMES}
    by_port = {name: [svc for svc in services if svc.state == 'open' and svc.port in ports] for name, ports in PORT_SIGNALS.items()}
    ad_surface = V2AdSurfaceCounters(
        domain_controller_hints=len({row.asset_id or row.value for row in by_signal['ldap_open'] + by_signal['kerberos_open']}),
        smb_hosts=_host_count(by_port['smb_open']) or len(by_signal['smb_open']),
        ldap_hosts=_host_count(by_port['ldap_open']) or len(by_signal['ldap_open']),
        kerberos_hosts=_host_count(by_port['kerberos_open']) or len(by_signal['kerberos_open']),
        winrm_hosts=_host_count(by_port['winrm_open']) or len(by_signal['winrm_open']),
        rdp_hosts=_host_count(by_port['rdp_open']) or len(by_signal['rdp_open']),
    )

    recent_scan_rows = sorted(scans, key=lambda scan: scan.created_at, reverse=True)[:max(0, limit_recent)]
    recent_diagnostic_rows = sorted(diagnostics, key=lambda row: row.created_at, reverse=True)[:max(0, limit_recent)]

    return V2DashboardSummary(
        scans=scan_counts,
        parsed=parsed,
        signals=signal_summary,
        services=V2ServiceSummary(top_ports=top_ports, top_service_names=top_names),
        assets=asset_summary,
        ad_surface=ad_surface,
        recent_scans=[V2RecentScan.model_validate(scan, from_attributes=True) for scan in recent_scan_rows],
        recent_diagnostics=[V2RecentDiagnostic.model_validate(row, from_attributes=True) for row in recent_diagnostic_rows],
    )
