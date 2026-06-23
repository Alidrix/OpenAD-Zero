import json
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import ensure_netexec_template_allowed, validate_netexec_command, CommandPolicyError
from app.db.session import SessionLocal
from app.db.models import Job, Mission, Host, Service, SMBFact, SMBShare, Finding, NextAction
from app.events.publisher import publish
from app.events.schemas import MissionEvent
from app.jobs.runner import run_command
from app.parsers.netexec_smb import parse_netexec_smb_output
from app.planner.next_actions import plan_after_netexec
from app.storage.evidence import job_dir

NETEXEC_TYPES = {'netexec_smb_fingerprint','netexec_smb_signing_check','netexec_smb_null_session_check','netexec_smb_null_session_shares'}

def _smb_targets(db: Session, mission_id: str) -> list[str]:
    rows=db.query(Host).join(Service, Host.id==Service.host_id).filter(Host.mission_id==mission_id, Service.port==445, Service.state=='open').all()
    return sorted({h.ip for h in rows})

def build_netexec_command(template_id: str, targets: list[str], jd) -> tuple[list[str], dict[str,str]]:
    ensure_netexec_template_allowed(template_id)
    log_path=jd/'netexec.log'; files={'log_path': str(log_path)}
    if template_id=='netexec_smb_fingerprint':
        args=['smb',*targets,'--log',str(log_path)]
    elif template_id=='netexec_smb_signing_check':
        relay=jd/'smb_signing_not_required.txt'; files['relay_list_path']=str(relay); args=['smb',*targets,'--gen-relay-list',str(relay),'--log',str(log_path)]
    elif template_id=='netexec_smb_null_session_check':
        args=['smb',*targets,'-u','','-p','','--log',str(log_path)]
    elif template_id=='netexec_smb_null_session_shares':
        args=['smb',*targets,'-u','','-p','','--shares','--log',str(log_path)]
    else:
        raise CommandPolicyError(f'Unsupported NetExec template: {template_id}')
    validate_netexec_command(['nxc',*args])
    return args, files

async def run_netexec_job(mission_id: str, job_id: str, action_id: str):
    db:Session=SessionLocal(); settings=get_settings(); job=db.get(Job, job_id); mission=db.get(Mission, mission_id); action=db.get(NextAction, action_id)
    jd=job_dir(mission_id, job_id); stdout=jd/'stdout.log'; stderr=jd/'stderr.log'; parsed_path=jd/'parsed.json'; findings_path=jd/'findings.json'; command_path=jd/'command.txt'
    try:
        targets=_smb_targets(db, mission_id)
        if not targets:
            msg='Aucun hôte SMB détecté par Nmap. Action NetExec annulée proprement.'
            job.status='cancelled'; action.status='blocked'; db.commit()
            await publish(MissionEvent(type='netexec.log', mission_id=mission_id, payload={'job_id':job_id,'line':f'[netexec] {msg}'})); return
        args, files=build_netexec_command(job.type, targets, jd)
        command=['nxc',*args]; command_path.write_text(' '.join(command))
        job.command_preview=' '.join(command); job.stdout_path=str(stdout); job.stderr_path=str(stderr); job.output_path=str(parsed_path); job.status='running'; job.started_at=datetime.utcnow(); action.status='running'; db.commit()
        await publish(MissionEvent(type='netexec.started', mission_id=mission_id, payload={'job_id':job_id,'action_id':action_id,'profile':job.type}))
        result=await run_command('nxc', args, jd, stdout, stderr, mission_id, job_id, settings.nmap_timeout_seconds, 'netexec.log', 'netexec')
        text=''
        for p in [stdout, stderr, jd/'netexec.log']:
            if p.exists(): text += '\n' + p.read_text(errors='replace')
        parsed=parse_netexec_smb_output(text); parsed_path.write_text(json.dumps(parsed, indent=2))
        facts=[]; shares=[]
        for item in parsed['facts']:
            host=db.query(Host).filter_by(mission_id=mission_id, ip=item['ip']).first()
            fact=SMBFact(mission_id=mission_id, host_id=host.id if host else None, source='netexec', **item); db.add(fact); facts.append(fact)
            if host and item.get('hostname') and not host.hostname: host.hostname=item['hostname']
            await publish(MissionEvent(type='smb.fact.discovered', mission_id=mission_id, payload={k:item.get(k) for k in ['ip','hostname','domain','os','smb_signing_required','smbv1_enabled','null_session_possible']}))
        for item in parsed['shares']:
            host=db.query(Host).filter_by(mission_id=mission_id, ip=item['ip']).first()
            share=SMBShare(mission_id=mission_id, host_id=host.id if host else None, source='netexec', **item); db.add(share); shares.append(share)
            await publish(MissionEvent(type='smb.share.discovered', mission_id=mission_id, payload=item))
        job.return_code=result.return_code; job.completed_at=datetime.utcnow()
        job.status='timeout' if result.timed_out else ('completed' if result.return_code==0 else 'failed')
        action.status='completed' if job.status=='completed' else 'failed'
        db.commit()
        findings, actions=plan_after_netexec(db, mission_id)
        findings_path.write_text(json.dumps([{'title':f.title,'severity':f.severity,'source':f.source,'confidence':f.confidence} for f in findings], indent=2))
        for f in findings:
            host=db.get(Host,f.host_id) if f.host_id else None
            await publish(MissionEvent(type='finding.created', mission_id=mission_id, payload={'title':f.title,'severity':f.severity,'host_ip':host.ip if host else None,'source':f.source,'confidence':f.confidence}))
        for a in actions:
            await publish(MissionEvent(type='planner.next_action', mission_id=mission_id, payload={'id':a.id,'title':a.title,'risk_level':a.risk_level,'requires_approval':a.requires_approval,'command_template_id':a.command_template_id,'status':a.status,'reason':a.reason}))
    except Exception as e:
        if job: job.status='failed'; job.completed_at=datetime.utcnow()
        if action: action.status='failed'
        db.commit(); await publish(MissionEvent(type='netexec.log', mission_id=mission_id, payload={'job_id':job_id,'line':f'[netexec] {e}'}))
    finally:
        db.close()
