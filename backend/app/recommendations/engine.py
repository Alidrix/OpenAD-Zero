from __future__ import annotations

from app.db.models import Scan, ScanArtifact, ScanEvent
from app.recommendations.catalog_loader import get_catalog
from app.recommendations.models import V2Recommendation

PORT_SIGNALS = {
    "445": "smb_open",
    "139": "smb_open",
    "389": "ldap_open",
    "636": "ldap_open",
    "88": "kerberos_open",
    "80": "http_open",
    "443": "http_open",
    "8080": "http_open",
}
ALLOWED_SIGNALS = {
    "host_discovered",
    "windows_host_detected",
    "smb_open",
    "ldap_open",
    "kerberos_open",
    "http_open",
    "scan_completed",
    "artifact_uploaded",
    "bloodhound_artifact_present",
}


def _add_text_signals(text: str, signals: set[str]) -> None:
    lower = text.lower()
    for token, signal in [
        ("smb", "smb_open"),
        ("445", "smb_open"),
        ("ldap", "ldap_open"),
        ("389", "ldap_open"),
        ("kerberos", "kerberos_open"),
        ("88", "kerberos_open"),
        ("http", "http_open"),
        ("443", "http_open"),
        ("windows", "windows_host_detected"),
    ]:
        if token in lower:
            signals.add(signal)
    if "host" in lower or "discovered" in lower:
        signals.add("host_discovered")


def extract_signals(
    scan: Scan, events: list[ScanEvent], artifacts: list[ScanArtifact]
) -> set[str]:
    signals: set[str] = set()
    if scan.status == "completed":
        signals.add("scan_completed")
    _add_text_signals(
        " ".join(filter(None, [scan.scan_type, scan.tool_name, scan.current_step])),
        signals,
    )
    for event in events:
        _add_text_signals(f"{event.event_type} {event.message}", signals)
        payload = event.payload_json or {}
        for key, value in payload.items():
            if key == "signals" and isinstance(value, list):
                signals.update(
                    str(item) for item in value if str(item) in ALLOWED_SIGNALS
                )
            if key in {"port", "service_port"} and str(value) in PORT_SIGNALS:
                signals.add(PORT_SIGNALS[str(value)])
            _add_text_signals(f"{key} {value}", signals)
    for artifact in artifacts:
        signals.add("artifact_uploaded")
        _add_text_signals(f"{artifact.artifact_type} {artifact.path}", signals)
        if "bloodhound" in f"{artifact.artifact_type} {artifact.path}".lower():
            signals.add("bloodhound_artifact_present")
    return signals & ALLOWED_SIGNALS


def build_recommendations(
    scan: Scan, events: list[ScanEvent], artifacts: list[ScanArtifact]
) -> list[V2Recommendation]:
    templates, rules, _policy = get_catalog()
    by_id = {template.id: template for template in templates}
    signals = extract_signals(scan, events, artifacts)
    recommendations: list[V2Recommendation] = []
    for rule in rules:
        if not set(rule.when.signals).issubset(signals):
            continue
        template = by_id[rule.recommend.template_id]
        if template.mode == "gated_high_risk":
            continue
        recommendations.append(
            V2Recommendation(
                recommendation_id=rule.id,
                template_id=template.id,
                name=template.name,
                reason=rule.recommend.reason,
                priority=rule.recommend.priority,
                risk_level=template.risk_level,
                mode=template.mode,
                requires_human_approval=template.requires_human_approval,
                safety_notes=template.safety_notes,
            )
        )
    return recommendations
