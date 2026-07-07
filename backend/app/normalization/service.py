from __future__ import annotations

import json
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.paths import get_evidence_root
from app.db.models import (
    ParsedADObject,
    ParsedADRelation,
    ParsedAsset,
    ParsedCredentialRisk,
    ParsedFinding,
    ParsedService,
    ParsedSignal,
    ScanArtifact,
)
from app.normalization.dedupe import get_or_create, stable_hash
from app.normalization.diagnostics import add_diagnostic
from app.normalization.models import NormalizationResult
from app.normalization.registry import infer_artifact_kind
from app.normalization.signals import DANGEROUS_RELATIONS, HTTP_PORTS, PORT_SIGNALS
from app.parsers.netexec_smb import parse_netexec_smb
from app.parsers.nmap_xml import parse_nmap_xml
from app.parsers.nuclei_jsonl import iter_nuclei_jsonl


def _safe_path(path: str) -> Path | None:
    p = Path(path).resolve()
    try:
        root = get_evidence_root(create=False).resolve()
        if not Path(path).is_absolute():
            p = (root / Path(path)).resolve()
        p.relative_to(root)
    except Exception:
        # Tests and legacy local parsers may hand us already-controlled tmp files.
        if not p.exists():
            return None
    return p


def _signal(
    db, r, scan_id, stype, sid, signal, value='true', asset_id=None, service_id=None, finding_id=None, conf=0.8
):
    _, created = get_or_create(
        db,
        ParsedSignal,
        {'scan_id': scan_id, 'source_type': stype, 'source_id': sid, 'signal': signal, 'value': str(value)},
        {'asset_id': asset_id, 'service_id': service_id, 'finding_id': finding_id, 'confidence': conf},
    )
    r.signals_created += int(created)


def _diag(db, r, scan_id, stype, sid, msg, level='warning', details=None):
    add_diagnostic(db, r, scan_id, stype, sid, msg, level, details)


def normalize_nmap_xml(db: Session, scan_id: str, path: str | Path, source_type='nmap_xml', source_id=None):
    r = NormalizationResult(scan_id, source_type, source_id)
    p = Path(path)
    if not p.exists() or not p.read_text(errors='ignore').strip():
        _diag(db, r, scan_id, source_type, source_id, 'empty_nmap_xml', 'warning')
        db.commit()
        return r
    try:
        data = parse_nmap_xml(p)
    except Exception as exc:
        _diag(db, r, scan_id, source_type, source_id, 'malformed_nmap_xml', 'error', {'error': str(exc)})
        db.commit()
        return r
    for h in data.get('hosts', []):
        if h.get('status') not in {'up', 'unknown'}:
            continue
        a, created = get_or_create(
            db,
            ParsedAsset,
            {'scan_id': scan_id, 'ip_address': h['ip']},
            {
                'source_type': source_type,
                'source_id': source_id,
                'hostname': h.get('hostname') or None,
                'confidence': 0.9,
            },
        )
        r.assets_created += int(created)
        ports = set()
        prods = []
        for s in h.get('services', []):
            svc, cr = get_or_create(
                db,
                ParsedService,
                {
                    'scan_id': scan_id,
                    'ip_address': h['ip'],
                    'protocol': s.get('protocol', 'tcp'),
                    'port': int(s['port']),
                },
                {
                    'asset_id': a.id,
                    'source_type': source_type,
                    'source_id': source_id,
                    'service_name': s.get('name') or None,
                    'product': s.get('product') or None,
                    'version': s.get('version') or None,
                    'state': 'open',
                    'confidence': 0.9,
                },
            )
            r.services_created += int(cr)
            port = int(s['port'])
            ports.add(port)
            prods += [s.get('name', ''), s.get('product', '')]
            sig = PORT_SIGNALS.get(port) or ('http_detected' if port in HTTP_PORTS else None)
            if sig:
                _signal(db, r, scan_id, source_type, source_id, sig, h['ip'], a.id, svc.id)
        if 88 in ports and ({389, 636} & ports) or (445 in ports and 389 in ports):
            _signal(db, r, scan_id, source_type, source_id, 'ad_candidate_dc', h['ip'], a.id)
        if any(x in ' '.join(prods).lower() for x in ['windows', 'microsoft', 'smb', 'winrm']):
            _signal(db, r, scan_id, source_type, source_id, 'windows_host_candidate', h['ip'], a.id)
    db.commit()
    return r


