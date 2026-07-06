import pytest

from app.core.parameter_validation import (
    ParameterPolicy,
    ParameterValidationError,
    mask_sensitive_params,
    validate_action_parameters,
    validate_network_value,
)


def test_network_scope_and_public_controls(monkeypatch):
    scope = ['10.0.0.0/24']
    assert validate_network_value('target', '10.0.0.5', scope) == ['10.0.0.5']
    with pytest.raises(ParameterValidationError):
        validate_network_value('target', '10.0.1.5', scope)
    with pytest.raises(ParameterValidationError):
        validate_network_value('target', '8.8.8.8', ['8.8.8.8'])
    assert validate_network_value('target', '8.8.8.8', ['8.8.8.8'], allow_public_scans=True) == ['8.8.8.8']
    for bad in ['0.0.0.0/0', '::/0', '2001:db8::1', '10.0.0.0/8']:
        with pytest.raises(ParameterValidationError):
            validate_network_value('target', bad, ['10.0.0.0/8'])


def test_all_scope_sensitive_fields_validated():
    policy = ParameterPolicy(
        required_params=['target', 'dc_ip', 'listener'], scope_sensitive_params=['target', 'dc_ip', 'listener']
    )
    with pytest.raises(ParameterValidationError):
        validate_action_parameters(
            {'target': '10.0.0.5', 'dc_ip': '10.0.1.10', 'listener': '10.0.0.20'}, policy, ['10.0.0.0/24']
        )
    with pytest.raises(ParameterValidationError):
        validate_action_parameters(
            {'target': '10.0.0.5', 'dc_ip': '10.0.0.10', 'listener': '10.0.2.20'}, policy, ['10.0.0.0/24']
        )


def test_url_and_hostname_policy():
    with pytest.raises(ParameterValidationError):
        validate_network_value('url', 'file:///etc/passwd', ['10.0.0.0/24'], allow_urls=True)
    assert validate_network_value('url', 'http://10.0.0.5', ['10.0.0.0/24'], allow_urls=True) == ['http://10.0.0.5']
    with pytest.raises(ParameterValidationError):
        validate_network_value('hostname', 'dc01.lab.local', ['10.0.0.0/24'])
    assert validate_network_value('hostname', 'dc01.lab.local', ['10.0.0.0/24'], allow_hostnames=True) == [
        'dc01.lab.local'
    ]


def test_file_input_output_and_symlink(isolated_evidence_dir, tmp_path):
    isolated_evidence_dir.mkdir(parents=True, exist_ok=True)
    input_file = isolated_evidence_dir / 'users.txt'
    input_file.write_text('alice\n')
    policy = ParameterPolicy(
        required_params=['userlist', 'output'], file_input_params=['userlist'], file_output_params=['output']
    )
    validated = validate_action_parameters({'userlist': str(input_file), 'output': 'jobs/out.txt'}, policy, [])
    assert validated['userlist'] == str(input_file.resolve())
    assert validated['output'].startswith(str(isolated_evidence_dir.resolve()))
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'userlist': '/etc/passwd', 'output': 'out.txt'}, policy, [])
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'userlist': '../users.txt', 'output': 'out.txt'}, policy, [])
    outside = tmp_path / 'outside.txt'
    outside.write_text('x')
    link = isolated_evidence_dir / 'link.txt'
    link.symlink_to(outside)
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'userlist': str(link), 'output': 'out.txt'}, policy, [])
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'userlist': str(input_file), 'output': '/etc/passwd'}, policy, [])
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'userlist': str(input_file), 'output': '/app/app/out.txt'}, policy, [])


def test_credentials_and_free_text_masked():
    policy = ParameterPolicy(
        required_params=['password', 'ntlm_hash', 'domain'],
        credential_params=['password', 'ntlm_hash'],
        free_text_params=['domain'],
    )
    with pytest.raises(ParameterValidationError):
        validate_action_parameters({'password': 'pw', 'ntlm_hash': 'bad', 'domain': 'LAB'}, policy, [])
    validate_action_parameters({'password': 'pw', 'ntlm_hash': 'A' * 32, 'domain': 'LAB'}, policy, [])
    assert mask_sensitive_params({'password': 'pw', 'domain': 'LAB'}, ['password'])['password'] == '***REDACTED***'
