from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.scope import validate_scope, ScopeValidationError
from app.db.session import get_db
from app.db.models import Mission, Job, Host, Service, Finding, NextAction, SMBFact, SMBShare, WebTarget, BloodHoundCollection, ManualActionCard, Evidence
from app.events.publisher import publish
from app.queue.enqueue import enqueue_job
from app.events.schemas import MissionEvent
from app.jobs.netexec_job import ALLOWED_TEMPLATES as NETEXEC_TEMPLATES
from app.jobs.nuclei_job import ALLOWED_TEMPLATES as NUCLEI_TEMPLATES
from app.integrations.nuclei.targets import ensure_web_targets_for_mission
from app.integrations.bloodhound.zip_inspector import inspect_sharphound_zip, sha256_file
from app.integrations.bloodhound.ingest import ingest_collection
from app.integrations.bloodhound.stats import empty_stats
from app.planner.next_actions import plan_after_bloodhound_upload
from app.capabilities.catalog import get_capability, creates_manual_card_only
from pathlib import Path
import json
import logging
from app.operations.service import initialize_operations_for_mission, safe_sync
from app.operations.phases import mark_phase_completed, update_phase_status
from app.operations.schemas import TimelineEventCreate
from app.operations.timeline import create_timeline_event
log=logging.getLogger(__name__)

router=APIRouter(prefix='/missions')
class MissionCreate(BaseModel):
    name:str; scenario:str='windows_ad_internal'; mode:str='safe'; scope:str

def serialize_mission(db:Session, m:Mission):
    hosts=db.query(Host).filter_by(mission_id=m.id).all(); services=db.query(Service).filter_by(mission_id=m.id).all(); ev_rows=db.query(Evidence.category).filter_by(mission_id=m.id).all(); ev_cats={}; [ev_cats.__setitem__(r[0], ev_cats.get(r[0],0)+1) for r in ev_rows]
    by_host={h.id:[] for h in hosts}
    for s in services: by_host.setdefault(s.host_id,[]).append({'id':s.id,'port':s.port,'protocol':s.protocol,'name':s.name,'product':s.product,'version':s.version,'state':s.state})
    return {'id':m.id,'name':m.name,'scenario':m.scenario,'mode':m.mode,'status':m.status,'raw_scope':m.raw_scope,'validated_targets':m.validated_targets,'created_at':m.created_at,'started_at':m.started_at,'completed_at':m.completed_at, 'evidence_summary':{'count':len(ev_rows),'categories':ev_cats}, 'jobs':[{'id':j.id,'mission_id':j.mission_id,'type':j.type,'tool':j.tool,'status':j.status,'command_preview':j.command_preview,'started_at':j.started_at,'completed_at':j.completed_at,'return_code':j.return_code,'stdout_path':j.stdout_path,'stderr_path':j.stderr_path,'output_path':j.output_path} for j in db.query(Job).filter_by(mission_id=m.id).all()], 'hosts':[{'id':h.id,'ip':h.ip,'hostname':h.hostname,'status':h.status,'os_guess':h.os_guess,'is_domain_controller_candidate':h.is_domain_controller_candidate,'services':by_host.get(h.id,[]), 'smb_facts':[{'hostname':sf.hostname,'domain':sf.domain,'os':sf.os,'smb_signing_required':sf.smb_signing_required,'smbv1_enabled':sf.smbv1_enabled,'null_session_possible':sf.null_session_possible,'source':sf.source} for sf in db.query(SMBFact).filter_by(mission_id=m.id, ip=h.ip).all()], 'smb_shares':[{'name':sh.name,'access':sh.access,'remark':sh.remark,'anonymous':sh.anonymous,'source':sh.source} for sh in db.query(SMBShare).filter_by(mission_id=m.id, ip=h.ip).all()]} for h in hosts], 'web_targets':[{'id':w.id,'url':w.url,'ip':w.ip,'port':w.port,'scheme':w.scheme,'source':w.source} for w in db.query(WebTarget).filter_by(mission_id=m.id).all()], 'findings':[{'id':f.id,'host_id':f.host_id,'title':f.title,'severity':f.severity,'description':f.description,'source':f.source,'confidence':f.confidence,'template_id':f.template_id,'template_name':f.template_name,'matched_at':f.matched_at,'host':f.host,'ip':f.ip,'port':f.port,'scheme':f.scheme,'tags':f.tags,'references':f.references,'raw_json':f.raw_json,'evidence_path':f.evidence_path} for f in db.query(Finding).filter_by(mission_id=m.id).all()], 'next_actions':[{'id':a.id,'title':a.title,'description':a.description,'reason':a.reason,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'status':a.status,'command_template_id':a.command_template_id} for a in db.query(NextAction).filter_by(mission_id=m.id).all()]}


