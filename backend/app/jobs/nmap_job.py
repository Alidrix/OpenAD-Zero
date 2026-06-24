from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import Job, Mission, Host, Service
from app.events.schemas import MissionEvent
from app.events.publisher import publish
from app.jobs.runner import run_command
from app.parsers.nmap_xml import parse_nmap_xml
from app.planner.next_actions import plan_for_mission
from app.integrations.nuclei.targets import ensure_web_targets_for_mission
from app.storage.evidence import job_dir
from app.core.config import get_settings

async def run_nmap_job(mission_id:str, job_id:str):
    db:Session=SessionLocal(); settings=get_settings()
    job=db.get(Job,job_id); mission=db.get(Mission,mission_id)
    try:
        job.status='running'; job.started_at=datetime.utcnow(); db.commit()
        await publish(MissionEvent(type='job.status',mission_id=mission_id,payload={'job_id':job_id,'status':'running'}))
        jd=job_dir(mission_id,job_id); xml=jd/'nmap.xml'; out=jd/'stdout.log'; err=jd/'stderr.log'
        args=['-Pn','-sV','--top-ports','1000','-oX',str(xml),*mission.validated_targets]
        job.command_preview='nmap '+' '.join(args); job.stdout_path=str(out); job.stderr_path=str(err); job.output_path=str(xml); db.commit()
        await publish(MissionEvent(type='job.log',mission_id=mission_id,payload={'job_id':job_id,'line':'[nmap] Starting safe discovery scan'}))
        res=await run_command('nmap',args,jd,out,err,mission_id,job_id,settings.nmap_timeout_seconds)
        job.return_code=res.return_code; job.completed_at=datetime.utcnow()
        if res.timed_out: job.status='timeout'; mission.status='failed'
        elif res.return_code!=0: job.status='failed'; mission.status='failed'
        else:
            job.status='completed'
            parsed=parse_nmap_xml(xml)
            for h in parsed['hosts']:
                host=Host(mission_id=mission_id, ip=h['ip'], hostname=h.get('hostname') or None, status=h.get('status','unknown')); db.add(host); db.flush()
                await publish(MissionEvent(type='host.discovered',mission_id=mission_id,payload={'ip':host.ip,'hostname':host.hostname,'is_domain_controller_candidate':False}))
                for s in h['services']:
                    svc=Service(mission_id=mission_id, host_id=host.id, **s); db.add(svc)
                    await publish(MissionEvent(type='service.discovered',mission_id=mission_id,payload={'host_ip':host.ip,**s}))
            db.commit()
            web_targets=ensure_web_targets_for_mission(db, mission_id)
            for w in web_targets:
                await publish(MissionEvent(type='web.target.discovered',mission_id=mission_id,payload={'url':w.url,'ip':w.ip,'port':w.port,'scheme':w.scheme,'source':w.source}))
            findings, actions=plan_for_mission(db, mission_id)
            for f in findings:
                host=db.get(Host,f.host_id) if f.host_id else None
                await publish(MissionEvent(type='finding.created',mission_id=mission_id,payload={'title':f.title,'severity':f.severity,'host_ip':host.ip if host else None,'source':f.source}))
            for a in actions:
                await publish(MissionEvent(type='planner.next_action',mission_id=mission_id,payload={'title':a.title,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'command_template_id':a.command_template_id}))
            mission.status='completed'; mission.completed_at=datetime.utcnow()
            try:
                from app.operations.service import safe_sync
                safe_sync(db, mission_id)
            except Exception: pass
        db.commit()
        await publish(MissionEvent(type='job.status',mission_id=mission_id,payload={'job_id':job_id,'status':job.status}))
        await publish(MissionEvent(type='mission.status',mission_id=mission_id,payload={'status':mission.status}))
    except Exception as e:
        if job: job.status='failed'; job.completed_at=datetime.utcnow()
        if mission: mission.status='failed'; mission.completed_at=datetime.utcnow()
        db.commit(); await publish(MissionEvent(type='job.log',mission_id=mission_id,payload={'job_id':job_id,'line':f'[error] {e}'}))
    finally: db.close()
