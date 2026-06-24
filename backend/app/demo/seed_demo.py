from __future__ import annotations
import hashlib, json
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import Mission, Host, Service, Finding, SMBFact, WebTarget, BloodHoundCollection, Evidence, EvidenceLink, MissionTimelineEvent, BloodHoundStat
from app.operations.service import initialize_operations_for_mission, sync_operations_from_current_data
from app.operations.phases import update_phase_status, mark_phase_completed
from app.reports.service import generate_report

DEMO_NAME='Demo Windows AD Lab'; DEMO_SCOPE='192.168.56.0/24'
FIXTURES=Path(__file__).with_name('fixtures')

def _sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def _evidence(db, mission_id, label, filename, content, category='demo'):
    existing=db.query(Evidence).filter_by(mission_id=mission_id,label=label).first()
    if existing: return existing
    data=content.encode(); base=Path(get_settings().evidence_dir)/mission_id/'demo'; base.mkdir(parents=True, exist_ok=True); path=base/filename; path.write_bytes(data)
    e=Evidence(mission_id=mission_id,label=label,category=category,description='Demo seed evidence fixture.',filename=filename,stored_path=str(path),sha256=_sha(data),size_bytes=len(data),mime_type='application/json' if filename.endswith('.json') else 'text/plain',source='demo_seed',preview_available=True,metadata_json={'demo':True})
    db.add(e); db.commit(); db.refresh(e); return e

def seed_demo(db:Session)->dict:
    m=db.query(Mission).filter_by(name=DEMO_NAME).first()
    created=False
    if not m:
        m=Mission(name=DEMO_NAME,scenario='windows_ad_internal',mode='safe',status='demo_seeded',raw_scope=DEMO_SCOPE,validated_targets=[DEMO_SCOPE],started_at=datetime.utcnow())
        db.add(m); db.commit(); db.refresh(m); created=True
        initialize_operations_for_mission(db,m.id)
    host_specs=[('192.168.56.10','DC01',True,[53,88,389,445]),('192.168.56.20','WS01',False,[445,3389]),('192.168.56.30','WEB01',False,[80,443])]
    hosts={h.ip:h for h in db.query(Host).filter_by(mission_id=m.id).all()}
    for ip,name,dc,ports in host_specs:
        h=hosts.get(ip) or Host(mission_id=m.id,ip=ip,hostname=name,status='up',os_guess='Windows',is_domain_controller_candidate=dc)
        db.add(h); db.commit(); db.refresh(h); hosts[ip]=h
        existing={(s.port,s.protocol) for s in db.query(Service).filter_by(mission_id=m.id,host_id=h.id).all()}
        for p in ports:
            if (p,'tcp') not in existing: db.add(Service(mission_id=m.id,host_id=h.id,port=p,protocol='tcp',name={53:'domain',88:'kerberos',389:'ldap',445:'microsoft-ds',3389:'rdp',80:'http',443:'https'}[p],product='Demo fixture',version='',state='open'))
    db.commit()
    facts=[('192.168.56.10','DC01','LAB.LOCAL',True),('192.168.56.20','WS01','LAB.LOCAL',False)]
    for ip,hn,dom,sign in facts:
        if not db.query(SMBFact).filter_by(mission_id=m.id,ip=ip,hostname=hn).first(): db.add(SMBFact(mission_id=m.id,host_id=hosts[ip].id,ip=ip,hostname=hn,domain=dom,os='Windows',smb_signing_required=sign,smbv1_enabled=False,null_session_possible=False,raw_line='demo seed'))
    for url,port,scheme in [('http://192.168.56.30',80,'http'),('https://192.168.56.30',443,'https')]:
        if not db.query(WebTarget).filter_by(mission_id=m.id,url=url).first(): db.add(WebTarget(mission_id=m.id,host_id=hosts['192.168.56.30'].id,url=url,ip='192.168.56.30',port=port,scheme=scheme,source='demo_seed'))
    finding_specs=[('Domain Controller candidate detected','info','nmap','192.168.56.10'),('SMB signing not required','medium','netexec','192.168.56.20'),('RDP exposed on internal host','low','nmap','192.168.56.20'),('Example Nuclei web exposure','medium','nuclei','192.168.56.30'),('Potential path to Domain Admins detected','high','bloodhound','192.168.56.10')]
    findings=[]
    for title,severity,source,ip in finding_specs:
        f=db.query(Finding).filter_by(mission_id=m.id,title=title).first()
        if not f:
            f=Finding(mission_id=m.id,host_id=hosts[ip].id,title=title,severity=severity,description=f'Demo fixture: {title}',source=source,confidence='medium',host=hosts[ip].hostname,ip=ip,port=None,tags=['demo'],references=[],raw_json={'demo':True},evidence_path='demo')
            db.add(f); db.commit(); db.refresh(f)
        findings.append(f)
    if not db.query(BloodHoundCollection).filter_by(mission_id=m.id,filename='demo_sharphound.zip').first():
        db.add(BloodHoundCollection(mission_id=m.id,status='validated',source='demo_seed',filename='demo_sharphound.zip',stored_path='demo',sha256='0'*64,size_bytes=4096,zip_valid=True,zip_summary_json=json.loads((FIXTURES/'sample_bloodhound_zip_summary.json').read_text()),ingestion_enabled=False,ingestion_status='ingested',uploaded_at=datetime.utcnow(),validated_at=datetime.utcnow(),ingested_at=datetime.utcnow()))
        db.add(BloodHoundStat(mission_id=m.id,domain_name='LAB.LOCAL',users_count=12,computers_count=3,groups_count=8,domains_count=1,edges_count=5,raw_stats_json={'demo':True}))
    ev1=_evidence(db,m.id,'Demo NetExec log','demo-netexec.log',(FIXTURES/'sample_netexec.log').read_text(),'network_log')
    ev2=_evidence(db,m.id,'Demo BloodHound summary','demo-bloodhound-summary.json',(FIXTURES/'sample_bloodhound_zip_summary.json').read_text(),'bloodhound')
    if findings and not db.query(EvidenceLink).filter_by(mission_id=m.id,evidence_id=ev1.id,target_type='finding',target_id=findings[1].id).first(): db.add(EvidenceLink(mission_id=m.id,evidence_id=ev1.id,target_type='finding',target_id=findings[1].id))
    if not db.query(MissionTimelineEvent).filter_by(mission_id=m.id,event_type='demo.seeded').first(): db.add(MissionTimelineEvent(mission_id=m.id,event_type='demo.seeded',title='Demo mission seeded',description='Reproducible QA scenario loaded.',source='demo',severity='success',metadata_json={'demo':True}))
    db.commit()
    for key in ['scope_validation','network_discovery','service_enumeration','active_directory_collection','evidence_consolidation']:
        try: mark_phase_completed(db,m.id,key,'Completed by demo seed.')
        except Exception: pass
    try: update_phase_status(db,m.id,'reporting','running','Demo report generated.')
    except Exception: pass
    if not db.query(EvidenceLink).filter_by(mission_id=m.id).first(): db.commit()
    if not db.query(__import__('app.db.models',fromlist=['Report']).Report).filter_by(mission_id=m.id).first(): generate_report(db,m.id)
    score=sync_operations_from_current_data(db,m.id)
    return {'mission_id':m.id,'created':created,'score':score.get('score',0)}
