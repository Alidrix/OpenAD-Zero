from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.paths import EvidencePathError
from app.db.session import get_db
from app.db.models import Mission, Report
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.reports.schemas import ReportGenerateRequest, ReportResponse, ReportPreviewResponse
from app.reports.service import generate_report, get_latest_report, get_report_file
import logging
from app.operations.phases import mark_phase_completed
from app.operations.schemas import TimelineEventCreate
from app.operations.timeline import create_timeline_event
log=logging.getLogger(__name__)

router=APIRouter(prefix='/missions')
MAX_PREVIEW=500000

def _ser(r:Report):
    return {'id':r.id,'mission_id':r.mission_id,'status':r.status,'title':r.title,'markdown_path':r.markdown_path,'html_path':r.html_path,'metadata_path':r.metadata_path,'sections_json':r.sections_json,'generated_at':r.generated_at}

@router.post('/{mission_id}/report/generate', response_model=ReportResponse)
async def generate(mission_id:str, payload:ReportGenerateRequest|None=None, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    try:
        r=generate_report(db, mission_id, payload.include_sections if payload else None)
        try:
            mark_phase_completed(db, mission_id, 'reporting', 'Report generated.'); create_timeline_event(db, mission_id, TimelineEventCreate(event_type='report.generated', title='Report generated', source='report', severity='success', related_report_id=r.id))
        except Exception: log.exception('operations report hook failed')
        await publish(MissionEvent(type='report.generated',mission_id=mission_id,payload={'report_id':r.id,'markdown_path':r.markdown_path,'html_path':r.html_path}))
        return _ser(r)
    except EvidencePathError as e:
        await publish(MissionEvent(type='report.failed',mission_id=mission_id,payload={'error':str(e)}))
        raise HTTPException(500, 'Evidence directory is not writable. Set EVIDENCE_DIR to a writable path.') from e
    except Exception as e:
        await publish(MissionEvent(type='report.failed',mission_id=mission_id,payload={'error':str(e)}))
        raise

@router.get('/{mission_id}/report')
def latest(mission_id:str, db:Session=Depends(get_db)):
    if not db.get(Mission, mission_id): raise HTTPException(404,'Mission not found')
    r=get_latest_report(db, mission_id)
    return {'report': _ser(r) if r else None}

@router.get('/{mission_id}/report/preview', response_model=ReportPreviewResponse)
def preview(mission_id:str, format:str=Query('markdown', pattern='^(markdown|html)$'), db:Session=Depends(get_db)):
    r=get_latest_report(db, mission_id)
    if not r: raise HTTPException(404,'No report generated yet')
    p=get_report_file(r, format); content=p.read_text(encoding='utf-8')
    truncated=len(content)>MAX_PREVIEW
    return {'format':format,'content':content[:MAX_PREVIEW] if truncated else content,'truncated':truncated}

@router.get('/{mission_id}/report/download')
def download(mission_id:str, format:str=Query('markdown', pattern='^(markdown|html)$'), db:Session=Depends(get_db)):
    r=get_latest_report(db, mission_id)
    if not r: raise HTTPException(404,'No report generated yet')
    p=get_report_file(r, format); ext='md' if format=='markdown' else 'html'
    return FileResponse(p, filename=f'openadzero_{mission_id}_report.{ext}', media_type='text/markdown' if ext=='md' else 'text/html')
