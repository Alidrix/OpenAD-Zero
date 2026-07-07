from __future__ import annotations

from app.recommendations.catalog_loader import get_catalog
from app.recommendations.models import V2CommandPreview
from app.recommendations.safety import assert_preview_only
from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS


class PreviewBuildError(ValueError):
    pass


def build_preview(template_id: str, params: dict[str, str]) -> V2CommandPreview:
    templates, _rules, policy = get_catalog()
    assert_preview_only(policy)
    if any(key.lower() in {'command', 'raw_command', 'argv', 'shell'} for key in params):
        raise PreviewBuildError('Raw frontend commands are not accepted')
    template = next((item for item in templates if item.id == template_id), None)
    if template is None:
        raise PreviewBuildError('Unknown V2 template')
    definition = COMMAND_TEMPLATE_DEFINITIONS[template.template_ref]
    allowed = set(definition.required_params) | set(definition.optional_params)
    unexpected = sorted(set(params) - allowed)
    if unexpected:
        raise PreviewBuildError(f'Unexpected template parameter: {unexpected[0]}')
    missing = [name for name in definition.required_params if not params.get(name)]
    argv_preview = []
    for arg in definition.argv:
        rendered = arg
        for name in allowed:
            rendered = rendered.replace('{' + name + '}', params.get(name, '<' + name + '>'))
        argv_preview.append(rendered)
    return V2CommandPreview(
        template_id=template.id,
        tool_id=template.tool_id,
        name=template.name,
        argv_preview=argv_preview,
        required_params=definition.required_params,
        missing_params=missing,
        safety_notes=template.safety_notes,
        risk_level=template.risk_level,
        mode=template.mode,
        executable=False,
        automatic_execution_allowed=False,
    )