def _bh_command(mission_id:str)->dict:
    safe=''.join(c if c.isalnum() or c in '-_' else '_' for c in mission_id)[:80]
    cmd=f'SharpHound.exe -c Default --ZipFileName openadzero_{safe}_sharphound.zip'
    return {'command':cmd,'execution_mode':'manual','risk_level':3,'requires_domain_user_context':True,'notes':['Exécuter uniquement dans un environnement autorisé.','SharpHound doit être lancé dans un contexte utilisateur domaine.','Importer le ZIP généré dans OpenAD Zero.']}

def _ser_collection(c:BloodHoundCollection):
    return {'id':c.id,'mission_id':c.mission_id,'status':c.status,'source':c.source,'filename':c.filename,'stored_path':c.stored_path,'sha256':c.sha256,'size_bytes':c.size_bytes,'zip_valid':c.zip_valid,'zip_summary_json':c.zip_summary_json,'ingestion_enabled':c.ingestion_enabled,'ingestion_status':c.ingestion_status,'ingestion_job_id':c.ingestion_job_id,'ingestion_error':c.ingestion_error,'created_at':c.created_at,'uploaded_at':c.uploaded_at,'validated_at':c.validated_at,'ingested_at':c.ingested_at}

def _write_readme(base:Path,c:BloodHoundCollection,enabled:bool):
    (base/'README.txt').write_text(f'Mission ID: {c.mission_id}\nCollection ID: {c.id}\nFilename: {c.filename}\nSHA256: {c.sha256}\nUpload timestamp: {c.uploaded_at}\nValidation status: {c.zip_valid}\nIngestion status: {c.ingestion_status}\nBloodHound enabled: {enabled}\n')

