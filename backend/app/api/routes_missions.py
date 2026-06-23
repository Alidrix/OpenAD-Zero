import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.scope import validate_scope, ScopeValidationError
from app.db.session import get_db
from app.db.models import Mission, Job, Host, Service, Finding, NextAction, SMBFact, SMBShare
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.jobs.nmap_job import run_nmap_job
from app.jobs.netexec_job import run_netexec_job, NETEXEC_TYPES
from app.core.security import ensure_netexec_template_allowed, CommandPolicyError

router=APIRouter(prefix='/missions')
class MissionCreate(BaseModel):
    name:str; scenario:str='windows_ad_internal'; mode:str='safe'; scope:str
class ApprovalRequest(BaseModel):
    approved: bool
    note: str | None = None
class IgnoreRequest(BaseModel):
    reason: str | None = None

def serialize_mission(db:Session, m:Mission):
    hosts=db.query(Host).filter_by(mission_id=m.id).all(); services=db.query(Service).filter_by(mission_id=m.id).all()
    by_host={h.id:[] for h in hosts}
    for s in services: by_host.setdefault(s.host_id,[]).append({'id':s.id,'port':s.port,'protocol':s.protocol,'name':s.name,'product':s.product,'version':s.version,'state':s.state})
    smb_facts=[{'id':f.id,'host_id':f.host_id,'ip':f.ip,'hostname':f.hostname,'domain':f.domain,'os':f.os,'smb_signing_required':f.smb_signing_required,'smbv1_enabled':f.smbv1_enabled,'null_session_possible':f.null_session_possible,'source':f.source,'raw_line':f.raw_line} for f in db.query(SMBFact).filter_by(mission_id=m.id).all()]
    smb_shares=[{'id':sh.id,'host_id':sh.host_id,'ip':sh.ip,'name':sh.name,'access':sh.access,'remark':sh.remark,'anonymous':sh.anonymous,'source':sh.source} for sh in db.query(SMBShare).filter_by(mission_id=m.id).all()]
    return {'id':m.id,'name':m.name,'scenario':m.scenario,'mode':m.mode,'status':m.status,'raw_scope':m.raw_scope,'validated_targets':m.validated_targets,'created_at':m.created_at,'started_at':m.started_at,'completed_at':m.completed_at,'smb_facts':smb_facts,'smb_shares':smb_shares, 'jobs':[{'id':j.id,'mission_id':j.mission_id,'type':j.type,'tool':j.tool,'status':j.status,'command_preview':j.command_preview,'started_at':j.started_at,'completed_at':j.completed_at,'return_code':j.return_code,'stdout_path':j.stdout_path,'stderr_path':j.stderr_path,'output_path':j.output_path} for j in db.query(Job).filter_by(mission_id=m.id).all()], 'hosts':[{'id':h.id,'ip':h.ip,'hostname':h.hostname,'status':h.status,'os_guess':h.os_guess,'is_domain_controller_candidate':h.is_domain_controller_candidate,'services':by_host.get(h.id,[])} for h in hosts], 'findings':[{'id':f.id,'host_id':f.host_id,'title':f.title,'severity':f.severity,'description':f.description,'source':f.source,'confidence':f.confidence} for f in db.query(Finding).filter_by(mission_id=m.id).all()], 'next_actions':[{'id':a.id,'title':a.title,'description':a.description,'reason':a.reason,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'status':a.status,'command_template_id':a.command_template_id} for a in db.query(NextAction).filter_by(mission_id=m.id).all()]}

@router.post('')
def create_mission(payload:MissionCreate, db:Session=Depends(get_db)):
    try: targets=validate_scope(payload.scope, get_settings().allow_public_scans).targets
    except ScopeValidationError as e: raise HTTPException(400, str(e))
    m=Mission(name=payload.name, scenario=payload.scenario, mode=payload.mode, status='scope_validated', raw_scope=payload.scope, validated_targets=targets); db.add(m); db.commit(); db.refresh(m)
    return {'mission_id':m.id,'status':m.status,'validated_targets':targets}
@router.post('/{mission_id}/start')
async def start_mission(mission_id:str, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id)
    if not m: raise HTTPException(404,'Mission not found')
    if m.status!='scope_validated': raise HTTPException(400,'Mission scope is not validated or mission already started')
    m.status='running'; m.started_at=datetime.utcnow()
    j=Job(mission_id=m.id,type='discovery',tool='nmap',status='pending',command_preview='nmap -Pn -sV --top-ports 1000 -oX <evidence-path> <validated-targets>'); db.add(j); db.commit(); db.refresh(j)
    await publish(MissionEvent(type='mission.status',mission_id=m.id,payload={'status':'running'}))
    asyncio.create_task(run_nmap_job(m.id,j.id))
    return {'mission_id':m.id,'status':'running','job_id':j.id}
@router.get('/{mission_id}')
def get_mission(mission_id:str, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id)
    if not m: raise HTTPException(404,'Mission not found')
    return serialize_mission(db,m)
@router.get('')
def list_missions(db:Session=Depends(get_db)):
    return [{'id':m.id,'name':m.name,'status':m.status,'created_at':m.created_at,'validated_targets':m.validated_targets} for m in db.query(Mission).order_by(Mission.created_at.desc()).all()]

@router.get('/{mission_id}/actions')
def list_actions(mission_id:str, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id)
    if not m: raise HTTPException(404,'Mission not found')
    return [{'id':a.id,'title':a.title,'description':a.description,'reason':a.reason,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'status':a.status,'command_template_id':a.command_template_id} for a in db.query(NextAction).filter_by(mission_id=mission_id).all()]

@router.post('/{mission_id}/actions/{action_id}/approve')
async def approve_action(mission_id:str, action_id:str, payload:ApprovalRequest, db:Session=Depends(get_db)):
    if not payload.approved: raise HTTPException(400,'Approval must be true to run this action')
    m=db.get(Mission,mission_id); a=db.get(NextAction,action_id)
    if not m: raise HTTPException(404,'Mission not found')
    if not a or a.mission_id != mission_id: raise HTTPException(404,'Action not found for mission')
    if not a.requires_approval: raise HTTPException(400,'Action does not require approval')
    if a.risk_level > 2: raise HTTPException(403,'Action prepared but automatic execution is disabled in V2')
    try: ensure_netexec_template_allowed(a.command_template_id or '')
    except CommandPolicyError as e: raise HTTPException(403, str(e))
    j=Job(mission_id=mission_id, type=a.command_template_id, tool='netexec', status='pending', command_preview='nxc <safe-template> <smb-targets>'); db.add(j); a.status='running'; db.commit(); db.refresh(j)
    asyncio.create_task(run_netexec_job(mission_id, j.id, a.id))
    return {'mission_id':mission_id,'action_id':action_id,'status':'running','job_id':j.id}

@router.post('/{mission_id}/actions/{action_id}/ignore')
def ignore_action(mission_id:str, action_id:str, payload:IgnoreRequest, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id); a=db.get(NextAction,action_id)
    if not m: raise HTTPException(404,'Mission not found')
    if not a or a.mission_id != mission_id: raise HTTPException(404,'Action not found for mission')
    a.status='ignored'; db.commit()
    return {'mission_id':mission_id,'action_id':action_id,'status':'ignored'}
