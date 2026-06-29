import subprocess

from app.tool_automation import executor
from app.tool_automation.executor import (
    ToolExecutionRequest,
    build_tool_env,
    compute_command_hash,
    execute_tool_request,
)


def test_build_tool_env_points_tools_at_runtime():
    env = build_tool_env({'PATH': '/custom/bin'})
    assert env['HOME'] == '/app/runtime/home'
    assert env['NXC_PATH'] == '/app/runtime/home/.nxc'
    assert env['XDG_CONFIG_HOME'] == '/app/runtime/config'
    assert env['XDG_CACHE_HOME'] == '/app/runtime/cache'
    assert env['TMPDIR'] == '/app/runtime/tmp'
    assert env['PATH'] == '/custom/bin'


def test_executor_runs_in_job_dir_with_runtime_env(monkeypatch, tmp_path):
    calls = {}

    def fake_run(argv, **kwargs):
        calls['argv'] = argv
        calls['kwargs'] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout='', stderr='')

    monkeypatch.setattr(executor, 'ensure_tool_runtime_dirs', lambda: None)
    monkeypatch.setattr(executor, '_ensure_writable_dir', lambda path: path.mkdir(parents=True, exist_ok=True))
    monkeypatch.setattr('app.tool_automation.executor.shutil.which', lambda _: '/bin/tool')
    monkeypatch.setattr('app.tool_automation.executor.subprocess.run', fake_run)
    monkeypatch.setenv('OPENAD_TOOL_RUN_DIR', str(tmp_path / 'runs'))
    monkeypatch.setenv('OPENAD_FINDINGS_DIR', str(tmp_path / 'findings'))

    argv = ['nmap', '-sV', '10.0.0.5']
    execute_tool_request(
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

    assert calls['kwargs']['shell'] is False
    assert calls['kwargs']['cwd'].startswith(str(tmp_path / 'runs'))
    assert calls['kwargs']['env']['HOME'] == '/app/runtime/home'
    assert calls['kwargs']['env']['NXC_PATH'] == '/app/runtime/home/.nxc'
