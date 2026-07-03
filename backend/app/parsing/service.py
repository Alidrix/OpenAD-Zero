from __future__ import annotations
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import ParseDiagnostic, ParsedAsset, ParsedFinding, ParsedService, ParsedSignal, Scan
from app.parsing.schemas import ParsePersistedResult
from app.parsing.signals import normalize_signal

class ParseContext:
    def __init__(self, db: Session, scan_id: str):
        self.db=db; self.scan_id=scan_id
        self.assets: dict[str, ParsedAsset] = {}
        self.services: dict[tuple[str,int,str], ParsedService] = {}
        self.signals: set[tuple[str,str,str|None,str|None]] = set()
    def asset(self, source_type: str, source_id: str|None, ip: str, hostname=None, fqdn=None, mac=None, os_family=None, os_name=None, confidence=0.8):
        ip=str(ip).strip()
        if not ip: return None
        a=self.assets.get(ip)
        if a is None:
            a=ParsedAsset(scan_id=self.scan_id, source_type=source_type, source_id=source_id, ip_address=ip, hostname=hostname, fqdn=fqdn, mac_address=mac, os_family=os_family, os_name=os_name, confidence=confidence, tags_json=None)
            self.db.add(a); self.db.flush(); self.assets[ip]=a
        else:
            a.hostname=a.hostname or hostname; a.fqdn=a.fqdn or fqdn; a.mac_address=a.mac_address or mac; a.os_family=a.os_family or os_family; a.os_name=a.os_name or os_name
        return a
    def service(self, source_type: str, source_id: str|None, ip: str, port, protocol='tcp', service_name=None, product=None, version=None, state='open', confidence=0.8):
        try: port_int=int(port)
        except (TypeError, ValueError): return None
        proto=str(protocol or 'tcp').lower(); a=self.asset(source_type, source_id, ip)
        key=(str(ip), port_int, proto)
        svc=self.services.get(key)
        if svc is None:
            svc=ParsedService(scan_id=self.scan_id, asset_id=a.id if a else None, source_type=source_type, source_id=source_id, ip_address=str(ip), port=port_int, protocol=proto, service_name=service_name, product=product, version=version, state=state or 'open', confidence=confidence, tags_json=None)
            self.db.add(svc); self.db.flush(); self.services[key]=svc
        return svc
    def signal(self, source_type: str, source_id: str|None, signal: object, value='true', asset=None, service=None, finding=None, confidence=0.8):
        sig=normalize_signal(signal)
        if not sig: return None
        key=(sig, str(value), getattr(asset,'id',None), getattr(service,'id',None))
        if key in self.signals: return None
        self.signals.add(key)
        row=ParsedSignal(scan_id=self.scan_id, asset_id=getattr(asset,'id',None), service_id=getattr(service,'id',None), finding_id=getattr(finding,'id',None), source_type=source_type, source_id=source_id, signal=sig, value=str(value), confidence=confidence)
        self.db.add(row); return row
    def diagnostic(self, source_type: str, source_id: str|None, level: str, message: str, details: dict|None=None):
        self.db.add(ParseDiagnostic(scan_id=self.scan_id, source_type=source_type, source_id=source_id, level=level, message=message, details_json=details))

def is_supported_nmap_artifact(artifact) -> bool:
    text=f"{artifact.artifact_type} {artifact.path}".lower()
    return 'nmap' in text or str(artifact.path).lower().endswith('.xml')

def artifact_path_under_evidence(path: str) -> Path | None:
    root=Path(get_settings().evidence_dir).resolve()
    candidate=Path(path)
    if not candidate.is_absolute(): candidate=root / candidate
    resolved=candidate.resolve()
    try: resolved.relative_to(root)
    except ValueError: return None
    return resolved

def parse_persisted_scan(db: Session, scan_id: str) -> ParsePersistedResult:
    from app.parsing.generic_event_parser import parse_scan_events
    from app.parsing.nmap_xml_parser import parse_nmap_artifacts
    scan=db.get(Scan, scan_id)
    if scan is None: raise ValueError('Scan not found')
    # First V2 slice uses delete-then-reparse per scan for deterministic idempotence; persisted source rows are untouched.
    for model in (ParsedSignal, ParsedFinding, ParsedService, ParsedAsset, ParseDiagnostic):
        db.query(model).filter_by(scan_id=scan_id).delete(synchronize_session=False)
    db.flush()
    ctx=ParseContext(db, scan_id)
    parse_scan_events(ctx, list(scan.events or []), scan)
    parse_nmap_artifacts(ctx, list(scan.artifacts or []))
    db.commit()
    return ParsePersistedResult(scan_id=scan_id, assets_created=db.query(ParsedAsset).filter_by(scan_id=scan_id).count(), services_created=db.query(ParsedService).filter_by(scan_id=scan_id).count(), findings_created=db.query(ParsedFinding).filter_by(scan_id=scan_id).count(), signals_created=db.query(ParsedSignal).filter_by(scan_id=scan_id).count(), diagnostics_created=db.query(ParseDiagnostic).filter_by(scan_id=scan_id).count(), status='parsed')
