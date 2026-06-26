from __future__ import annotations
import hashlib, json
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.models import *
from app.operations.service import initialize_operations_for_mission, safe_sync
from app.operations.timeline import create_timeline_event
from app.operations.schemas import TimelineEventCreate
from app.reports.service import generate_report

DEMO_NAME='Demo Windows AD Lab'; DEMO_SCOPE='192.168.56.0/24'

def _one(db, model, defaults=None, **kw):
    row=db.query(model).filter_by(**kw).first()
    if row: return row
    row=model(**kw, **(defaults or {})); db.add(row); db.commit(); db.refresh(row); return row

def seed_demo(db:Session)->Mission:
    m=db.query(Mission).filter_by(name=DEMO_NAME).first()
    if not m:
        m=Mission(name=DEMO_NAME, scenario='windows_ad_internal', mode='safe', status='demo_ready', raw_scope=DEMO_SCOPE, validated_targets=[DEMO_SCOPE]); db.add(m); db.commit(); db.refresh(m)
        initialize_operations_for_mission(db, m.id)
    host_specs=[('192.168.56.10','DC01',True,[53,88,389,445]),('192.168.56.20','WS01',False,[445,3389]),('192.168.56.30','WEB01',False,[80,443])]
    hosts={}
    for ip,hn,dc,ports in host_specs:
        h=_one(db, Host, mission_id=m.id, ip=ip, defaults={'hostname':hn,'status':'up','os_guess':'Windows','is_domain_controller_candidate':dc})
        hosts[ip]=h
        names={53:'domain',88:'kerberos-sec',389:'ldap',445:'microsoft-ds',3389:'ms-wbt-server',80:'http',443:'https'}
        for p in ports: _one(db, Service, mission_id=m.id, host_id=h.id, port=p, protocol='tcp', defaults={'name':names[p],'product':'demo','version':'','state':'open'})
    _one(db, SMBFact, mission_id=m.id, ip='192.168.56.10', defaults={'host_id':hosts['192.168.56.10'].id,'hostname':'DC01','domain':'LAB.LOCAL','os':'Windows Server 2022','smb_signing_required':True,'smbv1_enabled':False,'null_session_possible':False,'source':'demo'})
    _one(db, SMBFact, mission_id=m.id, ip='192.168.56.20', defaults={'host_id':hosts['192.168.56.20'].id,'hostname':'WS01','domain':'LAB.LOCAL','os':'Windows 11','smb_signing_required':False,'smbv1_enabled':False,'null_session_possible':False,'source':'demo'})
    for url,port,scheme in [('http://192.168.56.30',80,'http'),('https://192.168.56.30',443,'https')]: _one(db, WebTarget, mission_id=m.id, url=url, defaults={'host_id':hosts['192.168.56.30'].id,'ip':'192.168.56.30','port':port,'scheme':scheme,'source':'demo'})
    finds=[('Domain Controller candidate detected','info','nmap','192.168.56.10'),('SMB signing not required','medium','netexec','192.168.56.20'),('RDP exposed on internal host','low','nmap','192.168.56.20'),('Example Nuclei web exposure','low','nuclei','192.168.56.30'),('Potential path to Domain Admins detected','high','bloodhound','192.168.56.10')]
    first_f=None
    for title,sev,src,ip in finds:
        f=_one(db, Finding, mission_id=m.id, title=title, defaults={'host_id':hosts[ip].id,'severity':sev,'description':f'Demo finding: {title}','source':src,'confidence':'demo','host':hosts[ip].hostname,'ip':ip,'port':445 if src in ('netexec','bloodhound') else None,'tags':['demo'],'references':[],'raw_json':{'demo':True}})
        first_f=first_f or f
    c=_one(db, BloodHoundCollection, mission_id=m.id, filename='demo_sharphound.zip', defaults={'status':'ingested','source':'demo','zip_valid':True,'zip_summary_json':{'domain':'LAB.LOCAL'},'ingestion_enabled':False,'ingestion_status':'ingested'})
    _one(db, BloodHoundStat, mission_id=m.id, defaults={'collection_id':c.id,'domain_name':'LAB.LOCAL','users_count':42,'computers_count':12,'groups_count':18,'ous_count':2,'gpos_count':5,'domains_count':1,'edges_count':128,'raw_stats_json':{'demo':True}})
    base=Path(get_settings().evidence_dir)/m.id/'demo'; base.mkdir(parents=True, exist_ok=True)
    for fn,content,mime in [('demo-log.txt','Demo Windows AD lab seed log\n','text/plain'),('demo-finding.json',json.dumps({'finding':'demo'},indent=2),'application/json')]:
        path=base/fn; path.write_text(content,encoding='utf-8'); sha=hashlib.sha256(path.read_bytes()).hexdigest()
        ev=_one(db, Evidence, mission_id=m.id, filename=fn, defaults={'label':fn,'category':'demo','description':'Demo scenario evidence','stored_path':str(path),'sha256':sha,'size_bytes':path.stat().st_size,'mime_type':mime,'source':'demo_seed','preview_available':True,'metadata_json':{'demo':True}})
        if first_f: _one(db, EvidenceLink, mission_id=m.id, evidence_id=ev.id, target_type='finding', target_id=first_f.id)
    for t,s in [('demo.seeded','system'),('demo.nmap.loaded','nmap'),('demo.netexec.loaded','netexec'),('demo.nuclei.loaded','nuclei'),('demo.bloodhound.loaded','bloodhound')]:
        if not db.query(MissionTimelineEvent).filter_by(mission_id=m.id,event_type=t).first(): create_timeline_event(db,m.id,TimelineEventCreate(event_type=t,title=t.replace('.',' ').title(),source=s,severity='success'))
    safe_sync(db,m.id)
    if not db.query(Report).filter_by(mission_id=m.id).first(): generate_report(db,m.id)
    return m
