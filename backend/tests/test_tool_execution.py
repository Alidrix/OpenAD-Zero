from app.tool_automation.executor import ToolExecutionRequest, compute_command_hash, execute_tool_request


def test_executor_uses_shell_false_and_parses_findings(monkeypatch, tmp_path):
    calls = {}

    def fake_run(argv, **kwargs):
        calls['argv'] = argv
        calls['kwargs'] = kwargs

        class Result:
            return_code = 0
            status = 'completed'
            stdout_tail = '445/tcp open microsoft-ds Windows Server\n'
            stderr_tail = ''

        return Result()

    monkeypatch.setattr('app.tool_automation.executor.shutil.which', lambda _: '/bin/tool')
    monkeypatch.setattr('app.tool_automation.executor.run_process', fake_run)
    monkeypatch.setenv('OPENAD_TOOL_RUN_DIR', str(tmp_path / 'runs'))
    argv = ['nmap', '-sV', '10.0.0.5']
    result = execute_tool_request(
        ToolExecutionRequest(
            'nmap_safe_discovery',
            'nmap_safe_discovery',
            '10.0.0.5',
            {'target': '10.0.0.5'},
            compute_command_hash(argv),
            True,
            True,
            scope=['10.0.0.0/24'],
        ),
        argv,
        'nmap -sV 10.0.0.5',
    )
    assert isinstance(calls['argv'], list)
    assert result.status == 'success'
    assert result.findings


def test_executor_rejects_hash_mismatch():
    try:
        execute_tool_request(
            ToolExecutionRequest(
                'nmap_safe_discovery', 'nmap_safe_discovery', '10.0.0.5', {}, 'bad', True, True, scope=['10.0.0.0/24']
            ),
            ['nmap', '10.0.0.5'],
            'nmap 10.0.0.5',
        )
    except ValueError as exc:
        assert 'hash' in str(exc)
    else:
        raise AssertionError('hash mismatch accepted')
