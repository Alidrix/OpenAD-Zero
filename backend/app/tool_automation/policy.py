from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

IntegrationStatus = Literal["safe_auto", "assisted_safe", "manual_only", "blocked_auto", "planned"]
Action = Literal["preview", "approve", "run"]

AUTHORISED_KEYWORDS = {
    "secretsdump",
    "lsassy",
    "dcsync",
    "mimikatz",
    "psexec",
    "wmiexec",
    "smbexec",
    "atexec",
    "pass-the-hash",
    "pth",
    "relay",
    "coerce",
    "coercer",
    "responder",
    "poison",
    "dpapi",
    "sam",
    "lsa",
    "ntds",
    "shadow",
    "persistence",
    "reverse",
    "shell",
}

# Backward-compatible spelling from the 7B mission text.
AUTORISED_KEYWORDS = AUTHORISED_KEYWORDS

CATALOG_PATH = Path(__file__).with_name("tools.yml")


@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str


def load_tool_catalog(path: Path = CATALOG_PATH) -> dict[str, dict[str, str]]:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("Tool automation catalog must be a YAML list.")
    catalog: dict[str, dict[str, str]] = {}
    valid_statuses = {"safe_auto", "assisted_safe", "manual_only", "blocked_auto", "planned"}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Every tool automation catalog entry must have an id.")
        status = item.get("integration_status")
        if status not in valid_statuses:
            raise ValueError(f"Invalid integration_status for {item['id']}: {status}")
        if item["id"] in catalog:
            raise ValueError(f"Duplicate tool id: {item['id']}")
        catalog[item["id"]] = item
    return catalog


def contains_authorised_keyword(values: list[str] | tuple[str, ...] | str | None) -> bool:
    if values is None:
        return False
    text = " ".join(values) if not isinstance(values, str) else values
    normalized = text.casefold()
    return any(keyword in normalized for keyword in AUTHORISED_KEYWORDS)


def evaluate_tool_action(
    *,
    tool_id: str,
    action: Action,
    template: str | None = None,
    argv: list[str] | None = None,
    target_in_scope: bool = True,
    catalog: dict[str, dict[str, str]] | None = None,
    declared_template_ids: set[str] | None = None,
) -> ToolPolicyDecision:
    """Apply the hard 7B safety gate for preview/approval/run requests."""

    tools = catalog if catalog is not None else load_tool_catalog()
    tool = tools.get(tool_id)
    if tool is None:
        return ToolPolicyDecision(False, "Unknown tool_id is not executable.")
    if not target_in_scope:
        return ToolPolicyDecision(False, "Target is outside the validated scope.")

    status = tool["integration_status"]
    if status == "planned":
        return ToolPolicyDecision(False, "Planned tools are not available.")
    if status == "blocked_auto":
        return ToolPolicyDecision(False, "Blocked automation cannot be approved or run.")
    if contains_authorised_keyword(template) or contains_authorised_keyword(argv):
        return ToolPolicyDecision(False, "Blocked automation keyword cannot be executed by OpenAD Zero.")
    if action == "run" and declared_template_ids is not None and tool_id not in declared_template_ids:
        return ToolPolicyDecision(False, "No declared runnable template exists for this tool.")
    if status == "manual_only" and action == "run":
        return ToolPolicyDecision(False, "Manual-only tools can be documented and approved for manual tracking, but not run.")
    if status == "manual_only":
        return ToolPolicyDecision(True, "Manual-only workflow may be previewed or approved as documentation only.")
    if status == "assisted_safe":
        return ToolPolicyDecision(True, "Assisted-safe read-only workflow is allowed after preview and approval.")
    if status == "safe_auto":
        return ToolPolicyDecision(True, "Safe automatic workflow is allowed for validated scope.")
    return ToolPolicyDecision(False, "Unsupported integration status.")
