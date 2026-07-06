from __future__ import annotations

import xml.etree.ElementTree as ET

from app.parsing.service import artifact_path_under_evidence, is_supported_nmap_artifact
from app.parsing.signals import service_to_signal

DETECTED_ALIASES = {
    'smb_open': 'smb_detected',
    'ldap_open': 'ldap_detected',
    'kerberos_open': 'kerberos_detected',
    'http_open': 'http_detected',
    'rdp_open': 'rdp_detected',
    'winrm_open': 'winrm_detected',
    'mssql_open': 'mssql_detected',
}


def parse_nmap_artifacts(ctx, artifacts) -> None:
    for artifact in artifacts:
        ctx.signal('scan_artifact', artifact.id, 'artifact_uploaded')
        if 'bloodhound' in f'{artifact.artifact_type} {artifact.path}'.lower():
            ctx.signal('scan_artifact', artifact.id, 'bloodhound_artifact_present')
        if not is_supported_nmap_artifact(artifact):
            continue
        path = artifact_path_under_evidence(artifact.path)
        if path is None:
            ctx.diagnostic(
                'scan_artifact',
                artifact.id,
                'warning',
                'Artifact path is outside the configured evidence directory',
                {'path': artifact.path},
            )
            continue
        if not path.exists():
            ctx.diagnostic('scan_artifact', artifact.id, 'warning', 'Artifact file does not exist', {'path': str(path)})
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            ctx.diagnostic(
                'scan_artifact',
                artifact.id,
                'warning',
                'Invalid Nmap XML artifact',
                {'path': str(path), 'error': str(exc)},
            )
            continue
        except OSError as exc:
            ctx.diagnostic(
                'scan_artifact',
                artifact.id,
                'warning',
                'Unable to read artifact file',
                {'path': str(path), 'error': str(exc)},
            )
            continue
        _parse_root(ctx, artifact.id, root)


def _parse_root(ctx, artifact_id: str, root) -> None:
    for host in root.findall('host'):
        status = host.find('status')
        if status is not None and status.get('state') not in (None, 'up'):
            continue
        addresses = host.findall('address')
        ip = None
        mac = None
        for addr in addresses:
            atype = addr.get('addrtype')
            if atype in {'ipv4', 'ipv6'} and not ip:
                ip = addr.get('addr')
            if atype == 'mac':
                mac = addr.get('addr')
        if not ip:
            continue
        hostname = None
        hn = host.find('hostnames/hostname')
        if hn is not None:
            hostname = hn.get('name')
        os_name = None
        osmatch = host.find('os/osmatch')
        if osmatch is not None:
            os_name = osmatch.get('name')
        asset = ctx.asset(
            'scan_artifact',
            artifact_id,
            ip,
            hostname=hostname,
            fqdn=hostname if hostname and '.' in hostname else None,
            mac=mac,
            os_name=os_name,
            confidence=0.9,
        )
        ctx.signal('scan_artifact', artifact_id, 'host_discovered', asset=asset, confidence=0.9)
        if os_name and 'windows' in os_name.lower():
            ctx.signal('scan_artifact', artifact_id, 'windows_host_detected', asset=asset, confidence=0.8)
        if os_name and 'linux' in os_name.lower():
            ctx.signal('scan_artifact', artifact_id, 'linux_host_detected', asset=asset, confidence=0.8)
        for port in host.findall('ports/port'):
            state = port.find('state')
            state_name = state.get('state') if state is not None else None
            if state_name != 'open':
                continue
            service = port.find('service')
            service_name = service.get('name') if service is not None else None
            product = service.get('product') if service is not None else None
            version = service.get('version') if service is not None else None
            svc = ctx.service(
                'scan_artifact',
                artifact_id,
                ip,
                port.get('portid'),
                port.get('protocol') or 'tcp',
                service_name,
                product,
                version,
                'open',
                confidence=0.9,
            )
            sig = service_to_signal(port.get('portid'), port.get('protocol') or 'tcp', service_name)
            if sig:
                ctx.signal('scan_artifact', artifact_id, sig, asset=asset, service=svc, confidence=0.9)
                alias = DETECTED_ALIASES.get(sig)
                if alias:
                    ctx.signal('scan_artifact', artifact_id, alias, asset=asset, service=svc, confidence=0.9)
