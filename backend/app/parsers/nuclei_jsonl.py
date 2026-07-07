from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class NucleiFinding:
    template_id: str
    title: str
    severity: str
    matched_at: str | None
    host: str | None
    ip: str | None
    port: int | None
    tags: list[str]
    references: list[str]
    raw_json: dict[str, Any]


def iter_nuclei_jsonl(path: str | Path):
    for lineno, line in enumerate(Path(path).read_text(errors='replace').splitlines(), 1):
        if not line.strip():
            continue
        try:
            yield lineno, json.loads(line), None
        except Exception as exc:
            yield lineno, None, str(exc)


def parse_nuclei_jsonl(path: str | Path) -> list[NucleiFinding]:
    out = []
    for _lineno, item, err in iter_nuclei_jsonl(path):
        if err or not isinstance(item, dict):
            continue
        info = item.get('info') or {}
        sev = str(info.get('severity') or 'info').lower()
        if sev not in {'info', 'low', 'medium', 'high', 'critical'}:
            sev = 'info'
        refs = info.get('reference') or info.get('references') or []
        if isinstance(refs, str):
            refs = [refs]
        tags = info.get('tags') or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        try:
            port = int(item.get('port')) if item.get('port') is not None else None
        except (TypeError, ValueError):
            port = None
        out.append(
            NucleiFinding(
                template_id=str(item.get('template-id') or ''),
                title=str(info.get('name') or item.get('template-id') or 'Nuclei finding'),
                severity=sev,
                matched_at=item.get('matched-at'),
                host=item.get('host'),
                ip=item.get('ip'),
                port=port,
                tags=tags,
                references=refs,
                raw_json=item,
            )
        )
    return out
