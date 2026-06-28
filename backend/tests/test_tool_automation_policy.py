from pathlib import Path

import yaml

from app.tool_automation.command_templates import COMMAND_TEMPLATES
from app.tool_automation.policy import evaluate_tool_action, load_tool_catalog


def test_manual_only_can_preview_and_approve_but_not_run():
    assert evaluate_tool_action(tool_id="responder", action="preview").allowed
    assert evaluate_tool_action(tool_id="responder", action="approve").allowed
    decision = evaluate_tool_action(tool_id="responder", action="run")
    assert not decision.allowed
    assert "Manual-only" in decision.reason


def test_approval_does_not_bypass_blocked_auto():
    catalog = {"blocked": {"id": "blocked", "integration_status": "blocked_auto"}}
    decision = evaluate_tool_action(tool_id="blocked", action="approve", catalog=catalog)
    assert not decision.allowed
    assert "Blocked automation" in decision.reason


def test_sensitive_keywords_are_blocked_even_with_approval():
    keywords = [
        "secretsdump",
        "mimikatz",
        "psexec",
        "wmiexec",
        "responder",
        "coercer",
        "dcsync",
        "pass-the-hash",
        "shell",
        "reverse-shell",
    ]
    for keyword in keywords:
        decision = evaluate_tool_action(
            tool_id="nmap_safe_discovery",
            action="approve",
            argv=["tool", keyword, "10.0.0.1"],
        )
        assert not decision.allowed, keyword


def test_unknown_tool_out_of_scope_and_undeclared_template_are_blocked():
    assert not evaluate_tool_action(tool_id="missing", action="preview").allowed
    assert not evaluate_tool_action(tool_id="nmap_safe_discovery", action="run", target_in_scope=False).allowed
    decision = evaluate_tool_action(
        tool_id="nmap_safe_discovery",
        action="run",
        declared_template_ids=set(),
    )
    assert not decision.allowed


def test_removed_scanner_absent_from_tool_catalog_and_templates_and_docs():
    catalog = load_tool_catalog()
    assert all("ping" + "castle" not in tool_id.lower() for tool_id in catalog)
    assert all("ping" + "castle" not in template_id.lower() for template_id in COMMAND_TEMPLATES)

    root = Path(__file__).resolve().parents[2]
    checked = [
        root / "backend/app/tool_automation/tools.yml",
        root / "backend/app/tool_automation/command_templates.py",
        root / "docs/TOOL_AUTOMATION.md",
        root / "docs/backlog/v0.2.0.md",
    ]
    for path in checked:
        assert "ping" + "castle" not in path.read_text().casefold(), path


def test_catalog_uses_strict_integration_statuses():
    allowed = {"safe_auto", "assisted_safe", "manual_only", "blocked_auto", "planned"}
    raw = yaml.safe_load(Path("backend/app/tool_automation/tools.yml").read_text())
    assert {item["integration_status"] for item in raw} <= allowed
