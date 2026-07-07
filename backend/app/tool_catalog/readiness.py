from __future__ import annotations

import shutil
from collections import Counter
from typing import Any

from app.tool_catalog.registry import list_template_metadata, list_tools


def tool_readiness() -> list[dict[str, Any]]:
    templates_by_tool: dict[str, list[Any]] = {}
    for template in list_template_metadata():
        templates_by_tool.setdefault(template.tool_id, []).append(template)
    rows = []
    for tool in list_tools():
        candidates = [tool.binary, *tool.binary_aliases]
        found = next((c for c in candidates if c and shutil.which(c)), None)
        templates = templates_by_tool.get(tool.tool_id, [])
        risk_counts = Counter(t.risk_level for t in templates)
        rows.append(
            {
                'tool_id': tool.tool_id,
                'binary': tool.binary,
                'available': bool(found) if tool.binary else True,
                'version': None,
                'integration_status': tool.integration_status,
                'supported_templates': [t.template_id for t in templates if t.supported_for_run],
                'blocked_templates': [
                    t.template_id
                    for t in templates
                    if t.execution_mode in {'blocked', 'manual_only'} or not t.supported_for_run
                ],
                'missing_reason': None if (found or tool.binary is None) else 'Binary not found on PATH',
                'risk_summary': dict(risk_counts),
            }
        )
    return rows
