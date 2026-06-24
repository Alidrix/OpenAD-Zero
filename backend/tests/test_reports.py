from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.db.models import Mission, Host, Service, Finding, Evidence, BloodHoundCollection
from app.main import app
from app.reports.collector import collect_report_data
from app.reports.markdown import render_markdown_report
from app.reports.html import render_html_report
from app.reports.service import generate_report
from app.core.config import get_settings


def seed(db):
    m=Mission(name='Report Mission',scenario='windows_ad_internal',mode='safe',status='completed',raw_scope='10.0.0.0/24',validated_targets=['10.0.0.1'])
    db.add(m); db.commit(); db.refresh(m)
    h=Host(mission_id=m.id,ip='10.0.0.10',hostname='dc01',status='up',os_guess='Windows',is_domain_controller_candidate=True); db.add(h); db.commit(); db.refresh(h)
    db.add(Service(mission_id=m.id,host_id=h.id,port=445,protocol='tcp',name='smb',product='Windows SMB',version='10',state='open'))
    db.add(Finding(mission_id=m.id,host_id=h.id,title='Nuclei critical exposure',severity='critical',description='web issue',source='nuclei',confidence='high',template_id='exposure/test',matched_at='http://10.0.0.10',ip='10.0.0.10',port=80))
    db.add(Finding(mission_id=m.id,host_id=h.id,title='BloodHound path to privileged group',severity='high',description='path',source='bloodhound',confidence='medium',ip='10.0.0.10'))
    db.add(Evidence(mission_id=m.id,label='scan xml',category='scan',filename='nmap.xml',stored_path='/tmp/nmap.xml',sha256='a'*64,size_bytes=12,mime_type='text/xml',source='nmap'))
    db.add(BloodHoundCollection(mission_id=m.id,status='validated',filename='bh.zip',stored_path='/tmp/bh.zip',sha256='b'*64,zip_valid=True,ingestion_status='bloodhound_disabled'))
    db.commit(); return m


def test_collect_and_render_and_generate(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), 'evidence_dir', str(tmp_path))
    m=seed(db_session)
    data=collect_report_data(db_session, m.id)
    assert data['mission']['name']=='Report Mission'
    assert data['hosts'][0]['services'][0]['port']==445
    assert len(data['findings'])==2
    assert data['evidence'][0]['label']=='scan xml'
    md=render_markdown_report(data)
    assert 'Report Mission' in md and '10.0.0.0/24' in md and 'Nuclei critical exposure' in md and 'scan xml' in md
    html=render_html_report(md, data)
    assert '<html' in html.lower() and 'OpenAD Zero Report' in html
    r=generate_report(db_session, m.id)
    assert Path(r.markdown_path).exists()
    assert Path(r.html_path).exists()
    assert Path(r.metadata_path).exists()


def test_report_api_endpoints(monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), 'evidence_dir', str(tmp_path))
    engine=create_engine('sqlite:///:memory:', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine); Session=sessionmaker(bind=engine); db=Session(); m=seed(db); mission_id=m.id; db.close()
    def override():
        d=Session()
        try: yield d
        finally: d.close()
    app.dependency_overrides[get_db]=override
    try:
        client=TestClient(app)
        res=client.post(f'/api/missions/{mission_id}/report/generate', json={'include_sections':None}); assert res.status_code==200, res.text
        assert client.get(f'/api/missions/{mission_id}/report').json()['report']['id']==res.json()['id']
        pm=client.get(f'/api/missions/{mission_id}/report/preview?format=markdown'); assert pm.status_code==200 and 'Report Mission' in pm.json()['content']
        ph=client.get(f'/api/missions/{mission_id}/report/preview?format=html'); assert ph.status_code==200 and '<html' in ph.json()['content'].lower()
        dm=client.get(f'/api/missions/{mission_id}/report/download?format=markdown'); assert dm.status_code==200 and b'Report Mission' in dm.content
        dh=client.get(f'/api/missions/{mission_id}/report/download?format=html'); assert dh.status_code==200 and b'<html' in dh.content.lower()
    finally:
        app.dependency_overrides.clear(); Base.metadata.drop_all(engine)


def test_empty_report(db_session, monkeypatch, tmp_path):
    monkeypatch.setattr(get_settings(), 'evidence_dir', str(tmp_path))
    m=Mission(name='Empty Mission',scenario='windows_ad_internal',mode='safe',status='created',raw_scope='10.0.0.1',validated_targets=['10.0.0.1'])
    db_session.add(m); db_session.commit(); db_session.refresh(m)
    r=generate_report(db_session, m.id)
    assert Path(r.markdown_path).read_text().count('No SMB facts available.') == 1


def test_report_includes_operations_sections(db_session):
    from app.db.models import Mission
    from app.operations.service import initialize_operations_for_mission
    from app.reports.service import generate_report
    m=Mission(name='ops',scenario='windows_ad_internal',mode='safe',status='scope_validated',raw_scope='10.0.0.1',validated_targets=['10.0.0.1']); db_session.add(m); db_session.commit(); db_session.refresh(m)
    initialize_operations_for_mission(db_session,m.id)
    r=generate_report(db_session,m.id)
    md=open(r.markdown_path,encoding='utf-8').read()
    assert '## Mission Objective' in md
    assert '## Mission Progress' in md
    assert '## Mission Phases' in md
    assert '## Timeline' in md
