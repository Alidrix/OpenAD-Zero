from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS


def test_templates_have_explicit_metadata_lists():
    for template in COMMAND_TEMPLATE_DEFINITIONS.values():
        assert isinstance(template.scope_sensitive_params, list)
        assert isinstance(template.file_input_params, list)
        assert isinstance(template.file_output_params, list)
        assert isinstance(template.credential_params, list)
        assert isinstance(template.free_text_params, list)
        assert isinstance(template.enum_params, dict)


def test_sensitive_template_metadata_examples():
    assert COMMAND_TEMPLATE_DEFINITIONS['coercer_check_single_target'].scope_sensitive_params == ['target', 'listener']
    assert 'userlist' in COMMAND_TEMPLATE_DEFINITIONS['kerbrute_userenum'].file_input_params
    assert 'output' in COMMAND_TEMPLATE_DEFINITIONS['impacket_getnpusers'].file_output_params
    assert 'password' in COMMAND_TEMPLATE_DEFINITIONS['kerbrute_passwordspray_safe_preview'].credential_params


def test_new_parameter_validation_module_does_not_import_subprocess():
    import app.core.parameter_validation as pv

    assert 'subprocess' not in pv.__dict__
