from __future__ import annotations

import hashlib
import json
import re
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.tool_automation.command_templates import COMMAND_TEMPLATES
from app.tool_automation.policy import evaluate_tool_action, load_tool_catalog
from app.tool_automation.metasploit_allowlist import build_metasploit_command, mask_metasploit_secrets, public_allowlist

router = APIRouter(prefix='/tool-automation', tags=['tool-automation'])
_RUNS: dict[str, dict] = {}
_PLACEHOLDER_RE = re.compile(r'{([a-zA-Z0-9_]+)}')

class ToolActionRequest(BaseModel):
    tool_id: str
    template_id: str | None = None
    params: dict[str, str] = Field(default_factory=dict)
    target: str | None = None
    human_approved: bool = False
    terms_accepted: bool = False
    preview_generated: bool = False
    preview_command_hash: str | None = None
    final_exploit_confirmation: bool = False
    check_run_id: str | None = None
    check_status: str | None = None
    module_id: str | None = None
    payload: str | None = None


def _hash_command(command: list[str]) -> str:
    return hashlib.sha256(json.dumps(command, separators=(",", ":")).encode()).hexdigest()

def _render(template_id: str, params: dict[str, str], target: str | None = None, masked: bool = False) -> list[str]:
    if template_id in {'metasploit_controlled_check', 'metasploit_controlled_exploit_previewable'}:
        return build_metasploit_command(template_id=template_id, target=target or params.get('target', ''), module_id=params.get('module_id'), module_path=params.get('module'), options={k: v for k, v in params.items() if k not in {'module_id', 'module', 'payload'}}, payload=params.get('payload'), masked=masked)
    argv = COMMAND_TEMPLATES.get(template_id)
    if argv is None:
        raise HTTPException(status_code=400, detail='Selected template is not allowed for this tool.')
    rendered: list[str] = []
    for arg in argv:
        missing = [name for name in _PLACEHOLDER_RE.findall(arg) if name not in params]
        if missing:
            raise HTTPException(status_code=400, detail=f'Missing template parameter: {missing[0]}')
        rendered.append(arg.format(**params))
    return rendered

@router.get('/tools')
def tools():
    return list(load_tool_catalog().values())

@router.get('/metasploit/allowlist')
def metasploit_allowlist():
    return public_allowlist()

@router.get('/templates')
def templates():
    from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS
    return [{**COMMAND_TEMPLATE_DEFINITIONS[tid].__dict__, 'placeholders': sorted(set(_PLACEHOLDER_RE.findall(' '.join(argv))))} for tid, argv in COMMAND_TEMPLATES.items()]

@router.post('/preview')
def preview(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='preview', target_in_scope=True, selected_template_id=payload.template_id, metasploit_module_id=payload.params.get('module_id'), metasploit_module=payload.params.get('module'), metasploit_options={k: v for k, v in payload.params.items() if k not in {'module_id','module','payload'}}, metasploit_payload=payload.params.get('payload'))
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    try:
        command = _render(payload.template_id, payload.params, payload.target) if payload.template_id else []
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    command_hash = _hash_command(command)
    return {'decision': decision, 'command': command, 'command_preview': mask_metasploit_secrets(' '.join(command)), 'command_hash': command_hash, 'preview_command_hash': command_hash}

@router.post('/approve')
def approve(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='approve', target_in_scope=True, selected_template_id=payload.template_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return {'decision': decision, 'approved': True}

@router.post('/run')
def run(payload: ToolActionRequest):
    try:
        command = _render(payload.template_id, payload.params, payload.target) if payload.template_id else []
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    command_hash = _hash_command(command)
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='run', target_in_scope=True, selected_template_id=payload.template_id, preview_generated=payload.preview_generated, human_approved=payload.human_approved, terms_accepted=payload.terms_accepted, argv=command, command_hash=command_hash, preview_command_hash=payload.preview_command_hash, final_exploit_confirmation=payload.final_exploit_confirmation, check_run_id=payload.check_run_id, check_status=payload.check_status, metasploit_module_id=payload.params.get('module_id'), metasploit_module=payload.params.get('module'), metasploit_options={k: v for k, v in payload.params.items() if k not in {'module_id','module','payload'}}, metasploit_payload=payload.params.get('payload'))
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    run_id = str(uuid4())
    record = {'run_id': run_id, 'tool_id': payload.tool_id, 'template_id': payload.template_id, 'status': 'queued', 'command_preview': mask_metasploit_secrets(' '.join(command)), 'command_hash': command_hash, 'stdout': [], 'stderr': [], 'artifacts': []}
    _RUNS[run_id] = record
    return record

@router.get('/presets')
def presets():
    import yaml
    from pathlib import Path
    path = Path(__file__).parents[1] / 'tool_automation' / 'workflow_presets.yml'
    return yaml.safe_load(path.read_text())

@router.get('/findings')
def findings(tool_id: str | None = Query(default=None)):
    rows = []
    for run in _RUNS.values():
        for item in run.get('findings', []):
            if not tool_id or item.get('tool_id') == tool_id:
                rows.append(item)
    return rows

@router.get('/suggestions')
def suggestions():
    from app.tool_automation.correlation import suggest_metasploit_searches
    return [s.__dict__ for s in suggest_metasploit_searches([])]

@router.post('/metasploit/suggest')
def metasploit_suggest(findings_payload: list[dict]):
    from app.tool_automation.correlation import suggest_metasploit_searches
    from app.tool_automation.results import ParsedFinding
    findings = [ParsedFinding(**item) for item in findings_payload]
    return [s.__dict__ for s in suggest_metasploit_searches(findings)]

@router.get('/runs/{run_id}')
def get_run(run_id: str):
    if run_id not in _RUNS:
        raise HTTPException(status_code=404, detail='Run not found')
    return _RUNS[run_id]

@router.get('/runs')
def list_runs(tool_id: str | None = Query(default=None)):
    runs = list(_RUNS.values())
    return [r for r in runs if not tool_id or r['tool_id'] == tool_id]
