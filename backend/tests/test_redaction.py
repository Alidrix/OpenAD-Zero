import json
from pathlib import Path

from app.tool_automation.redaction import MASK, mask_command, redact_mapping, redact_text
from app.tool_automation.results import make_finding


def test_results_py_does_not_use_sha1_and_uses_sha256():
    source = (Path(__file__).parents[1] / 'app/tool_automation/results.py').read_text()
    assert 'sha1' not in source
    assert 'sha256' in source


def test_finding_id_does_not_depend_on_raw_secret_and_evidence_is_redacted():
    finding = make_finding(
        tool_id='donpapi',
        template_id='donpapi_collect_target',
        target='10.10.10.5',
        category='credential_artifact',
        severity='high',
        title='Credential artifact found',
        description='desc',
        raw='password=SuperSecretPassword123',
        fields={'username': 'alice', 'password': 'SuperSecretPassword123'},
    )
    serialized = json.dumps(finding.__dict__, default=str)
    assert 'SuperSecretPassword123' not in finding.id
    assert 'SuperSecretPassword123' not in serialized
    assert MASK in serialized


def test_raw_evidence_is_not_part_of_finding_identity_seed():
    a = make_finding(
        'donpapi',
        'donpapi_collect_target',
        '10.10.10.5',
        'credential_artifact',
        'high',
        'Credential artifact found',
        'desc',
        'password=OneSecret',
        {'username': 'alice'},
    )
    b = make_finding(
        'donpapi',
        'donpapi_collect_target',
        '10.10.10.5',
        'credential_artifact',
        'high',
        'Credential artifact found',
        'desc',
        'password=DifferentSecret',
        {'username': 'alice'},
    )
    assert a.id == b.id


def test_sensitive_parsed_fields_are_redacted_before_hash():
    redacted = redact_mapping(
        {'password': 'SuperSecretPassword123', 'nested': {'api_key': 'abc'}, 'note': 'token=abc123'}
    )
    assert redacted['password'] == MASK
    assert redacted['nested']['api_key'] == MASK
    assert redacted['note'] == f'token={MASK}'


def test_redact_text_masks_ntlm_hash_token_secret_and_key():
    text = 'token=abc secret=hunter2 api_key=xyz hash aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c'
    out = redact_text(text)
    assert 'abc' not in out and 'hunter2' not in out and 'xyz' not in out
    assert '8846f7eaee8fb117ad06bdd830b7586c' not in out
    assert MASK in out


def test_mask_command_masks_metasploit_smbpass_and_ntlm_hash():
    command = [
        'msfconsole',
        '-q',
        '-x',
        'set SMBUser alice; set SMBPass SuperSecretPassword123; set SMBPass 8846f7eaee8fb117ad06bdd830b7586c; run',
    ]
    masked = mask_command(command, {'SMBPass': 'SuperSecretPassword123'})
    serialized = json.dumps(masked)
    assert 'SuperSecretPassword123' not in serialized
    assert '8846f7eaee8fb117ad06bdd830b7586c' not in serialized
    assert MASK in serialized
