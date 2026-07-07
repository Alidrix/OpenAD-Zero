from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

INTEGRATION_STATUSES = {'supported', 'preview_only', 'manual_only', 'blocked', 'planned'}
EXECUTION_MODES = {'safe_auto', 'approval_required', 'reinforced_approval_required', 'manual_only', 'blocked'}
RISK_LEVELS = {'info', 'low', 'medium', 'high', 'critical'}


@dataclass(frozen=True)
class ToolFamily:
    id: str
    name: str
    description: str
    phase_id: str
    default_risk_level: str
    supported_tools: list[str]
    default_execution_mode: str
    safety_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolMetadata:
    tool_id: str
    name: str
    family: str
    description: str
    binary: str | None
    binary_aliases: list[str]
    integration_status: str
    default_risk_level: str
    default_execution_mode: str
    requires_approval: bool
    requires_reinforced_approval: bool
    requires_terms_acceptance: bool
    supports_dry_run: bool
    supports_json_output: bool
    supports_parser: bool
    parser_id: str | None
    allowed_templates: list[str]
    blocked_capabilities: list[str]
    health_check: str
    install_notes: str
    safety_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TemplateMetadata:
    template_id: str
    tool_id: str
    family: str
    name: str
    description: str
    argv: list[str]
    required_params: list[str]
    optional_params: list[str]
    scope_sensitive_params: list[str]
    file_input_params: list[str]
    file_output_params: list[str]
    credential_params: list[str]
    free_text_params: list[str]
    enum_params: dict[str, list[str]]
    risk_level: str
    execution_mode: str
    supported_for_run: bool
    parser_id: str | None
    artifact_type: str | None
    integration_status: str = 'preview_only'
    safety_notes: list[str] = field(default_factory=list)
    blocked_reason: str | None = None

    def to_dict(self, include_argv: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if not include_argv:
            data.pop('argv', None)
        return data