@router.get('/{mission_id}/bloodhound/sharphound-command')
async def sharphound_command(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    data=_bh_command(mission_id)
    await publish(MissionEvent(type='bloodhound.command.generated',mission_id=mission_id,payload={'command':data['command']}))
    return data

@router.get('/{mission_id}/bloodhound/status')
def bloodhound_status(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return {'enabled':get_settings().bloodhound_enabled,'status':'disabled' if not get_settings().bloodhound_enabled else 'enabled','base_url':get_settings().bloodhound_base_url,'checked_at':datetime.utcnow(),'stats':empty_stats()}

@router.get('/{mission_id}/bloodhound/collections')
def list_bh_collections(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return [_ser_collection(c) for c in db.query(BloodHoundCollection).filter_by(mission_id=mission_id).order_by(BloodHoundCollection.created_at.desc()).all()]

@router.get('/{mission_id}/bloodhound/collections/{collection_id}')
def get_bh_collection(mission_id:str, collection_id:str, db:Session=Depends(get_db)):
    c=db.get(BloodHoundCollection, collection_id)
    if not c or c.mission_id!=mission_id: raise HTTPException(404,'Collection not found')
    return _ser_collection(c)

@router.post('/{mission_id}/bloodhound/upload')
async def upload_bh_zip(mission_id:str, file:UploadFile=File(...), db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    if not file.filename or not file.filename.lower().endswith('.zip'): raise HTTPException(400,'Only .zip files are accepted')
    c=BloodHoundCollection(mission_id=mission_id,status='created',source='upload',filename=file.filename,ingestion_enabled=get_settings().bloodhound_enabled); db.add(c); db.commit(); db.refresh(c)
    base=Path(get_settings().evidence_dir)/mission_id/'bloodhound'/c.id; base.mkdir(parents=True, exist_ok=True); dest=base/'original.zip'
    max_bytes=get_settings().bloodhound_max_upload_mb*1024*1024; size=0
    await publish(MissionEvent(type='bloodhound.upload.started',mission_id=mission_id,payload={'filename':file.filename}))
    with dest.open('wb') as out:
        while True:
            chunk=await file.read(1024*1024)
            if not chunk: break
            size+=len(chunk)
            if size>max_bytes: raise HTTPException(413,'ZIP upload too large')
            out.write(chunk)
    if size==0: raise HTTPException(400,'Empty ZIP file refused')
    c.stored_path=str(dest); c.size_bytes=size; c.uploaded_at=datetime.utcnow(); c.status='uploaded'; c.sha256=sha256_file(dest); (base/'sha256.txt').write_text(c.sha256+'\n')
    summary=inspect_sharphound_zip(dest); c.zip_summary_json=summary; c.zip_valid=summary['valid']; c.validated_at=datetime.utcnow(); c.status='validated' if c.zip_valid else 'invalid'; (base/'zip_summary.json').write_text(json.dumps(summary,indent=2))
    await publish(MissionEvent(type='bloodhound.zip.validated',mission_id=mission_id,payload={'collection_id':c.id,'valid':c.zip_valid,'json_files_count':summary['json_files_count'],'sha256':c.sha256}))
    result={'status':'not_attempted'}
    if c.zip_valid:
        try:
            mark_phase_completed(db, mission_id, 'active_directory_collection', 'BloodHound ZIP validated.'); create_timeline_event(db, mission_id, TimelineEventCreate(event_type='bloodhound.collection.validated', title='BloodHound collection uploaded and validated', source='bloodhound', severity='success', related_bloodhound_collection_id=c.id))
        except Exception: log.exception('operations bloodhound hook failed')
        await publish(MissionEvent(type='bloodhound.ingestion.started',mission_id=mission_id,payload={'collection_id':c.id,'provider':'bloodhound-ce'}))
        result=await ingest_collection(c)
        event='bloodhound.ingestion.completed' if c.ingestion_status=='ingested' or c.ingestion_status=='bloodhound_disabled' else 'bloodhound.ingestion.failed'
        await publish(MissionEvent(type=event,mission_id=mission_id,payload={'collection_id':c.id,'status':c.ingestion_status,'error':c.ingestion_error}))
        plan_after_bloodhound_upload(db, mission_id, c.zip_valid)
    (base/'ingestion_result.json').write_text(json.dumps(result,indent=2)); (base/'stats.json').write_text(json.dumps(empty_stats(),indent=2)); _write_readme(base,c,get_settings().bloodhound_enabled)
    db.add(c); db.commit(); db.refresh(c)
    return _ser_collection(c)

@router.post('/{mission_id}/bloodhound/collections/{collection_id}/ingest')
async def reingest_bh_collection(mission_id:str, collection_id:str, db:Session=Depends(get_db)):
    c=db.get(BloodHoundCollection, collection_id)
    if not c or c.mission_id!=mission_id: raise HTTPException(404,'Collection not found')
    if not c.zip_valid: raise HTTPException(400,'Collection ZIP is not valid')
    res=await ingest_collection(c); db.commit(); return {'collection':_ser_collection(c),'result':res}

@router.post('')
def create_mission(payload:MissionCreate, db:Session=Depends(get_db)):
    try: targets=validate_scope(payload.scope, get_settings().allow_public_scans).targets
    except ScopeValidationError as e: raise HTTPException(400, str(e))
    m=Mission(name=payload.name, scenario=payload.scenario, mode=payload.mode, status='scope_validated', raw_scope=payload.scope, validated_targets=targets); db.add(m); db.commit(); db.refresh(m)
    try: initialize_operations_for_mission(db, m.id)
    except Exception: log.exception('operations init failed')
    return {'mission_id':m.id,'status':m.status,'validated_targets':targets}

class ApproveActionPayload(BaseModel):
    approved: bool
    note: str | None = None
class IgnoreActionPayload(BaseModel):
    reason: str | None = None

@router.get('/{mission_id}/actions')
def list_actions(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return [{'id':a.id,'title':a.title,'description':a.description,'reason':a.reason,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'status':a.status,'command_template_id':a.command_template_id} for a in db.query(NextAction).filter_by(mission_id=mission_id).all()]

@router.post('/{mission_id}/actions/{action_id}/approve')
async def approve_action(mission_id:str, action_id:str, payload:ApproveActionPayload, db:Session=Depends(get_db)):
    if not payload.approved: raise HTTPException(400,'approved must be true')
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    a=db.get(NextAction, action_id)
    if not a or a.mission_id!=mission_id: raise HTTPException(404,'Action not found')
    if not a.requires_approval: raise HTTPException(400,'Action does not require approval')
    if a.risk_level>2: raise HTTPException(403,'Action préparée mais exécution automatique désactivée en V2.')
    if a.command_template_id in NETEXEC_TEMPLATES:
        j=Job(mission_id=mission_id,type=a.command_template_id,tool='netexec',status='pending',command_preview='nxc smb <nmap-smb-targets> <safe-template>')
        a.status='running'; db.add(j); db.commit(); db.refresh(j)
        enqueue_job(db, mission_id, j.id, j.type)
    elif a.command_template_id in NUCLEI_TEMPLATES:
        targets=ensure_web_targets_for_mission(db, mission_id)
        if not targets: raise HTTPException(400,'No web targets available')
        j=Job(mission_id=mission_id,type=a.command_template_id,tool='nuclei',status='pending',command_preview='nuclei -list <web-targets> -jsonl -o <evidence>/nuclei.jsonl <safe-options>')
        a.status='running'; db.add(j); db.commit(); db.refresh(j)
        enqueue_job(db, mission_id, j.id, j.type)
    else: raise HTTPException(403,'Action template not allowed')
    return {'mission_id':mission_id,'action_id':action_id,'status':'queued','job_id':j.id}

@router.post('/{mission_id}/actions/{action_id}/ignore')
def ignore_action(mission_id:str, action_id:str, payload:IgnoreActionPayload, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    a=db.get(NextAction, action_id)
    if not a or a.mission_id!=mission_id: raise HTTPException(404,'Action not found')
    a.status='ignored'; db.commit(); return {'mission_id':mission_id,'action_id':action_id,'status':'ignored'}

class ManualActionCreate(BaseModel):
    capability_id: str
    title: str
    description: str
    risk_level: int
    operator_note: str | None = ''
    evidence_reference: str | None = ''
class ManualActionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    risk_level: int | None = None
    status: str | None = None
    operator_note: str | None = None
    evidence_reference: str | None = None

def _ser_manual(c:ManualActionCard):
    return {'id':c.id,'mission_id':c.mission_id,'capability_id':c.capability_id,'title':c.title,'description':c.description,'risk_level':c.risk_level,'status':c.status,'operator_note':c.operator_note,'evidence_reference':c.evidence_reference,'created_at':c.created_at,'updated_at':c.updated_at}

def _validate_manual_payload(payload):
    cap=get_capability(payload.capability_id)
    if not cap: raise HTTPException(400,'Unknown capability')
    if not creates_manual_card_only(cap): raise HTTPException(400,'Capability does not allow manual action cards')
    blob=' '.join(str(getattr(payload,k,'')) for k in ('title','description','operator_note','evidence_reference')).lower()
    banned=['command','cmd.exe','powershell','mimikatz','lsass','dcsync','pass-the-hash','password spray','brute force']
    if any(x in blob for x in banned): raise HTTPException(400,'Manual action cards document outcomes only and cannot contain executable commands or sensitive instructions')
    return cap

@router.post('/{mission_id}/manual-actions')
def create_manual_action(mission_id:str, payload:ManualActionCreate, db:Session=Depends(get_db)):
    if not get_settings().openadzero_enable_manual_action_cards: raise HTTPException(403,'Manual action cards disabled')
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    cap=_validate_manual_payload(payload)
    card=ManualActionCard(mission_id=mission_id,capability_id=cap.id,title=payload.title,description=payload.description,risk_level=payload.risk_level,status='draft',operator_note=payload.operator_note,evidence_reference=payload.evidence_reference)
    db.add(card); db.commit(); db.refresh(card); return _ser_manual(card)

@router.get('/{mission_id}/manual-actions')
def list_manual_actions(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return [_ser_manual(c) for c in db.query(ManualActionCard).filter_by(mission_id=mission_id).order_by(ManualActionCard.created_at.desc()).all()]

@router.get('/{mission_id}/manual-actions/{manual_action_id}')
def get_manual_action(mission_id:str, manual_action_id:str, db:Session=Depends(get_db)):
    c=db.get(ManualActionCard, manual_action_id)
    if not c or c.mission_id!=mission_id: raise HTTPException(404,'Manual action card not found')
    return _ser_manual(c)

@router.patch('/{mission_id}/manual-actions/{manual_action_id}')
def update_manual_action(mission_id:str, manual_action_id:str, payload:ManualActionUpdate, db:Session=Depends(get_db)):
    c=db.get(ManualActionCard, manual_action_id)
    if not c or c.mission_id!=mission_id: raise HTTPException(404,'Manual action card not found')
    if payload.status and payload.status not in {'draft','documented','reviewed','rejected'}: raise HTTPException(400,'Invalid manual action status')
    if payload.capability_id if hasattr(payload,'capability_id') else False: raise HTTPException(400,'Capability cannot be changed')
    _validate_manual_payload(type('P',(),{'capability_id':c.capability_id,'title':payload.title or c.title,'description':payload.description or c.description,'operator_note':payload.operator_note or c.operator_note,'evidence_reference':payload.evidence_reference or c.evidence_reference})())
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(c,k,v)
    c.updated_at=datetime.utcnow(); db.commit(); db.refresh(c); return _ser_manual(c)

@router.post('/{mission_id}/start')
async def start_mission(mission_id:str, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id)
    if not m: raise HTTPException(404,'Mission not found')
    if m.status!='scope_validated': raise HTTPException(400,'Mission scope is not validated or mission already started')
    m.status='running'; m.started_at=datetime.utcnow()
    try:
        initialize_operations_for_mission(db, m.id); mark_phase_completed(db, m.id, 'scope_validation', 'Mission scope validated.'); update_phase_status(db, m.id, 'network_discovery', 'running', 'Nmap discovery started.'); create_timeline_event(db, m.id, TimelineEventCreate(event_type='nmap.started', title='Nmap discovery started', source='nmap', severity='info'))
    except Exception: log.exception('operations start hook failed')
    j=Job(mission_id=m.id,type='nmap_discovery',tool='nmap',status='pending',command_preview='nmap -Pn -sV --top-ports 1000 -oX <evidence-path> <validated-targets>'); db.add(j); db.commit(); db.refresh(j)
    await publish(MissionEvent(type='mission.status',mission_id=m.id,payload={'status':'running'}))
    enqueue_job(db, m.id, j.id, j.type)
    return {'mission_id':m.id,'status':'queued','job_id':j.id}
@router.get('/{mission_id}')
def get_mission(mission_id:str, db:Session=Depends(get_db)):
    m=db.get(Mission,mission_id)
    if not m: raise HTTPException(404,'Mission not found')
    return serialize_mission(db,m)
@router.get('')
def list_missions(db:Session=Depends(get_db)):
    return [{'id':m.id,'name':m.name,'status':m.status,'created_at':m.created_at,'validated_targets':m.validated_targets} for m in db.query(Mission).order_by(Mission.created_at.desc()).all()]

@router.get('/{mission_id}/web-targets')
def list_web_targets(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    ensure_web_targets_for_mission(db, mission_id)
    return [{'id':w.id,'url':w.url,'ip':w.ip,'port':w.port,'scheme':w.scheme,'source':w.source,'findings_count':db.query(Finding).filter_by(mission_id=mission_id, ip=w.ip, source='nuclei').count()} for w in db.query(WebTarget).filter_by(mission_id=mission_id).all()]

@router.get('/{mission_id}/findings')
def list_findings(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return [{'id':f.id,'title':f.title,'severity':f.severity,'description':f.description,'source':f.source,'template_id':f.template_id,'template_name':f.template_name,'matched_at':f.matched_at,'host':f.host,'ip':f.ip,'port':f.port,'tags':f.tags,'references':f.references,'raw_json':f.raw_json,'evidence_path':f.evidence_path} for f in db.query(Finding).filter_by(mission_id=mission_id).all()]

from typing import Optional
from app.integrations.bloodhound.explorer import BloodHoundExplorer
from app.integrations.bloodhound.query_catalog import QueryCatalog, QueryCatalogError
from app.integrations.bloodhound.errors import BloodHoundError

class PathfindingPayload(BaseModel):
    source_object_id: str
    target: str = 'Domain Admins'
    max_depth: int = 8

def _explorer(db:Session): return BloodHoundExplorer(db)
def _bh_exc(e:Exception):
    if isinstance(e, QueryCatalogError): raise HTTPException(400,str(e))
    if isinstance(e, BloodHoundError): raise HTTPException(503,str(e))
    raise e

@router.get('/{mission_id}/bloodhound/explorer/status')
async def bloodhound_explorer_status(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    data=await _explorer(db).status(mission_id)
    await publish(MissionEvent(type='bloodhound.explorer.ready',mission_id=mission_id,payload={'enabled':data['enabled'],'reachable':data['reachable'],'ingested':data['ingested']}))
    return data

@router.get('/{mission_id}/bloodhound/query-catalog')
def bloodhound_query_catalog(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return QueryCatalog().list_public()

@router.get('/{mission_id}/bloodhound/objects/search')
async def bloodhound_search_objects(mission_id:str, q:str, types:Optional[str]=None, limit:int=20, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    try: return await _explorer(db).search_objects(mission_id,q,min(limit,50),[x for x in (types or '').split(',') if x])
    except Exception as e: _bh_exc(e)

@router.get('/{mission_id}/bloodhound/objects/{object_id}')
async def bloodhound_object_detail(mission_id:str, object_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    try: return await _explorer(db).object_detail(mission_id,object_id)
    except Exception as e: _bh_exc(e)

@router.get('/{mission_id}/bloodhound/objects/{object_id}/relations')
async def bloodhound_object_relations(mission_id:str, object_id:str, direction:str='outbound', limit:int=100, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    if direction not in ('outbound','inbound'): raise HTTPException(400,'direction must be inbound or outbound')
    try: return await _explorer(db).relations(mission_id,object_id,direction,min(limit,200))
    except Exception as e: _bh_exc(e)

@router.get('/{mission_id}/bloodhound/objects/{object_id}/permissions')
async def bloodhound_object_permissions(mission_id:str, object_id:str, limit:int=100, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    try: return await _explorer(db).permissions(mission_id,object_id,min(limit,200))
    except Exception as e: _bh_exc(e)

@router.post('/{mission_id}/bloodhound/pathfinding')
async def bloodhound_pathfinding(mission_id:str, payload:PathfindingPayload, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    try:
        res=await _explorer(db).pathfinding(mission_id,payload.source_object_id,payload.target,min(payload.max_depth,12))
        if res:
            try:
                mark_phase_completed(db, mission_id, 'pathfinding', 'BloodHound pathfinding returned results.'); create_timeline_event(db, mission_id, TimelineEventCreate(event_type='bloodhound.path.detected', title='BloodHound pathfinding detected a path', source='bloodhound', severity='success'))
            except Exception: log.exception('operations pathfinding hook failed')
        return res
    except Exception as e: _bh_exc(e)

def _serialize_job(j: Job):
    return {'id':j.id,'mission_id':j.mission_id,'type':j.type,'tool':j.tool,'status':j.status,'command_preview':j.command_preview,'rq_job_id':j.rq_job_id,'queued_at':j.queued_at,'started_at':j.started_at,'completed_at':j.completed_at,'return_code':j.return_code,'attempts':j.attempts,'max_attempts':j.max_attempts,'error_message':j.error_message,'stdout_path':j.stdout_path,'stderr_path':j.stderr_path,'output_path':j.output_path}

@router.get('/{mission_id}/jobs')
def list_jobs(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    return [_serialize_job(j) for j in db.query(Job).filter_by(mission_id=mission_id).order_by(Job.queued_at.desc().nullslast(), Job.started_at.desc().nullslast()).all()]

@router.get('/{mission_id}/jobs/{job_id}')
def get_job(mission_id:str, job_id:str, db:Session=Depends(get_db)):
    j=db.get(Job, job_id)
    if not j or j.mission_id!=mission_id: raise HTTPException(404,'Job not found')
    return _serialize_job(j)

@router.get('/{mission_id}/jobs/{job_id}/logs')
def get_job_logs(mission_id:str, job_id:str, db:Session=Depends(get_db)):
    from app.db.models import JobLog
    j=db.get(Job, job_id)
    if not j or j.mission_id!=mission_id: raise HTTPException(404,'Job not found')
    return [{'id':l.id,'mission_id':l.mission_id,'job_id':l.job_id,'source':l.source,'stream':l.stream,'line':l.line,'created_at':l.created_at} for l in db.query(JobLog).filter_by(mission_id=mission_id, job_id=job_id).order_by(JobLog.created_at.asc()).all()]

@router.post('/{mission_id}/jobs/{job_id}/cancel')
async def cancel_job(mission_id:str, job_id:str, db:Session=Depends(get_db)):
    from app.events.persistent import publish_mission_event
    j=db.get(Job, job_id)
    if not j or j.mission_id!=mission_id: raise HTTPException(404,'Job not found')
    if j.status not in {'pending','queued','running'}: raise HTTPException(400,'Job cannot be cancelled')
    j.cancel_requested_at=datetime.utcnow()
    if j.status in {'pending','queued'}: j.status='cancelled'; j.completed_at=datetime.utcnow()
    else: j.status='cancel_requested'
    db.commit(); db.refresh(j)
    await publish_mission_event(db, mission_id, 'job.cancel_requested', {'job_id':j.id,'job_type':j.type,'tool':j.tool,'status':j.status}, source=j.tool)
    if j.status=='cancelled': await publish_mission_event(db, mission_id, 'job.cancelled', {'job_id':j.id,'job_type':j.type,'tool':j.tool,'status':j.status}, source=j.tool)
    return _serialize_job(j)

@router.post('/{mission_id}/jobs/{job_id}/retry')
async def retry_job(mission_id:str, job_id:str, db:Session=Depends(get_db)):
    from app.events.persistent import publish_mission_event
    j=db.get(Job, job_id)
    if not j or j.mission_id!=mission_id: raise HTTPException(404,'Job not found')
    if j.status not in {'failed','timeout'}: raise HTTPException(400,'Only failed or timeout jobs can be retried')
    if (j.attempts or 0) >= (j.max_attempts or 1): raise HTTPException(400,'Maximum retry attempts reached')
    j.status='pending'; j.completed_at=None; j.started_at=None; j.cancel_requested_at=None; j.error_message=None; db.commit(); db.refresh(j)
    rqid=enqueue_job(db, mission_id, j.id, j.type)
    await publish_mission_event(db, mission_id, 'job.retried', {'job_id':j.id,'job_type':j.type,'tool':j.tool,'status':j.status,'rq_job_id':rqid}, source=j.tool)
    return _serialize_job(j)
