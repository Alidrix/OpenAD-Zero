from collections import Counter
from collections.abc import Iterable

from sqlalchemy.orm import Query, Session

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
from app.db.models import (
    ParsedAsset,
    ParsedFinding,
    ParseDiagnostic,
    ParsedService,
    ParsedSignal,
    Scan,
)

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


def _is_soft_deleted(scan: Scan) -> bool:
    return scan.deleted_at is not None or scan.status == 'deleted'


def _scope_scans(db: Session, include_deleted: bool, scan_id: str | None) -> list[Scan]:
    query = db.query(Scan)

    if scan_id:
        scan = db.get(Scan, scan_id)
        if scan is None:
            raise LookupError('scan_not_found')
        return [scan]

    if not include_deleted:
        query = query.filter(Scan.deleted_at.is_(None), Scan.status != 'deleted')

    return query.all()


def _scope_parsed_query(
    query: Query,
    model: type[ParsedAsset | ParsedService | ParsedFinding | ParsedSignal | ParseDiagnostic],
    scan_ids: set[str],
    scan_id: str | None,
) -> Query:
    if scan_id:
        return query.filter(model.scan_id == scan_id)

    if not scan_ids:
        return query.filter(False)

    return query.filter(model.scan_id.in_(scan_ids))


def _host_count(rows: Iterable[ParsedService]) -> int:
    return len({row.ip_address for row in rows if row.ip_address})


def _build_scan_counters(scans: list[Scan]) -> V2ScanCounters:
    return V2ScanCounters(
        total=len(scans),
        active=sum(1 for scan in scans if scan.status in ACTIVE_STATUSES),
        queued=sum(1 for scan in scans if scan.status == 'queued'),
        running=sum(1 for scan in scans if scan.status == 'running'),
        completed=sum(1 for scan in scans if scan.status == 'completed'),
        failed=sum(1 for scan in scans if scan.status == 'failed'),
        stopped=sum(1 for scan in scans if scan.status == 'stopped'),
        deleted=sum(1 for scan in scans if _is_soft_deleted(scan)),
    )


def _build_signal_counters(
    services: list[ParsedService],
    signals: list[ParsedSignal],
) -> V2SignalCounters:
    signal_counter = Counter(row.signal for row in signals if row.signal in SIGNAL_NAMES)

    for service in services:
        if service.state != 'open':
            continue

        for signal_name, ports in PORT_SIGNALS.items():
            if service.port in ports:
                signal_counter[signal_name] += 1

    return V2SignalCounters(**{name: signal_counter[name] for name in SIGNAL_NAMES})


def _build_service_summary(services: list[ParsedService]) -> V2ServiceSummary:
    top_ports = [
        V2TopPort(port=port, protocol=protocol, count=count)
        for (port, protocol), count in Counter(
            (service.port, service.protocol or 'tcp') for service in services
        ).most_common(10)
    ]
    top_service_names = [
        V2TopService(service_name=service_name, count=count)
        for service_name, count in Counter(service.service_name or 'unknown' for service in services).most_common(10)
    ]

    return V2ServiceSummary(top_ports=top_ports, top_service_names=top_service_names)


def _build_asset_counters(assets: list[ParsedAsset]) -> V2AssetCounters:
    windows_hosts = sum(
        1
        for asset in assets
        if (asset.os_family or '').lower() == 'windows' or 'windows' in (asset.os_name or '').lower()
    )
    linux_hosts = sum(
        1 for asset in assets if (asset.os_family or '').lower() == 'linux' or 'linux' in (asset.os_name or '').lower()
    )

    return V2AssetCounters(
        windows_hosts=windows_hosts,
        linux_hosts=linux_hosts,
        unknown_hosts=max(0, len(assets) - windows_hosts - linux_hosts),
    )


def _build_ad_surface(
    services: list[ParsedService],
    signals: list[ParsedSignal],
) -> V2AdSurfaceCounters:
    by_signal = {name: [row for row in signals if row.signal == name] for name in SIGNAL_NAMES}
    by_port = {
        name: [service for service in services if service.state == 'open' and service.port in ports]
        for name, ports in PORT_SIGNALS.items()
    }

    return V2AdSurfaceCounters(
        domain_controller_hints=len(
            {row.asset_id or row.value for row in by_signal['ldap_open'] + by_signal['kerberos_open']}
        ),
        smb_hosts=_host_count(by_port['smb_open']) or len(by_signal['smb_open']),
        ldap_hosts=_host_count(by_port['ldap_open']) or len(by_signal['ldap_open']),
        kerberos_hosts=_host_count(by_port['kerberos_open']) or len(by_signal['kerberos_open']),
        winrm_hosts=_host_count(by_port['winrm_open']) or len(by_signal['winrm_open']),
        rdp_hosts=_host_count(by_port['rdp_open']) or len(by_signal['rdp_open']),
    )


def build_v2_dashboard_summary(
    db: Session,
    *,
    include_deleted: bool = False,
    scan_id: str | None = None,
    limit_recent: int = 5,
) -> V2DashboardSummary:
    scans = _scope_scans(db, include_deleted=include_deleted, scan_id=scan_id)
    scan_ids = {scan.id for scan in scans}

    assets = _scope_parsed_query(db.query(ParsedAsset), ParsedAsset, scan_ids, scan_id).all()
    services = _scope_parsed_query(db.query(ParsedService), ParsedService, scan_ids, scan_id).all()
    findings_count = _scope_parsed_query(
        db.query(ParsedFinding),
        ParsedFinding,
        scan_ids,
        scan_id,
    ).count()
    signals = _scope_parsed_query(db.query(ParsedSignal), ParsedSignal, scan_ids, scan_id).all()
    diagnostics = _scope_parsed_query(
        db.query(ParseDiagnostic),
        ParseDiagnostic,
        scan_ids,
        scan_id,
    ).all()

    recent_limit = max(0, limit_recent)
    recent_scans = sorted(scans, key=lambda scan: scan.created_at, reverse=True)[:recent_limit]
    recent_diagnostics = sorted(
        diagnostics,
        key=lambda diagnostic: diagnostic.created_at,
        reverse=True,
    )[:recent_limit]

    return V2DashboardSummary(
        scans=_build_scan_counters(scans),
        parsed=V2ParsedCounters(
            assets=len(assets),
            services=len(services),
            findings=findings_count,
            signals=len(signals),
            diagnostics=len(diagnostics),
        ),
        signals=_build_signal_counters(services, signals),
        services=_build_service_summary(services),
        assets=_build_asset_counters(assets),
        ad_surface=_build_ad_surface(services, signals),
        recent_scans=[V2RecentScan.model_validate(scan, from_attributes=True) for scan in recent_scans],
        recent_diagnostics=[
            V2RecentDiagnostic.model_validate(diagnostic, from_attributes=True) for diagnostic in recent_diagnostics
        ],
    )
