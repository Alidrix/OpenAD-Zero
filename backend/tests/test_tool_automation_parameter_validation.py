from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS


def test_tool_preview_rejects_unexpected_and_forbidden_fields(client):
    payload = {
        'tool_id': 'nmap_safe_discovery',
        'template_id': 'nmap_safe_discovery',
        'params': {'target': '10.0.0.5', 'dc_ip': '10.0.0.9'},
        'target': '10.0.0.5',
        'scope': ['10.0.0.0/24'],
    }
    assert client.post('/api/tool-automation/preview', json=payload).status_code == 400
    bad = dict(payload)
    bad['command'] = 'id'
    assert client.post('/api/tool-automation/preview', json=bad).status_code == 422


def test_tool_preview_masks_credentials(client, isolated_evidence_dir):
    isolated_evidence_dir.mkdir(parents=True, exist_ok=True)
    userlist = isolated_evidence_dir / 'users.txt'
    userlist.write_text('alice')
    payload = {
        'tool_id': 'kerbrute',
        'template_id': 'kerbrute_passwordspray_safe_preview',
        'params': {'dc_ip': '10.0.0.10', 'domain': 'LAB', 'userlist': str(userlist), 'password': 'Secret123!'},
        'scope': ['10.0.0.0/24'],
    }
    response = client.post('/api/tool-automation/preview', json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert 'Secret123!' not in str(body)
    assert '***REDACTED***' in str(body)


def test_tool_run_revalidates_parameters(client):
    payload = {
        'tool_id': 'nmap_safe_discovery',
        'template_id': 'nmap_safe_discovery',
        'params': {'target': '10.0.1.5'},
        'target': '10.0.1.5',
        'scope': ['10.0.0.0/24'],
        'preview_generated': True,
        'human_approved': True,
        'terms_accepted': True,
        'preview_command_hash': 'bad',
    }
    assert client.post('/api/tool-automation/run', json=payload).status_code in {400, 403}


def test_no_template_accepts_raw_command_params():
    forbidden = {'command', 'argv', 'shell', 'raw_command', 'command_hash'}
    for template in COMMAND_TEMPLATE_DEFINITIONS.values():
        assert not forbidden & set(template.required_params + template.optional_params)
