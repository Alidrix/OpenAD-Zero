from __future__ import annotations

import asyncio
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.core.process_runner import run_process
from app.core.security import ensure_allowed_tool
from app.events.publisher import publish
from app.events.schemas import MissionEvent


class CommandResult:
    def __init__(self, return_code: int | None, timed_out: bool = False, status: str = 'failed'):
        self.return_code = return_code
        self.timed_out = timed_out
        self.status = status


async def run_command(
    tool: str,
    args: list[str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    mission_id: str,
    job_id: str,
    timeout: int,
) -> CommandResult:
    ensure_allowed_tool(tool)
    if shutil.which(tool) is None:
        await publish(
            MissionEvent(
                type='job.log',
                mission_id=mission_id,
                payload={
                    'job_id': job_id,
                    'line': f'[{tool}] executable not found. Install {tool} or use Docker Compose.',
                },
            )
        )
        return CommandResult(127, False, 'failed')
    await publish(
        MissionEvent(type='process.started', mission_id=mission_id, payload={'job_id': job_id, 'tool_id': tool})
    )
    result = await asyncio.to_thread(
        run_process,
        [tool, *args],
        cwd,
        None,
        timeout,
        stdout_path,
        stderr_path,
        None,
        get_settings().openadzero_process_max_log_bytes,
    )
    await publish(
        MissionEvent(
            type=f'process.{result.status}',
            mission_id=mission_id,
            payload={
                'job_id': job_id,
                'tool_id': tool,
                'status': result.status,
                'return_code': result.return_code,
                'duration_seconds': result.duration_seconds,
                'stdout_tail_redacted': result.stdout_tail,
                'stderr_tail_redacted': result.stderr_tail,
                'error_message_redacted': result.error_message,
            },
        )
    )
    return CommandResult(result.return_code, result.timed_out, result.status)
