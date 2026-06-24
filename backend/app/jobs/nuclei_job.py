from __future__ import annotations
import asyncio,json,shutil,os
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.db.models import Job, Mission, NextAction, Host, Finding, WebTarget
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.integrations.nuclei.targets import ensure_web_targets_for_mission, build_web_targets_for_mission
from app.jobs.nuclei_policy import validate_nuclei_command
from app.parsers.nuclei_jsonl import parse_nuclei_jsonl
from app.planner.next_actions import plan_after_nuclei
from app.storage.evidence import job_dir

ALLOWED_TEMPLATES={'nuclei_web_exposure_scan'}

def build_nuclei_command(targets_file:Path, jsonl_output:Path, templates_dir:Path, rate_limit:int, concurrency:int, timeout:int)->list[str]:
    return ['nuclei','-list',str(targets_file),'-jsonl','-o',str(jsonl_output),'-severity','info,low,medium,high,critical','-templates',str(templates_dir),'-rl',str(rate_limit),'-c',str(concurrency),'-timeout',str(timeout),'-retries','1','-no-color']

async def run_nuclei_job(mission_id:str, job_id:str, action_id:str):
    db:Session=SessionLocal(); settings=get_settings(); job=db.get(Job,job_id); action=db.get(NextAction,action_id); mission=db.get(Mission,mission_id)
    try:
        job.status='running'; job.started_at=datetime.utcnow(); db.commit()
        targets=ensure_web_targets_for_mission(db, mission_id)
        jd=job_dir(mission_id,job_id); stdout=jd/'stdout.log'; stderr=jd/'stderr.log'; jsonl=jd/'nuclei.jsonl'; parsed_path=jd/'parsed.json'; findings_path=jd/'findings.json'; targets_file=jd/'targets.txt'
        if not targets:
            msg='Aucune cible HTTP/HTTPS détectée par Nmap. Action Nuclei annulée proprement.'
            stdout.write_text(msg+'\n'); job.status='blocked'; action.status='blocked'; db.commit(); await publish(MissionEvent(type='nuclei.log',mission_id=mission_id,payload={'job_id':job_id,'line':msg})); return
        targets_file.write_text('\n'.join(w.url for w in targets)+'\n')
        await publish(MissionEvent(type='nuclei.started',mission_id=mission_id,payload={'job_id':job_id,'action_id':action_id,'targets_count':len(targets)}))
        templates=Path(os.getenv('NUCLEI_TEMPLATES_DIR','/app/nuclei-templates-safe'))
        if not templates.exists(): templates=Path(__file__).resolve().parents[3]/'nuclei-templates-safe'
        cmd=build_nuclei_command(targets_file,jsonl,templates,settings.nuclei_rate_limit,settings.nuclei_concurrency,settings.nuclei_timeout)
        validate_nuclei_command(cmd, targets_file, jsonl, jd); (jd/'command.txt').write_text(' '.join(cmd)+'\n')
        job.command_preview=' '.join(cmd); job.stdout_path=str(stdout); job.stderr_path=str(stderr); job.output_path=str(jsonl); db.commit()
        if shutil.which('nuclei') is None: raise RuntimeError('Nuclei indisponible dans l’environnement backend.')
        await publish(MissionEvent(type='nuclei.log',mission_id=mission_id,payload={'job_id':job_id,'line':f'[nuclei] Starting scan on {len(targets)} targets'}))
        proc=await asyncio.create_subprocess_exec(*cmd,cwd=str(jd),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        async def pump(stream,path):
            with path.open('w') as f:
                while True:
                    line=await stream.readline()
                    if not line: break
                    text=line.decode(errors='replace').rstrip(); f.write(text+'\n'); f.flush(); await publish(MissionEvent(type='nuclei.log',mission_id=mission_id,payload={'job_id':job_id,'line':f'[nuclei] {text}'}))
        await asyncio.wait_for(asyncio.gather(pump(proc.stdout,stdout),pump(proc.stderr,stderr),proc.wait()), timeout=settings.nuclei_job_timeout_seconds)
        job.return_code=proc.returncode; job.completed_at=datetime.utcnow(); job.status='completed' if proc.returncode==0 else 'failed'; action.status=job.status
        parsed=parse_nuclei_jsonl(jsonl); parsed_path.write_text(json.dumps([p.to_dict() for p in parsed],indent=2))
        created=[]
        for p in parsed:
            wt=db.query(WebTarget).filter_by(mission_id=mission_id,url=p.host or '').first() or (db.query(WebTarget).filter_by(mission_id=mission_id,ip=p.ip).first() if p.ip else None)
            host=db.query(Host).filter_by(mission_id=mission_id, ip=p.ip).first() if p.ip else None
            f=Finding(mission_id=mission_id,host_id=host.id if host else (wt.host_id if wt else None),title=p.template_name,severity=p.severity,description=p.description or p.template_name,source='nuclei',confidence='medium',template_id=p.template_id,template_name=p.template_name,matcher_name=p.matcher_name,matched_at=p.matched_at,host=p.host,ip=p.ip,port=p.port,scheme=(wt.scheme if wt else None),tags=p.tags,references=p.references,raw_json=p.raw_json,raw_event_path=str(jsonl),evidence_path=str(jd))
            db.add(f); created.append(f); await publish(MissionEvent(type='nuclei.finding.created',mission_id=mission_id,payload={'template_id':p.template_id,'template_name':p.template_name,'severity':p.severity,'matched_at':p.matched_at,'host':p.host}))
        db.commit(); findings_path.write_text(json.dumps([{'title':f.title,'severity':f.severity,'source':f.source} for f in created],indent=2))
        _, actions=plan_after_nuclei(db,mission_id,created)
        for a in actions: await publish(MissionEvent(type='planner.next_action',mission_id=mission_id,payload={'id':a.id,'title':a.title,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'command_template_id':a.command_template_id,'status':a.status}))
        try:
            from app.operations.service import safe_sync
            safe_sync(db, mission_id)
        except Exception: pass
        db.commit()
    except Exception as e:
        if job: job.status='failed'; job.completed_at=datetime.utcnow()
        if action: action.status='failed'
        db.commit(); await publish(MissionEvent(type='nuclei.log',mission_id=mission_id,payload={'job_id':job_id,'line':f'[nuclei] {e}'}))
    finally: db.close()