def normalize_nuclei_jsonl(db, scan_id, path, source_type='nuclei_jsonl', source_id=None):
    r = NormalizationResult(scan_id, source_type, source_id)
    for lineno, item, err in iter_nuclei_jsonl(path):
        if err:
            _diag(
                db,
                r,
                scan_id,
                source_type,
                source_id,
                'malformed_nuclei_jsonl_line',
                'warning',
                {'line': lineno, 'error': err},
            )
            continue
        info = item.get('info') or {}
        sev = str(info.get('severity') or 'info').lower()
        if sev not in {'info', 'low', 'medium', 'high', 'critical'}:
            _diag(db, r, scan_id, source_type, source_id, 'unknown_nuclei_severity', 'warning', {'severity': sev})
            sev = 'info'
        host = item.get('matched-at') or item.get('host') or ''
        tid = item.get('template-id') or 'unknown'
        tags = {
            'template_id': tid,
            'host': host,
            'ip': item.get('ip'),
            'port': item.get('port'),
            'scheme': item.get('scheme'),
            'matcher_name': item.get('matcher-name'),
            'tags': info.get('tags'),
            'classification': info.get('classification'),
            'references': info.get('reference') or info.get('references'),
        }
        f, cr = get_or_create(
            db,
            ParsedFinding,
            {
                'scan_id': scan_id,
                'source_type': source_type,
                'source_id': source_id,
                'title': str(info.get('name') or tid)[:255],
                'severity': sev,
            },
            {
                'description': json.dumps(
                    {k: v for k, v in item.items() if k not in {'request', 'response', 'curl-command'}}, default=str
                )[:4000],
                'confidence': 0.8,
                'tags_json': tags,
            },
        )
        r.findings_created += int(cr)
        low = ' '.join(map(str, [tid, info.get('name'), info.get('tags')])).lower()
        for key, sig in [
            ('cve', 'known_cve_detected'),
            ('default', 'default_credential_exposure'),
            ('tls', 'tls_issue_detected'),
            ('misconfig', 'misconfiguration_detected'),
            ('panel', 'panel_exposed'),
            ('directory listing', 'directory_listing'),
            ('backup', 'backup_file_exposed'),
        ]:
            if key in low:
                _signal(db, r, scan_id, source_type, source_id, sig, host, finding_id=f.id)
        _signal(db, r, scan_id, source_type, source_id, 'web_exposure_detected', host, finding_id=f.id)
    db.commit()
    return r


def normalize_netexec_smb(db, scan_id, path, source_type='netexec_smb', source_id=None):
    r = NormalizationResult(scan_id, source_type, source_id)
    data = parse_netexec_smb(path)
    if data.get('raw_empty'):
        _diag(db, r, scan_id, source_type, source_id, 'empty_netexec_output', 'warning')
        db.commit()
        return r
    hosts = data.get('hosts') or [None]
    sigs = data.get('signals', {})
    for host in hosts:
        for sig, on in sigs.items():
            if on:
                _signal(db, r, scan_id, source_type, source_id, sig, host or 'true')
        if sigs.get('smb_signing_disabled'):
            _, cr = get_or_create(
                db,
                ParsedFinding,
                {
                    'scan_id': scan_id,
                    'source_type': source_type,
                    'source_id': source_id,
                    'title': 'SMB signing disabled',
                    'severity': 'medium',
                },
                {
                    'description': 'NetExec output indicates SMB signing is not required.',
                    'confidence': 0.8,
                    'tags_json': {'host': host},
                },
            )
            r.findings_created += int(cr)
            _, cr = get_or_create(
                db,
                ParsedCredentialRisk,
                {
                    'scan_id': scan_id,
                    'risk_type': 'smb_signing_disabled',
                    'principal': '',
                    'asset_ip': host or '',
                    'evidence': stable_hash('smb_signing_disabled' + str(host)),
                },
                {'source_type': source_type, 'source_id': source_id, 'risk_level': 'medium', 'properties_json': {}},
            )
            r.credential_risks_created += int(cr)
        if sigs.get('null_session_possible') or sigs.get('anonymous_smb_possible'):
            _, cr = get_or_create(
                db,
                ParsedFinding,
                {
                    'scan_id': scan_id,
                    'source_type': source_type,
                    'source_id': source_id,
                    'title': 'Anonymous or null SMB session possible',
                    'severity': 'high',
                },
                {
                    'description': 'NetExec output indicates anonymous or null-session SMB access may be possible.',
                    'confidence': 0.8,
                    'tags_json': {'host': host},
                },
            )
            r.findings_created += int(cr)
            for rt in ['anonymous_smb', 'null_session']:
                _, cr = get_or_create(
                    db,
                    ParsedCredentialRisk,
                    {
                        'scan_id': scan_id,
                        'risk_type': rt,
                        'principal': 'anonymous',
                        'asset_ip': host or '',
                        'evidence': stable_hash(rt + str(host)),
                    },
                    {'source_type': source_type, 'source_id': source_id, 'risk_level': 'high', 'properties_json': {}},
                )
                r.credential_risks_created += int(cr)
        if sigs.get('smb_guest_access_detected') or sigs.get('smb_share_listed'):
            _, cr = get_or_create(
                db,
                ParsedFinding,
                {
                    'scan_id': scan_id,
                    'source_type': source_type,
                    'source_id': source_id,
                    'title': 'SMB guest or share exposure',
                    'severity': 'medium',
                },
                {
                    'description': 'NetExec output indicates guest access or listed SMB shares.',
                    'confidence': 0.7,
                    'tags_json': {'host': host},
                },
            )
            r.findings_created += int(cr)
    db.commit()
    return r


