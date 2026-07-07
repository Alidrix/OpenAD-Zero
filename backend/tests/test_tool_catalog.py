from app.tool_catalog.families import FAMILIES, REQUIRED_FAMILY_IDS
from app.tool_catalog.models import EXECUTION_MODES, RISK_LEVELS
from app.tool_catalog.registry import SUPPORTED_RUN_TEMPLATE_IDS, list_template_metadata, list_tools


def test_all_required_families_exist():
    assert set(REQUIRED_FAMILY_IDS).issubset(FAMILIES)


def test_tools_and_templates_have_valid_families_and_modes():
    families = set(FAMILIES)
    for tool in list_tools():
        assert tool.family in families
    for template in list_template_metadata():
        assert template.family in families
        assert template.execution_mode in EXECUTION_MODES
        assert template.risk_level in RISK_LEVELS
        assert isinstance(template.scope_sensitive_params, list)
        assert isinstance(template.file_input_params, list)
        assert isinstance(template.file_output_params, list)
        assert isinstance(template.credential_params, list)
        if template.risk_level in {'high', 'critical'}:
            assert template.execution_mode != 'safe_auto'
        if template.execution_mode in {'manual_only', 'blocked'}:
            assert template.supported_for_run is False
        if template.supported_for_run:
            assert template.template_id in SUPPORTED_RUN_TEMPLATE_IDS
            assert template.parser_id
            assert template.artifact_type
