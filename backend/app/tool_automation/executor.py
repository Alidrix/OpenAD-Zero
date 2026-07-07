from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.parameter_validation import ParameterValidationError, validate_action_parameters
from app.core.paths import get_evidence_root
from app.core.process_runner import run_process
from app.core.scope import is_target_in_validated_scope
from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS
from app.tool_automation.parsers import parse_tool_output
from app.tool_automation.redaction import mask_command, redact_text
from app.tool_automation.results import ParsedFinding

RUNTIME_DIRS = {
    'HOME': Path('/app/runtime/home'),
    'XDG_CONFIG_HOME': Path('/app/runtime/config'),
    'XDG_CACHE_HOME': Path('/app/runtime/cache'),
    'XDG_DATA_HOME': Path('/app/runtime/data'),
    'TMPDIR': Path('/app/runtime/tmp'),
}
NXC_PATH = Path('/app/runtime/home/.nxc')
RESPONDER_RUNTIME_DIR = Path('/app/runtime/responder')


def _ensure_writable_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    probe = path / f'.openadzero-write-test-{uuid4().hex}'
    try:
        probe.write_text('ok', encoding='utf-8')
    finally:
        probe.unlink(missing_ok=True)


def ensure_tool_runtime_dirs() -> None:
    for path in RUNTIME_DIRS.values():
        _ensure_writable_dir(path)
    _ensure_writable_dir(NXC_PATH)
    _ensure_writable_dir(RUNTIME_DIRS['XDG_CONFIG_HOME'] / 'nuclei')
    _ensure_writable_dir(Path('/app/runtime/nxc'))
    _ensure_writable_dir(RESPONDER_RUNTIME_DIR)


def build_tool_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env['HOME'] = str(RUNTIME_DIRS['HOME'])
    env['XDG_CONFIG_HOME'] = str(RUNTIME_DIRS['XDG_CONFIG_HOME'])
    env['XDG_CACHE_HOME'] = str(RUNTIME_DIRS['XDG_CACHE_HOME'])
    env['XDG_DATA_HOME'] = str(RUNTIME_DIRS['XDG_DATA_HOME'])
    env['TMPDIR'] = str(RUNTIME_DIRS['TMPDIR'])
    env['NXC_PATH'] = str(NXC_PATH)
    env['NETEXEC_HOME'] = '/app/runtime/nxc'
    env['PATH'] = env.get('PATH') or os.getenv('PATH', '/go/bin:/usr/local/bin:/usr/bin:/bin')
    env.setdefault('LANG', 'C.UTF-8')
    env.setdefault('LC_ALL', 'C.UTF-8')
    return env


def tool_runs_dir() -> Path:
    return (
        Path(os.getenv('OPENAD_TOOL_RUN_DIR'))
        if os.getenv('OPENAD_TOOL_RUN_DIR')
        else get_evidence_root() / 'tool-runs'
    )


def findings_dir() -> Path:
    return (
        Path(os.getenv('OPENAD_FINDINGS_DIR')) if os.getenv('OPENAD_FINDINGS_DIR') else get_evidence_root() / 'findings'
    )


@dataclass(frozen=True)
class ToolExecutionRequest:
    tool_id: str
    template_id: str
    target: str | None
    params: dict[str, object]
    preview_command_hash: str
    human_approved: bool
    terms_accepted: bool
    final_confirmation: bool = False
    scope: list[str] | None = None


@dataclass(frozen=True)
class ToolExecutionResult:
    run_id: str
    tool_id: str
    template_id: str
    target: str | None
    status: str
    returncode: int | None
    stdout: list[str]
    stderr: list[str]
    findings: list[ParsedFinding]
    artifacts: list[str]
    started_at: str
    finished_at: str | None


def canonicalize_argv(argv: list[str]) -> str:
    return json.dumps([str(a) for a in argv], ensure_ascii=False, separators=(',', ':'))


def compute_command_hash(argv: list[str]) -> str:
    return hashlib.sha256(canonicalize_argv(argv).encode('utf-8')).hexdigest()


def persist_run(record: dict) -> None:
    data_dir = tool_runs_dir()
    findings_path = findings_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    findings_path.mkdir(parents=True, exist_ok=True)
    (data_dir / f'{record["run_id"]}.json').write_text(
        json.dumps(record, indent=2, default=_json_default), encoding='utf-8'
    )
    for finding in record.get('findings', []):
        (findings_path / f'{finding["id"]}.json').write_text(
            json.dumps(finding, indent=2, default=_json_default), encoding='utf-8'
        )


def _json_default(value):
    if hasattr(value, '__dict__'):
        return value.__dict__
    return str(value)


def load_runs() -> list[dict]:
    data_dir = tool_runs_dir()
    if not data_dir.exists():
        return []
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(data_dir.glob('*.json'))]


def load_findings() -> list[dict]:
    findings_path = findings_dir()
    if not findings_path.exists():
        return []
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(findings_path.glob('*.json'))]


def execute_tool_request(
    request: ToolExecutionRequest, argv: list[str], command_preview: str, timeout_seconds: int = 300
) -> ToolExecutionResult:
    template = COMMAND_TEMPLATE_DEFINITIONS.get(request.template_id)
    if template is not None:
        try:
            params = dict(request.params)
            if request.target and 'target' in template.required_params and 'target' not in params:
                params['target'] = request.target
            validate_action_parameters(params, template, request.scope or ([request.target] if request.target else []))
        except ParameterValidationError as exc:
            raise ValueError(str(exc)) from exc
    if request.target and not is_target_in_validated_scope(request.target, request.scope or [request.target]):
        raise ValueError('Target is outside the validated scope.')
    actual_hash = compute_command_hash(argv)
    if actual_hash != request.preview_command_hash:
        raise ValueError('Executed command hash must match the generated preview command hash.')
    run_id = str(uuid4())
    started_at = datetime.now(UTC).isoformat()
    ensure_tool_runtime_dirs()
    job_dir = tool_runs_dir() / run_id
    _ensure_writable_dir(job_dir)
    safe_env = build_tool_env()
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    status = 'running'
    returncode: int | None = None
    try:
        if not argv or not shutil.which(argv[0]):
            raise FileNotFoundError(argv[0] if argv else '')
        result_run = run_process(
            argv,
            cwd=job_dir,
            env=safe_env,
            timeout_seconds=timeout_seconds,
            stdout_path=job_dir / 'stdout.log',
            stderr_path=job_dir / 'stderr.log',
        )
        returncode = result_run.return_code
        stdout_lines = [redact_text(line) for line in result_run.stdout_tail.splitlines()]
        stderr_lines = [redact_text(line) for line in result_run.stderr_tail.splitlines()]
        status = 'success' if result_run.status == 'completed' else result_run.status
    except FileNotFoundError as exc:
        status = 'blocked'
        stderr_lines = [f'Missing binary: {exc.filename or argv[0]}']
    finished_at = datetime.now(UTC).isoformat()
    output = '\n'.join(stdout_lines + stderr_lines)
    findings = parse_tool_output(request.tool_id, request.template_id, output, request.target)
    result = ToolExecutionResult(
        run_id,
        request.tool_id,
        request.template_id,
        request.target,
        status,
        returncode,
        stdout_lines,
        stderr_lines,
        findings,
        [],
        started_at,
        finished_at,
    )
    record = {
        **asdict(result),
        'command_preview': command_preview,
        'masked_command': mask_command(argv, request.params),
        'preview_command_hash': actual_hash,
    }
    persist_run(record)
    return result
