from __future__ import annotations

import shutil
from pathlib import Path

from app.core.process_runner import run_process
from app.tool_automation.executor import build_tool_env, ensure_tool_runtime_dirs

CHECKS = {
    'nmap': ['nmap', '--version'],
    'nuclei': ['nuclei', '-version'],
    'netexec': ['nxc', '--help'],
    'enum4linux-ng': ['enum4linux-ng', '-h'],
    'kerbrute': ['kerbrute', '-h'],
    'impacket': ['GetNPUsers.py', '-h'],
    'gMSADumper': ['gMSADumper.py', '-h'],
    'DonPAPI': ['DonPAPI', '-h'],
    'Coercer': ['coercer', '-h'],
    'BloodyAD': ['bloodyAD', '-h'],
    'Responder': ['responder', '-h'],
    'metasploit': ['msfconsole', '-v'],
}

RUNTIME_CHECKS = {
    'home': Path('/app/runtime/home'),
    'nxc': Path('/app/runtime/home/.nxc'),
    'xdg_config': Path('/app/runtime/config'),
    'xdg_cache': Path('/app/runtime/cache'),
    'tmp': Path('/app/runtime/tmp'),
    'evidence': Path('/app/evidence'),
}


def is_writable_dir(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / '.openadzero-health-write-test'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def runtime_dir_status() -> dict[str, dict[str, object]]:
    return {name: {'path': str(path), 'writable': is_writable_dir(path)} for name, path in RUNTIME_CHECKS.items()}


def collect_tool_health(timeout: int = 10) -> dict[str, object]:
    ensure_tool_runtime_dirs()
    env = build_tool_env()
    runtime_dirs = runtime_dir_status()
    any_misconfigured = any(not item['writable'] for item in runtime_dirs.values())
    out: dict[str, object] = {
        'status': 'misconfigured' if any_misconfigured else 'ok',
        'runtime_dirs': runtime_dirs,
        'tools': {},
    }
    tools: dict[str, dict[str, object]] = {}
    for name, argv in CHECKS.items():
        if not shutil.which(argv[0]):
            tools[name] = {'available': False, 'reason': f'{argv[0]} not installed'}
            continue
        try:
            result = run_process(argv, cwd=Path('/app/evidence'), env=env, timeout_seconds=timeout)
            output = result.stdout_tail or result.stderr_tail
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            if name == 'metasploit':
                version = next(
                    (line for line in lines if line.startswith('Framework Version:')),
                    lines[-1] if lines else 'available',
                )
            elif name == 'impacket':
                version = next(
                    (line for line in lines if line.startswith('Impacket ')), lines[0] if lines else 'available'
                )
            else:
                version = lines[0] if lines else 'available'
            tools[name] = {'available': True, 'version': version}
        except Exception as exc:
            tools[name] = {'available': False, 'reason': str(exc)}
    out['tools'] = tools
    return out