def _bh_obj_type(name):
    n = name.lower()
    return {
        'users': 'user',
        'computers': 'computer',
        'groups': 'group',
        'domains': 'domain',
        'ous': 'ou',
        'gpos': 'gpo',
        'containers': 'container',
    }.get(n, 'unknown')


def normalize_bloodhound_zip(db, scan_id, path, source_type='bloodhound_zip', source_id=None):
    r = NormalizationResult(scan_id, source_type, source_id)
    p = Path(path)
    try:
        z = zipfile.ZipFile(p)
    except Exception as exc:
        _diag(db, r, scan_id, source_type, source_id, 'invalid_bloodhound_zip', 'error', {'error': str(exc)})
        db.commit()
        return r
    with z:
        for info in z.infolist():
            name = info.filename
            if name.startswith('/') or '..' in Path(name).parts:
                _diag(db, r, scan_id, source_type, source_id, 'unsafe_bloodhound_zip_path', 'error', {'path': name})
                continue
            if info.file_size > 10_000_000:
                _diag(db, r, scan_id, source_type, source_id, 'bloodhound_json_too_large', 'warning', {'path': name})
                continue
            if not name.lower().endswith('.json'):
                continue
            try:
                data = json.loads(z.read(info).decode('utf-8', 'replace'))
            except Exception as exc:
                _diag(
                    db,
                    r,
                    scan_id,
                    source_type,
                    source_id,
                    'malformed_bloodhound_json',
                    'warning',
                    {'path': name, 'error': str(exc)},
                )
                continue
            kind = _bh_obj_type(Path(name).stem.split('_')[-1])
            rows = data.get('data') if isinstance(data, dict) else data
            if not isinstance(rows, list):
                rows = []
            for item in rows:
                props = item.get('Properties') or item.get('properties') or item
                oid = (
                    item.get('ObjectIdentifier')
                    or props.get('objectid')
                    or props.get('sid')
                    or props.get('distinguishedname')
                    or props.get('name')
                )
                if not oid:
                    continue
                o, cr = get_or_create(
                    db,
                    ParsedADObject,
                    {'scan_id': scan_id, 'object_id': str(oid)},
                    {
                        'source_type': source_type,
                        'source_id': source_id,
                        'object_type': kind,
                        'name': props.get('name') or props.get('samaccountname'),
                        'domain': props.get('domain'),
                        'distinguished_name': props.get('distinguishedname'),
                        'sam_account_name': props.get('samaccountname'),
                        'sid': props.get('sid'),
                        'enabled': props.get('enabled'),
                        'high_value': bool(props.get('highvalue') or props.get('high_value')),
                        'owned': bool(props.get('owned')),
                        'properties_json': props,
                    },
                )
                r.ad_objects_created += int(cr)
                if o.high_value:
                    _signal(db, r, scan_id, source_type, source_id, 'high_value_target_detected', o.object_id)
                for edge in item.get('Aces', []) + item.get('Edges', []):
                    rel = edge.get('RightName') or edge.get('Label') or edge.get('kind') or 'Unknown'
                    tgt = edge.get('PrincipalSID') or edge.get('Target') or edge.get('target')
                    if tgt:
                        _, cr = get_or_create(
                            db,
                            ParsedADRelation,
                            {
                                'scan_id': scan_id,
                                'source_object_id': str(oid),
                                'relation_type': rel,
                                'target_object_id': str(tgt),
                            },
                            {
                                'source_type': source_type,
                                'source_id': source_id,
                                'is_abusable': rel in DANGEROUS_RELATIONS,
                                'risk_level': 'high' if rel in DANGEROUS_RELATIONS else 'info',
                                'properties_json': edge,
                            },
                        )
                        r.ad_relations_created += int(cr)
                        if rel in DANGEROUS_RELATIONS:
                            _signal(db, r, scan_id, source_type, source_id, 'dangerous_acl_detected', rel)
    _signal(db, r, scan_id, source_type, source_id, 'bloodhound_data_imported', 'true')
    db.commit()
    return r


