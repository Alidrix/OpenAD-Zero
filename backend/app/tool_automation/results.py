from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from app.tool_automation.redaction import redact_mapping, redact_text

FindingValue = str | int | bool | list[str]

CATEGORIES = {
    "host", "port", "service", "domain", "user", "group", "computer", "share", "session", "spn", "asrep", "gmsa", "acl",
    "credential_artifact", "coercion", "captured_hash", "metasploit_module", "metasploit_check", "metasploit_controlled_exploit", "vulnerability", "bloodhound_path",
}

@dataclass(frozen=True)
class ParsedFinding:
    id: str
    tool_id: str
    template_id: str
    target: str | None
    category: str
    severity: str
    title: str
    description: str
    raw_evidence: str
    parsed_fields: dict[str, FindingValue] = field(default_factory=dict)
    artifact_path: str | None = None
    run_id: str = ""


def _finding_id(run_id: str, tool_id: str, template_id: str, target: str | None, category: str, severity: str, title: str, fields: dict[str, Any] | None, raw_evidence: str) -> str:
    redacted_evidence = redact_text(raw_evidence)
    identity_payload = {
        "run_id": run_id,
        "tool_id": tool_id,
        "template_id": template_id,
        "target": target,
        "category": category,
        "severity": severity,
        "title": title,
        "parsed_fields": redact_mapping(fields or {}),
        "evidence_fingerprint": hashlib.sha256(redacted_evidence.encode("utf-8")).hexdigest()[:16],
    }
    canonical = json.dumps(identity_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


def make_finding(tool_id: str, template_id: str, target: str | None, category: str, severity: str, title: str, description: str, raw: str, fields: dict[str, Any] | None = None, artifact_path: str | None = None, run_id: str = "") -> ParsedFinding:
    safe_fields = redact_mapping(fields or {})
    safe_raw = redact_text(raw)
    fid = _finding_id(run_id, tool_id, template_id, target, category, severity, title, safe_fields, safe_raw)
    return ParsedFinding(fid, tool_id, template_id, target, category, severity, title, description, safe_raw, safe_fields, artifact_path, run_id)
