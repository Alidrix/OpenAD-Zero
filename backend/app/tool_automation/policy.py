from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

from app.tool_automation.command_templates import COMMAND_TEMPLATES

IntegrationStatus = Literal["safe_auto", "assisted_safe", "executable_after_human_approval", "manual_only", "blocked_auto", "planned"]
Action = Literal["preview", "approve", "run"]

VALID_INTEGRATION_STATUSES = {"safe_auto", "assisted_safe", "executable_after_human_approval", "manual_only", "blocked_auto", "planned"}

AUTHORISED_KEYWORDS = {"secretsdump", "lsassy", "dcsync", "mimikatz", "psexec", "wmiexec", "smbexec", "atexec", "pass-the-hash", "pth", "relay", "coerce", "coercer", "responder", "poison", "dpapi", "sam", "lsa", "ntds", "shadow", "persistence", "reverse", "shell"}
AUTORISED_KEYWORDS = AUTHORISED_KEYWORDS
CATALOG_PATH = Path(__file__).with_name("tools.yml")

@dataclass(frozen=True)
class ToolPolicyDecision:
    allowed: bool
    reason: str
    risk_level: str = "low"
    requires_human_approval: bool = False
    requires_terms_acceptance: bool = False


def load_tool_catalog(path: Path = CATALOG_PATH) -> dict[str, dict]:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("Tool automation catalog must be a YAML list.")
    catalog: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Every tool automation catalog entry must have an id.")
        status = item.get("integration_status")
        if status not in VALID_INTEGRATION_STATUSES:
            raise ValueError(f"Invalid integration_status for {item['id']}: {status}")
        if item["id"] in catalog:
            raise ValueError(f"Duplicate tool id: {item['id']}")
        item.setdefault("templates", [])
        catalog[item["id"]] = item
    return catalog


def contains_authorised_keyword(values: list[str] | tuple[str, ...] | str | None) -> bool:
    if values is None:
        return False
    text = " ".join(values) if not isinstance(values, str) else values
    normalized = text.casefold()
    return any(keyword in normalized for keyword in AUTHORISED_KEYWORDS)


def _template_decision(tool: dict, selected_template_id: str | None) -> ToolPolicyDecision | None:
    templates = set(tool.get("templates") or [])
    if not templates:
        return ToolPolicyDecision(False, "No declared runnable template exists for this tool.", tool.get("risk_level", "low"), bool(tool.get("requires_human_approval")), bool(tool.get("requires_terms_acceptance")))
    if not selected_template_id:
        return ToolPolicyDecision(False, "No declared runnable template exists for this tool.", tool.get("risk_level", "low"), bool(tool.get("requires_human_approval")), bool(tool.get("requires_terms_acceptance")))
    if selected_template_id not in COMMAND_TEMPLATES or selected_template_id not in templates:
        return ToolPolicyDecision(False, "Selected template is not allowed for this tool.", tool.get("risk_level", "low"), bool(tool.get("requires_human_approval")), bool(tool.get("requires_terms_acceptance")))
    return None


def evaluate_tool_action(*, tool_id: str, action: Action, template: str | None = None, argv: list[str] | None = None, target_in_scope: bool = True, catalog: dict[str, dict] | None = None, declared_template_ids: set[str] | None = None, human_approved: bool = False, terms_accepted: bool = False, preview_generated: bool = False, selected_template_id: str | None = None) -> ToolPolicyDecision:
    tools = catalog if catalog is not None else load_tool_catalog()
    tool = tools.get(tool_id)
    if tool is None:
        return ToolPolicyDecision(False, "Unknown tool_id is not executable.")
    risk = tool.get("risk_level", "low")
    needs_approval = bool(tool.get("requires_human_approval"))
    needs_terms = bool(tool.get("requires_terms_acceptance"))
    deny = lambda reason: ToolPolicyDecision(False, reason, risk, needs_approval, needs_terms)
    allow = lambda reason: ToolPolicyDecision(True, reason, risk, needs_approval, needs_terms)
    if not target_in_scope:
        return deny("Target is outside the validated scope.")
    status = tool["integration_status"]
    if status == "planned":
        return deny("Planned tools are not available.")
    if status == "blocked_auto":
        return deny("Blocked automation cannot be approved or run.")
    if status == "manual_only":
        if action == "run":
            return deny("Manual-only tools can be documented, but not run.")
        return allow("Manual-only workflow may be previewed or approved as documentation only.")
    if action in {"preview", "approve"}:
        return allow("Command preview or approval step is allowed for validated scope.")
    template_denial = _template_decision(tool, selected_template_id or (tool_id if declared_template_ids and tool_id in declared_template_ids else None))
    if template_denial is not None:
        return template_denial
    if status in {"safe_auto", "assisted_safe"} and (contains_authorised_keyword(template) or contains_authorised_keyword(argv)):
        return deny("Blocked automation keyword cannot be executed by OpenAD Zero.")
    if status == "executable_after_human_approval":
        if not preview_generated:
            return deny("This tool requires command preview before execution.")
        if not human_approved:
            return deny("This tool requires human approval before execution.")
        if not terms_accepted:
            return deny("This tool requires explicit terms acceptance before execution.")
        return ToolPolicyDecision(True, "Advanced workflow is allowed after preview, human approval, terms acceptance and scope validation.", "high", True, True)
    if status in {"safe_auto", "assisted_safe"}:
        return allow("Safe or assisted workflow is allowed for validated scope and declared template.")
    return deny("Unsupported integration status.")
