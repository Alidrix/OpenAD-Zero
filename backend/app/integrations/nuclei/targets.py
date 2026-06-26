from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Host, Service, WebTarget

WEB_PORTS = {80, 443, 8080, 8000, 8443}
HTTPS_PORTS = {443, 8443}


def is_web_service(service: Service) -> bool:
    text = ' '.join([service.name or '', service.product or '', getattr(service, 'version', '') or '']).lower()
    return service.port in WEB_PORTS or 'http' in text or 'https' in text or 'ssl' in text


def scheme_for(service: Service) -> str:
    text = ' '.join([service.name or '', service.product or '', getattr(service, 'version', '') or '']).lower()
    if service.port in HTTPS_PORTS or 'https' in text or 'ssl' in text:
        return 'https'
    return 'http'


def url_for(ip: str, port: int, scheme: str) -> str:
    if (scheme == 'http' and port == 80) or (scheme == 'https' and port == 443):
        return f'{scheme}://{ip}'
    return f'{scheme}://{ip}:{port}'


def build_web_targets_for_mission(db: Session, mission_id: str) -> list[str]:
    rows = db.query(Host, Service).join(Service, Service.host_id == Host.id).filter(Host.mission_id == mission_id).all()
    urls = []
    for host, svc in rows:
        if not is_web_service(svc):
            continue
        urls.append(url_for(host.ip, svc.port, scheme_for(svc)))
    return sorted(set(urls))


def ensure_web_targets_for_mission(db: Session, mission_id: str) -> list[WebTarget]:
    existing = {w.url: w for w in db.query(WebTarget).filter_by(mission_id=mission_id).all()}
    created = []
    rows = db.query(Host, Service).join(Service, Service.host_id == Host.id).filter(Host.mission_id == mission_id).all()
    for host, svc in rows:
        if not is_web_service(svc):
            continue
        scheme = scheme_for(svc)
        url = url_for(host.ip, svc.port, scheme)
        if url not in existing:
            w = WebTarget(
                mission_id=mission_id, host_id=host.id, url=url, ip=host.ip, port=svc.port, scheme=scheme, source='nmap'
            )
            db.add(w)
            db.flush()
            existing[url] = w
            created.append(w)
    db.commit()
    return list(existing.values())
