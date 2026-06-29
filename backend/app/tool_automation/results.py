from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from app.tool_automation.redaction import redact_mapping, redact_text

FindingValue = str | int | bool | list[str]

CATEGORIES = {
    "host", "port", "service", "domain", "user", "group", "computer", "share", "session", "spn", "asrep", "gmsa", "acl",
    "credential_artifact", "coercion", "captured_hash", "metasploit_module", "vulnerability", "bloodhound_path",
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


def _finding_id(tool_id: str, template_id: str, target: str | None, category: str, severity: str, title: str, fields: dict[str, Any] | None) -> str:
    identity_payload = {
        "tool_id": tool_id,
        "template_id": template_id,
        "target": target,
        "category": category,
        "severity": severity,
        "title": title,
        "parsed_fields": redact_mapping(fields or {}),
    }
    canonical = json.dumps(identity_payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:16]


def make_finding(tool_id: str, template_id: str, target: str | None, category: str, severity: str, title: str, description: str, raw: str, fields: dict[str, Any] | None = None, artifact_path: str | None = None) -> ParsedFinding:
    safe_fields = redact_mapping(fields or {})
    fid = _finding_id(tool_id, template_id, target, category, severity, title, safe_fields)
    return ParsedFinding(fid, tool_id, template_id, target, category, severity, title, description, redact_text(raw), safe_fields, artifact_path)
