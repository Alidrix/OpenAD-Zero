# V2 Job Runtime Hardening

OpenAD-Zero now routes controlled external process execution through `backend/app/core/process_runner.py`.

## Shared runner

`run_process(argv, cwd, env, timeout_seconds, stdout_path, stderr_path, redaction_patterns, max_log_bytes)` accepts only `list[str]` argv and always uses `shell=False`. The working directory must be under the configured evidence/artifact root.

## Timeout and cleanup

The runner is Linux/container-first. It starts tools in a new session and kills the whole process group on timeout, waits after termination, and returns status `timeout` instead of a generic failure.

## Bounded logs and redaction

Stdout/stderr stream directly to files. API/event tails are bounded by `OPENADZERO_PROCESS_LOG_TAIL_BYTES` and redacted through centralized tool automation redaction. Raw artifacts remain on disk for operator-controlled evidence review; short tails, events, metadata, and masked commands must never expose tokens, passwords, hashes, or Authorization headers.

## Statuses and events

Canonical statuses are `queued`, `running`, `completed`, `failed`, `timeout`, `cancelled`, `stopping`, and `blocked`. Process events use `process.started`, `process.completed`, `process.failed`, and `process.timeout` payloads with masked command/log material only.

## Cancel/stop limits

Queued job cancellation remains handled by existing job APIs. Running process cleanup is covered for runner-backed executions when the process exits through timeout/error handling. A future Prompt 14 can add cooperative live cancellation tokens for currently running RQ jobs.

## Security notes

The runner does not accept raw frontend commands, does not run high-risk templates automatically, and does not bypass approvals or scope validation.
