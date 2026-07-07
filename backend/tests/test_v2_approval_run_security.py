from app.approvals.run_service import SUPPORTED_EXECUTABLE_TEMPLATES
from app.approvals.schemas import ApprovalRunRequest


def test_run_payload_forbids_command_material():
    for field in ['command', 'argv', 'shell', 'raw_command', 'command_hash', 'command_preview']:
        try:
            ApprovalRunRequest(operator='op', **{field: 'bad'})
        except Exception:
            pass
        else:
            raise AssertionError(f'{field} was accepted')


def test_prompt10_allowlist_excludes_high_risk_templates():
    forbidden = {
        'secretsdump',
        'kerbrute_passwordspray_safe_preview',
        'donpapi_collect_target',
        'responder_lab_capture',
    }
    assert not (SUPPORTED_EXECUTABLE_TEMPLATES & forbidden)
