from __future__ import annotations
import re
from app.parsing.signals import normalize_signal, service_to_signal
IP_RE=re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def _first(payload, keys):
    for k in keys:
        if k in payload and payload[k] not in (None, ''): return payload[k]
    return None

def parse_scan_events(ctx, events, scan=None) -> None:
    if scan and scan.status == 'completed': ctx.signal('scan', scan.id, 'scan_completed')
    for event in events:
        payload=event.payload_json or {}
        if not isinstance(payload, dict):
            ctx.diagnostic('scan_event', event.id, 'warning', 'Scan event payload is not an object', {'event_type': event.event_type}); payload={}
        for raw in payload.get('signals') or []:
            if normalize_signal(raw): ctx.signal('scan_event', event.id, raw)
        ip=_first(payload, ['ip','host','ip_address','address','target'])
        hostname=_first(payload, ['hostname','host_name','fqdn'])
        os_name=_first(payload, ['os','os_name','operating_system'])
        asset=None
        if ip:
            asset=ctx.asset('scan_event', event.id, str(ip), hostname=str(hostname) if hostname else None, fqdn=str(hostname) if hostname and '.' in str(hostname) else None, os_name=str(os_name) if os_name else None)
            ctx.signal('scan_event', event.id, 'host_discovered', asset=asset)
            if os_name and 'windows' in str(os_name).lower(): ctx.signal('scan_event', event.id, 'windows_host_detected', asset=asset)
            if os_name and 'linux' in str(os_name).lower(): ctx.signal('scan_event', event.id, 'linux_host_detected', asset=asset)
        port=_first(payload, ['port','service_port'])
        if port:
            svc=ctx.service('scan_event', event.id, str(ip or 'unknown'), port, _first(payload,['protocol','proto']) or 'tcp', _first(payload,['service','service_name','name']))
            sig=service_to_signal(port, _first(payload,['protocol','proto']) or 'tcp', _first(payload,['service','service_name','name']))
            if sig: ctx.signal('scan_event', event.id, sig, asset=asset, service=svc)
        if not payload:
            # Limited fallback for legacy free-text events only; structured payload wins whenever present.
            text=f'{event.event_type} {event.message}'.lower()
            ip_match=IP_RE.search(text)
            if ip_match:
                asset=ctx.asset('scan_event', event.id, ip_match.group(0)); ctx.signal('scan_event', event.id, 'host_discovered', asset=asset)
            for port, sig in [(445,'smb_open'),(389,'ldap_open'),(88,'kerberos_open'),(80,'http_open'),(443,'http_open')]:
                if str(port) in text or sig.split('_')[0] in text: ctx.signal('scan_event', event.id, sig, asset=asset)
