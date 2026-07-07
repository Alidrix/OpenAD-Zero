from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.core.paths import get_evidence_root
from app.tool_automation.redaction import mask_command, redact_text


@dataclass(frozen=True)
class ProcessRunResult:
    argv_masked: list[str]
    return_code: int | None
    status: str
    timed_out: bool
    started_at: str
    completed_at: str
    duration_seconds: float
    stdout_path: str | None
    stderr_path: str | None
    stdout_tail: str
    stderr_tail: str
    error_message: str | None = None


def _ensure_argv(argv: list[str]) -> None:
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise TypeError('argv must be a non-empty list[str]')


def _ensure_cwd(cwd: Path) -> Path:
    if not isinstance(cwd, Path):
        raise TypeError('cwd must be a pathlib.Path')
    resolved = cwd.resolve()
    root = get_evidence_root(create=True).resolve()
    if root not in (resolved, *resolved.parents):
        raise ValueError('cwd must be under the configured evidence/artifact root')
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _bounded_tail(path: Path | None, limit: int, patterns: Sequence[str] | None) -> str:
    if path is None or not path.exists():
        return ''
    with path.open('rb') as fh:
        size = path.stat().st_size
        fh.seek(max(0, size - limit))
        data = fh.read(limit)
    text = data.decode('utf-8', errors='replace')
    text = redact_text(text)
    for pattern in patterns or []:
        if pattern:
            text = text.replace(pattern, '********')
    return text


def _truncate_if_needed(path: Path, max_bytes: int) -> None:
    if path.exists() and path.stat().st_size > max_bytes:
        with path.open('rb') as fh:
            fh.seek(-max_bytes, os.SEEK_END)
            data = fh.read(max_bytes)
        path.write_bytes(b'[openadzero] log truncated to max_log_bytes\n' + data)


def _kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        proc.wait(timeout=5)


def run_process(
    argv: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout_seconds: int = 900,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
    redaction_patterns: list[str] | None = None,
    max_log_bytes: int = 5_000_000,
) -> ProcessRunResult:
    _ensure_argv(argv)
    if timeout_seconds <= 0:
        raise ValueError('timeout_seconds must be positive')
    cwd = _ensure_cwd(cwd)
    settings = get_settings()
    tail_bytes = int(getattr(settings, 'openadzero_process_log_tail_bytes', 20000))
    max_bytes = int(max_log_bytes or getattr(settings, 'openadzero_process_max_log_bytes', 5000000))
    stdout_path = (stdout_path or cwd / 'stdout.log').resolve()
    stderr_path = (stderr_path or cwd / 'stderr.log').resolve()
    for p in (stdout_path, stderr_path):
        if cwd not in (p, *p.parents):
            raise ValueError('stdout/stderr paths must be under cwd')
        p.parent.mkdir(parents=True, exist_ok=True)
    started_dt = datetime.now(UTC)
    started = time.monotonic()
    return_code: int | None = None
    timed_out = False
    error_message = None
    with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
        proc = subprocess.Popen(
            argv, cwd=str(cwd), env=env, stdout=out, stderr=err, shell=False, start_new_session=True
        )
        try:
            return_code = proc.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            error_message = 'timeout'
            _kill_process_group(proc)
            return_code = proc.returncode if proc.returncode is not None else -9
    _truncate_if_needed(stdout_path, max_bytes)
    _truncate_if_needed(stderr_path, max_bytes)
    completed_dt = datetime.now(UTC)
    duration = time.monotonic() - started
    status = 'timeout' if timed_out else ('completed' if return_code == 0 else 'failed')
    err_redacted = redact_text(error_message) if error_message else None
    return ProcessRunResult(
        argv_masked=mask_command(argv),
        return_code=return_code,
        status=status,
        timed_out=timed_out,
        started_at=started_dt.isoformat(),
        completed_at=completed_dt.isoformat(),
        duration_seconds=round(duration, 3),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        stdout_tail=_bounded_tail(stdout_path, tail_bytes, redaction_patterns),
        stderr_tail=_bounded_tail(stderr_path, tail_bytes, redaction_patterns),
        error_message=err_redacted,
    )
