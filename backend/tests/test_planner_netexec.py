from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.db.models import Mission, Host, Service, SMBFact
from app.planner.next_actions import plan_for_mission, plan_after_netexec

def session():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()

def test_smb_after_nmap_proposes_netexec_actions():
    db=session(); m=Mission(name='m', scenario='windows_ad_internal', mode='safe', status='running', raw_scope='192.168.1.10', validated_targets=['192.168.1.10']); db.add(m); db.commit()
    h=Host(mission_id=m.id, ip='192.168.1.10', status='up'); db.add(h); db.flush()
    db.add(Service(mission_id=m.id, host_id=h.id, port=445, protocol='tcp', name='microsoft-ds', product='', version='', state='open')); db.commit()
    _, actions=plan_for_mission(db,m.id)
    templates={a.command_template_id for a in actions}
    assert 'netexec_smb_fingerprint' in templates
    assert 'netexec_smb_signing_check' in templates

def test_netexec_domain_signing_and_null_session_planning():
    db=session(); m=Mission(name='m', scenario='windows_ad_internal', mode='safe', status='running', raw_scope='192.168.1.20', validated_targets=['192.168.1.20']); db.add(m); db.commit()
    h=Host(mission_id=m.id, ip='192.168.1.20', status='up'); db.add(h); db.flush()
    db.add(SMBFact(mission_id=m.id, host_id=h.id, ip='192.168.1.20', hostname='DC01', domain='LAB.LOCAL', os='Windows', smb_signing_required=False, smbv1_enabled=False, null_session_possible=True, source='netexec', raw_line='SMB ...'))
    db.commit()
    findings, actions=plan_after_netexec(db,m.id)
    assert any(f.title == 'SMB signing not required' and f.severity == 'high' for f in findings)
    templates={a.command_template_id for a in actions}
    assert 'bloodhound_prepare_collection' in templates
    assert 'netexec_smb_null_session_shares' in templates
