from datetime import datetime
from pathlib import Path
import mimetypes, shutil
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.db.models import Mission, Evidence, EvidenceLink
from app.evidence.storage import safe_extension, sanitize_filename, compute_sha256, write_metadata, EvidenceStorageError
from app.evidence.preview import can_preview, build_preview
from app.evidence.schemas import EvidenceLinkCreate
from app.events.publisher import publish
from app.events.schemas import MissionEvent
import logging
from app.operations.phases import update_phase_status
from app.operations.schemas import TimelineEventCreate
from app.operations.timeline import create_timeline_event
log=logging.getLogger(__name__)

router=APIRouter(prefix='/missions')
TARGET_TYPES={'mission','host','service','job','finding','next_action','bloodhound_collection'}

def _allowed(): return {e.strip() for e in get_settings().external_evidence_allowed_extensions.split(',') if e.strip()}
def _ser(e:Evidence): return {k:getattr(e,k) for k in ('id','mission_id','label','category','description','filename','stored_path','sha256','size_bytes','mime_type','source','preview_available','metadata_json','created_at')}
def _get(mission_id,evidence_id,db):
    e=db.get(Evidence,evidence_id)
    if not e or e.mission_id!=mission_id: raise HTTPException(404,'Evidence not found')
    return e

@router.post('/{mission_id}/evidence/import')
async def import_evidence(mission_id:str, file:UploadFile=File(...), label:str=Form(...), category:str=Form('external'), description:str|None=Form(None), db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    if not get_settings().openadzero_enable_external_evidence_import: raise HTTPException(403,'External evidence import disabled')
    try:
        original=sanitize_filename(file.filename or ''); ext=safe_extension(original,_allowed())
    except EvidenceStorageError as exc: raise HTTPException(400,str(exc))
    e=Evidence(mission_id=mission_id,label=label[:255],category=(category or 'external')[:100],description=description,filename=original,stored_path='',sha256='',size_bytes=0,mime_type=file.content_type or mimetypes.guess_type(original)[0],source='external_upload',preview_available=False,metadata_json={})
    db.add(e); db.commit(); db.refresh(e)
    base=Path(get_settings().evidence_dir)/mission_id/'external'/e.id; base.mkdir(parents=True, exist_ok=True); dest=base/f'original{ext}'
    max_bytes=get_settings().external_evidence_max_upload_mb*1024*1024; size=0
    with dest.open('wb') as out:
        while True:
            chunk=await file.read(1024*1024)
            if not chunk: break
            size+=len(chunk)
            if size>max_bytes:
                db.delete(e); db.commit(); shutil.rmtree(base, ignore_errors=True); raise HTTPException(413,'Evidence upload too large')
            out.write(chunk)
    if size==0:
        db.delete(e); db.commit(); shutil.rmtree(base, ignore_errors=True); raise HTTPException(400,'Empty file refused')
    e.stored_path=str(dest); e.size_bytes=size; e.sha256=compute_sha256(dest); e.preview_available=can_preview(e)
    metadata={'evidence_id':e.id,'mission_id':mission_id,'original_filename':original,'stored_filename':dest.name,'label':e.label,'category':e.category,'description':description,'sha256':e.sha256,'size_bytes':size,'mime_type':e.mime_type,'source':e.source,'created_at':datetime.utcnow().isoformat()+'Z'}
    e.metadata_json=metadata; write_metadata(base,metadata); (base/'sha256.txt').write_text(e.sha256+'\n'); (base/'README.txt').write_text('OpenAD Zero external evidence. Uploaded evidence is stored for documentation only and is never executed.\n')
    db.commit(); db.refresh(e)
    try:
        update_phase_status(db, mission_id, 'evidence_consolidation', 'completed', 'Evidence imported.'); create_timeline_event(db, mission_id, TimelineEventCreate(event_type='evidence.imported', title='Evidence imported', source='evidence', severity='success', related_evidence_id=e.id))
    except Exception: log.exception('operations evidence hook failed')
    await publish(MissionEvent(type='evidence.created',mission_id=mission_id,payload={'evidence_id':e.id,'label':e.label,'category':e.category,'sha256':e.sha256,'size_bytes':e.size_bytes}))
    return _ser(e)

@router.get('/{mission_id}/evidence')
def list_evidence(mission_id:str, category:str|None=None, q:str|None=None, source:str|None=None, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    qry=db.query(Evidence).filter_by(mission_id=mission_id)
    if category: qry=qry.filter(Evidence.category==category)
    if source: qry=qry.filter(Evidence.source==source)
    if q: qry=qry.filter(Evidence.label.ilike(f'%{q}%') | Evidence.filename.ilike(f'%{q}%'))
    return [_ser(e) for e in qry.order_by(Evidence.created_at.desc()).all()]

@router.get('/{mission_id}/evidence/{evidence_id}')
def get_evidence(mission_id:str,evidence_id:str,db:Session=Depends(get_db)): return _ser(_get(mission_id,evidence_id,db))
@router.get('/{mission_id}/evidence/{evidence_id}/preview')
def preview(mission_id:str,evidence_id:str,db:Session=Depends(get_db)): return build_preview(_get(mission_id,evidence_id,db), get_settings().external_evidence_preview_max_bytes)
@router.get('/{mission_id}/evidence/{evidence_id}/download')
def download(mission_id:str,evidence_id:str,db:Session=Depends(get_db)):
    e=_get(mission_id,evidence_id,db); return FileResponse(e.stored_path, filename=e.filename, media_type=e.mime_type or 'application/octet-stream')
@router.delete('/{mission_id}/evidence/{evidence_id}')
async def delete_evidence(mission_id:str,evidence_id:str,db:Session=Depends(get_db)):
    e=_get(mission_id,evidence_id,db); db.query(EvidenceLink).filter_by(mission_id=mission_id,evidence_id=evidence_id).delete(); db.delete(e); db.commit(); await publish(MissionEvent(type='evidence.deleted',mission_id=mission_id,payload={'evidence_id':evidence_id})); return {'deleted':True}
@router.post('/{mission_id}/evidence/{evidence_id}/links')
async def create_link(mission_id:str,evidence_id:str,payload:EvidenceLinkCreate,db:Session=Depends(get_db)):
    _get(mission_id,evidence_id,db)
    if payload.target_type not in TARGET_TYPES: raise HTTPException(400,'Invalid target_type')
    l=EvidenceLink(mission_id=mission_id,evidence_id=evidence_id,target_type=payload.target_type,target_id=payload.target_id); db.add(l); db.commit(); db.refresh(l); await publish(MissionEvent(type='evidence.linked',mission_id=mission_id,payload={'evidence_id':evidence_id,'target_type':l.target_type,'target_id':l.target_id})); return l
@router.get('/{mission_id}/evidence/{evidence_id}/links')
def list_links(mission_id:str,evidence_id:str,db:Session=Depends(get_db)):
    _get(mission_id,evidence_id,db); return db.query(EvidenceLink).filter_by(mission_id=mission_id,evidence_id=evidence_id).order_by(EvidenceLink.created_at.desc()).all()
@router.delete('/{mission_id}/evidence/{evidence_id}/links/{link_id}')
def delete_link(mission_id:str,evidence_id:str,link_id:str,db:Session=Depends(get_db)):
    _get(mission_id,evidence_id,db); l=db.get(EvidenceLink,link_id)
    if not l or l.mission_id!=mission_id or l.evidence_id!=evidence_id: raise HTTPException(404,'Evidence link not found')
    db.delete(l); db.commit(); return {'deleted':True}