def _normalize_simple_ad(db, scan_id, path, source_type, source_id=None):
    r = NormalizationResult(scan_id, source_type, source_id)
    txt = Path(path).read_text(errors='replace') if Path(path).exists() else ''
    try:
        data = json.loads(txt) if txt.strip().startswith(('[', '{')) else None
    except Exception:
        data = None
    if data is None:
        _diag(db, r, scan_id, source_type, source_id, 'parser_not_implemented', 'info', {'format': 'text'})
        db.commit()
        return r
    rows = data if isinstance(data, list) else data.get('objects', [])
    risks = data.get('credential_risks', []) if isinstance(data, dict) else []
    for item in rows:
        oid = item.get('object_id') or item.get('sid') or item.get('distinguished_name') or item.get('name')
        if oid:
            _, cr = get_or_create(
                db,
                ParsedADObject,
                {'scan_id': scan_id, 'object_id': str(oid)},
                {
                    'source_type': source_type,
                    'source_id': source_id,
                    'object_type': item.get('object_type', 'unknown'),
                    'name': item.get('name'),
                    'domain': item.get('domain'),
                    'distinguished_name': item.get('distinguished_name'),
                    'sid': item.get('sid'),
                    'enabled': item.get('enabled'),
                    'properties_json': item,
                },
            )
            r.ad_objects_created += int(cr)
    for risk in risks:
        rt = risk.get('risk_type', 'weak_password_policy')
        _, cr = get_or_create(
            db,
            ParsedCredentialRisk,
            {
                'scan_id': scan_id,
                'risk_type': rt,
                'principal': risk.get('principal', ''),
                'asset_ip': risk.get('asset_ip', ''),
                'evidence': stable_hash(risk),
            },
            {
                'source_type': source_type,
                'source_id': source_id,
                'domain': risk.get('domain'),
                'risk_level': risk.get('risk_level', 'medium'),
                'properties_json': risk,
            },
        )
        r.credential_risks_created += int(cr)
        _signal(db, r, scan_id, source_type, source_id, rt, risk.get('domain') or 'true')
    db.commit()
    return r


def normalize_ldap_output(db, scan_id, path, source_type='ldap_output', source_id=None):
    return _normalize_simple_ad(db, scan_id, path, source_type, source_id)


def normalize_kerberos_output(db, scan_id, path, source_type='kerberos_output', source_id=None):
    return _normalize_simple_ad(db, scan_id, path, source_type, source_id)


def normalize_adcs_output(db, scan_id, path, source_type='adcs_output', source_id=None):
    return _normalize_simple_ad(db, scan_id, path, source_type, source_id)


def normalize_artifact(db, artifact):
    path = _safe_path(artifact.path)
    r = NormalizationResult(artifact.scan_id, artifact.artifact_type, artifact.id)
    if path is None:
        _diag(db, r, artifact.scan_id, artifact.artifact_type, artifact.id, 'artifact_path_outside_evidence', 'error')
        db.commit()
        return r
    kind = infer_artifact_kind(artifact)
    return {
        'nmap': normalize_nmap_xml,
        'nuclei': normalize_nuclei_jsonl,
        'netexec_smb': normalize_netexec_smb,
        'bloodhound': normalize_bloodhound_zip,
        'ldap': normalize_ldap_output,
        'kerberos': normalize_kerberos_output,
        'adcs': normalize_adcs_output,
    }.get(kind, lambda *a, **k: r)(db, artifact.scan_id, path, artifact.artifact_type, artifact.id)


def normalize_job_outputs(db, scan_id):
    total = NormalizationResult(scan_id, 'job_outputs')
    for artifact in db.query(ScanArtifact).filter_by(scan_id=scan_id).all():
        total.merge(normalize_artifact(db, artifact))
    return total
