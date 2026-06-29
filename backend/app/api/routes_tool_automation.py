from __future__ import annotations

import re
import shutil
import subprocess

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from app.core.scope import is_target_in_validated_scope
from app.tool_automation.command_templates import COMMAND_TEMPLATES, COMMAND_TEMPLATE_DEFINITIONS
from app.tool_automation.policy import evaluate_tool_action, load_tool_catalog
from app.tool_automation.executor import ToolExecutionRequest, compute_command_hash, execute_tool_request, load_findings, load_runs
from app.tool_automation.redaction import mask_command, redact_mapping

router = APIRouter(prefix='/tool-automation', tags=['tool-automation'])
_RUNS: dict[str, dict] = {}
_PLACEHOLDER_RE = re.compile(r'{([a-zA-Z0-9_]+)}')

class ToolActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool_id: str
    template_id: str | None = None
    params: dict[str, str] = Field(default_factory=dict)
    target: str | None = None
    human_approved: bool = False
    terms_accepted: bool = False
    preview_generated: bool = False
    preview_command_hash: str | None = None
    scope: list[str] = Field(default_factory=list)
    final_confirmation: bool = False
    final_exploit_confirmation: bool = False
    check_run_id: str | None = None
    check_status: str | None = None



def _masked_preview(command: list[str], params: dict[str, str]) -> tuple[list[str], str]:
    masked = mask_command(command, params)
    return masked, ' '.join(masked)

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


def _target_in_scope(payload: ToolActionRequest) -> bool:
    if not payload.target:
        return True
    return is_target_in_validated_scope(payload.target, payload.scope or [payload.target])

@router.get('/tools')
def tools():
    return list(load_tool_catalog().values())

@router.get('/templates')
def templates():
    from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS
    return [{**COMMAND_TEMPLATE_DEFINITIONS[tid].__dict__, 'placeholders': sorted(set(_PLACEHOLDER_RE.findall(' '.join(argv))))} for tid, argv in COMMAND_TEMPLATES.items()]

@router.post('/preview')
def preview(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='preview', target_in_scope=_target_in_scope(payload), selected_template_id=payload.template_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    command = _render(payload.template_id, payload.params) if payload.template_id else []
    command_hash = compute_command_hash(command)
    masked_command, command_preview = _masked_preview(command, payload.params)
    return {'decision': decision, 'masked_command': masked_command, 'command': masked_command, 'command_preview': command_preview, 'preview_command_hash': command_hash}

@router.post('/approve')
def approve(payload: ToolActionRequest):
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='approve', target_in_scope=_target_in_scope(payload), selected_template_id=payload.template_id)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    return {'decision': decision, 'approved': True}

@router.post('/run')
def run(payload: ToolActionRequest):
    raw = getattr(payload, '__pydantic_extra__', None) or {}
    if 'command' in raw:
        raise HTTPException(status_code=400, detail='Raw commands are not accepted.')
    command = _render(payload.template_id, payload.params) if payload.template_id else []
    command_hash = compute_command_hash(command)
    decision = evaluate_tool_action(tool_id=payload.tool_id, action='run', target_in_scope=_target_in_scope(payload), selected_template_id=payload.template_id, preview_generated=payload.preview_generated, human_approved=payload.human_approved, terms_accepted=payload.terms_accepted, argv=command, command_hash=command_hash, preview_command_hash=payload.preview_command_hash)
    if not decision.allowed:
        raise HTTPException(status_code=403, detail=decision.reason)
    masked_command, command_preview = _masked_preview(command, payload.params)
    timeout = 300
    try:
        result = execute_tool_request(ToolExecutionRequest(payload.tool_id, payload.template_id or '', payload.target, dict(payload.params), payload.preview_command_hash or '', payload.human_approved, payload.terms_accepted, payload.final_confirmation or payload.final_exploit_confirmation, payload.scope), command, command_preview, timeout)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    record = result.__dict__ | {'masked_command': masked_command, 'command_preview': command_preview, 'preview_command_hash': command_hash}
    _RUNS[result.run_id] = record
    return redact_mapping(record)

@router.get('/presets')
def presets():
    import yaml
    from pathlib import Path
    path = Path(__file__).parents[1] / 'tool_automation' / 'workflow_presets.yml'
    return yaml.safe_load(path.read_text())

@router.get('/findings')
def findings(tool_id: str | None = Query(default=None), target: str | None = Query(default=None)):
    rows = load_findings()
    for run in list(_RUNS.values()):
        for item in run.get('findings', []):
            rows.append(item if isinstance(item, dict) else item.__dict__)
    return [redact_mapping(item) for item in rows if (not tool_id or item.get('tool_id') == tool_id) and (not target or item.get('target') == target)]


@router.get('/tool-health')
def tool_health():
    checks = {
        'nmap': ['nmap', '--version'], 'nuclei': ['nuclei', '-version'], 'netexec': ['nxc', '--version'],
        'enum4linux-ng': ['enum4linux-ng', '-h'], 'kerbrute': ['kerbrute', '-h'], 'impacket': ['GetNPUsers.py', '-h'],
        'gMSADumper': ['gMSADumper.py', '-h'], 'DonPAPI': ['DonPAPI', '-h'], 'Coercer': ['coercer', '-h'],
        'BloodyAD': ['bloodyAD', '-h'], 'Responder': ['responder', '-h'], 'metasploit': ['msfconsole', '-v'],
    }
    out = {}
    for name, argv in checks.items():
        if not shutil.which(argv[0]):
            out[name] = {'available': False, 'reason': f'{argv[0]} not installed'}
            continue
        try:
            cp = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=10)
            version = (cp.stdout or cp.stderr).splitlines()[0] if (cp.stdout or cp.stderr) else 'available'
            out[name] = {'available': True, 'version': version}
        except Exception as exc:
            out[name] = {'available': False, 'reason': str(exc)}
    return out

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
    return redact_mapping(_RUNS[run_id])

@router.get('/runs')
def list_runs(tool_id: str | None = Query(default=None)):
    runs = load_runs() + list(_RUNS.values())
    return [redact_mapping(r) for r in runs if not tool_id or r['tool_id'] == tool_id]
