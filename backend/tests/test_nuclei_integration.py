import json
from pathlib import Path
import pytest
from app.db.models import Mission, Host, Service, Finding, NextAction
from app.integrations.nuclei.targets import build_web_targets_for_mission
from app.jobs.nuclei_policy import validate_nuclei_command
from app.jobs.command_policy import CommandPolicyError
from app.parsers.nuclei_jsonl import parse_nuclei_jsonl
from app.planner.next_actions import plan_for_mission, plan_after_nuclei

def add_svc(db_session, mission_id, ip, port, name='x', product=''):
    h=Host(mission_id=mission_id,ip=ip,status='up'); db_session.add(h); db_session.flush(); db_session.add(Service(mission_id=mission_id,host_id=h.id,port=port,protocol='tcp',name=name,product=product,version='',state='open')); db_session.commit(); return h

def test_web_target_builder(db_session):
    m=Mission(name='m',scenario='s',mode='safe',raw_scope='10.0.0.0/24',validated_targets=['10.0.0.0/24']); db_session.add(m); db_session.commit()
    add_svc(db_session,m.id,'10.0.0.1',80,'http'); add_svc(db_session,m.id,'10.0.0.2',443,'https'); add_svc(db_session,m.id,'10.0.0.3',8080,'x'); add_svc(db_session,m.id,'10.0.0.4',8443,'x'); add_svc(db_session,m.id,'10.0.0.5',1234,'http-alt'); add_svc(db_session,m.id,'10.0.0.6',22,'ssh')
    assert build_web_targets_for_mission(db_session,m.id)==['http://10.0.0.1','http://10.0.0.3:8080','http://10.0.0.5:1234','https://10.0.0.2','https://10.0.0.4:8443']

def test_nuclei_policy_blocks_and_allows():
    for c in ['nuclei -list targets.txt -headless','nuclei -list targets.txt -code','nuclei -list targets.txt -fuzz','nuclei -list targets.txt -interactsh','nuclei -list targets.txt -proxy http://127.0.0.1:8080','nuclei -list targets.txt -H Cookie: test=1','nuclei -list targets.txt -var token=abc']:
        with pytest.raises(CommandPolicyError): validate_nuclei_command(c.split())
    validate_nuclei_command('nuclei -list targets.txt -jsonl -o nuclei.jsonl -severity info,low,medium,high,critical -rl 20 -c 10 -timeout 10 -retries 1 -no-color'.split())

def test_nuclei_jsonl_parser(tmp_path:Path):
    p=tmp_path/'n.jsonl'; p.write_text('\nnot-json\n'+json.dumps({'template-id':'exposed-panel','info':{'name':'Exposed Admin Panel','severity':'weird','description':'d','tags':['exposure','panel'],'reference':['https://e']},'type':'http','matcher-name':'word','matched-at':'http://1.1.1.1:8080/admin','host':'http://1.1.1.1:8080','ip':'1.1.1.1','port':'8080','extracted-results':['x']})+'\n')
    r=parse_nuclei_jsonl(p); assert len(r)==1; assert r[0].severity=='info'; assert r[0].tags==['exposure','panel']; assert r[0].raw_json['template-id']=='exposed-panel'
    e=tmp_path/'e.jsonl'; e.write_text(''); assert parse_nuclei_jsonl(e)==[]

def test_planner_nuclei_actions(db_session):
    m=Mission(name='m',scenario='s',mode='safe',raw_scope='10.0.0.0/24',validated_targets=['10.0.0.0/24']); db_session.add(m); db_session.commit(); add_svc(db_session,m.id,'10.0.0.1',80,'http')
    _, actions=plan_for_mission(db_session,m.id); assert any(a.command_template_id=='nuclei_web_exposure_scan' for a in actions)
    _, actions2=plan_for_mission(db_session,m.id); assert not any(a.command_template_id=='nuclei_web_exposure_scan' for a in actions2)
    f=Finding(mission_id=m.id,title='x',severity='high',description='',source='nuclei',confidence='medium'); db_session.add(f); db_session.commit(); _, acts=plan_after_nuclei(db_session,m.id,[f]); assert any('validation manuelle' in a.title for a in acts)
