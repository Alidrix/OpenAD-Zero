from app.tool_automation import tool_health


def test_tool_health_uses_runtime_env_for_netexec_and_nuclei(monkeypatch):
    calls = []
    monkeypatch.setattr(tool_health, 'ensure_tool_runtime_dirs', lambda: None)
    monkeypatch.setattr(
        tool_health, 'runtime_dir_status', lambda: {'home': {'path': '/app/runtime/home', 'writable': True}}
    )
    monkeypatch.setattr(
        tool_health.shutil, 'which', lambda binary: f'/usr/bin/{binary}' if binary in {'nxc', 'nuclei'} else None
    )

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))

        class Result:
            stdout_tail = 'ok\n'
            stderr_tail = ''
            status = 'completed'
            return_code = 0

        return Result()

    monkeypatch.setattr(tool_health, 'run_process', fake_run)
    result = tool_health.collect_tool_health()

    assert result['status'] == 'ok'
    nxc_call = next(kwargs for argv, kwargs in calls if argv[0] == 'nxc')
    nuclei_call = next(kwargs for argv, kwargs in calls if argv[0] == 'nuclei')
    assert nxc_call['env']['HOME'] == '/app/runtime/home'
    assert nxc_call['env']['NXC_PATH'] == '/app/runtime/home/.nxc'
    assert nxc_call['env']['HOME'] != '/app'
    assert nuclei_call['env']['XDG_CONFIG_HOME'] == '/app/runtime/config'
    assert nuclei_call['env']['XDG_CONFIG_HOME'] != '/app/.config'
    assert str(nxc_call['cwd']) == '/app/evidence'


def test_tool_health_reports_misconfigured_runtime(monkeypatch):
    monkeypatch.setattr(tool_health, 'ensure_tool_runtime_dirs', lambda: None)
    monkeypatch.setattr(
        tool_health, 'runtime_dir_status', lambda: {'tmp': {'path': '/app/runtime/tmp', 'writable': False}}
    )
    monkeypatch.setattr(tool_health.shutil, 'which', lambda _: None)
    assert tool_health.collect_tool_health()['status'] == 'misconfigured'
