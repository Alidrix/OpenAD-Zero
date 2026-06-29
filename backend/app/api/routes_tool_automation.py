from __future__ import annotations

import re
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.tool_automation.command_templates import COMMAND_TEMPLATES
from app.tool_automation.policy import evaluate_tool_action, load_tool_catalog

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


def _render(template_id: str, params: dict[str, str]) -> list[str]:
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

@router.get('/templates')
def templates():
    return [{'id': tid, 'argv': argv, 'placeholders': sorted(set(_PLACEHOLDER_RE.findall(' '.join(argv))))} for tid, argv in COMMAND_TEMPLATES.items()]

@router.post('/preview')
def preview(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='preview', target_in_scope=True, selected_template_id=payload.template_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    command = _render(payload.template_id, payload.params) if payload.template_id else []
    return {'decision': decision, 'command': command, 'command_preview': ' '.join(command)}

@router.post('/approve')
def approve(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='approve', target_in_scope=True, selected_template_id=payload.template_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return {'decision': decision, 'approved': True}

@router.post('/run')
def run(payload: ToolActionRequest):
    command = _render(payload.template_id, payload.params) if payload.template_id else []
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='run', target_in_scope=True, selected_template_id=payload.template_id, preview_generated=payload.preview_generated, human_approved=payload.human_approved, terms_accepted=payload.terms_accepted, argv=command)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    run_id = str(uuid4())
    record = {'run_id': run_id, 'tool_id': payload.tool_id, 'template_id': payload.template_id, 'status': 'queued', 'command_preview': ' '.join(command), 'stdout': [], 'stderr': [], 'artifacts': []}
    _RUNS[run_id] = record
    return record

@router.get('/runs/{run_id}')
def get_run(run_id: str):
    if run_id not in _RUNS:
        raise HTTPException(status_code=404, detail='Run not found')
    return _RUNS[run_id]

@router.get('/runs')
def list_runs(tool_id: str | None = Query(default=None)):
    runs = list(_RUNS.values())
    return [r for r in runs if not tool_id or r['tool_id'] == tool_id]
