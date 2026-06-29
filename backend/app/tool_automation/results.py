from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any

FindingValue = str | int | bool | list[str]

CATEGORIES = {
    "host", "port", "service", "domain", "user", "group", "computer", "share", "session", "spn", "asrep", "gmsa", "acl",
    "credential_artifact", "coercion", "captured_hash", "metasploit_module", "metasploit_check", "metasploit_controlled_exploit", "metasploit_session", "vulnerability", "bloodhound_path",
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


def make_finding(tool_id: str, template_id: str, target: str | None, category: str, severity: str, title: str, description: str, raw: str, fields: dict[str, Any] | None = None, artifact_path: str | None = None) -> ParsedFinding:
    fid = sha1(f"{tool_id}|{template_id}|{target}|{category}|{title}|{raw}".encode()).hexdigest()[:16]
    return ParsedFinding(fid, tool_id, template_id, target, category, severity, title, description, raw, fields or {}, artifact_path)
