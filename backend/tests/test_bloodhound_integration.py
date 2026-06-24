import io, zipfile
from app.integrations.bloodhound.zip_inspector import inspect_sharphound_zip, sha256_file
from app.api.routes_missions import _bh_command
from app.db.models import Mission, Host, Service, NextAction
from app.planner.next_actions import plan_for_mission, plan_after_netexec, plan_after_bloodhound_upload

def make_zip(entries):
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w') as z:
        for name,data in entries.items(): z.writestr(name,data)
    bio.seek(0); return bio.getvalue()

def test_zip_valid_with_json(tmp_path):
    p=tmp_path/'bh.zip'; p.write_bytes(make_zip({'users.json':'{"meta":{"type":"users"}}'}))
    r=inspect_sharphound_zip(p)
    assert r['valid']; assert r['json_files_count']==1; assert 'users' in r['file_types_detected']

def test_zip_empty(tmp_path):
    p=tmp_path/'empty.zip'; p.write_bytes(make_zip({}))
    assert not inspect_sharphound_zip(p)['valid']

def test_zip_without_json(tmp_path):
    p=tmp_path/'x.zip'; p.write_bytes(make_zip({'readme.txt':'x'}))
    assert not inspect_sharphound_zip(p)['valid']

def test_zip_path_traversal_refused(tmp_path):
    p=tmp_path/'evil.zip'; p.write_bytes(make_zip({'../evil.json':'{}'}))
    r=inspect_sharphound_zip(p); assert not r['valid']; assert any('path traversal' in w for w in r['warnings'])

def test_zip_large_file_simulated(monkeypatch,tmp_path):
    import app.integrations.bloodhound.zip_inspector as zi
    monkeypatch.setattr(zi,'MAX_ENTRY_BYTES',1)
    p=tmp_path/'large.zip'; p.write_bytes(make_zip({'users.json':'{}'}))
    assert not zi.inspect_sharphound_zip(p)['valid']

def test_malformed_json_accepted_with_warning(tmp_path):
    p=tmp_path/'badjson.zip'; p.write_bytes(make_zip({'users.json':'{bad'}))
    r=inspect_sharphound_zip(p); assert r['valid']; assert r['warnings']

def test_sha256(tmp_path):
    p=tmp_path/'a.zip'; p.write_bytes(b'abc')
    assert sha256_file(p)=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'

def test_sharphound_command_safe():
    c=_bh_command('mission 1') ['command']
    assert 'openadzero_mission_1_sharphound.zip' in c
    assert 'password' not in c.lower() and 'pass' not in c.lower()
    assert '-c Default' in c and 'Loop' not in c and 'Session' not in c

def test_planner_dc_candidate(db_session):
    m=Mission(id='m1',name='m',scenario='s',mode='safe',raw_scope='10.0.0.1',validated_targets=[]); db_session.add(m)
    h=Host(mission_id='m1',ip='10.0.0.1',status='up'); db_session.add(h); db_session.flush(); db_session.add(Service(mission_id='m1',host_id=h.id,port=88,protocol='tcp',name='kerberos',product='',version='',state='open')); db_session.commit()
    _,a=plan_for_mission(db_session,'m1'); assert any(x.command_template_id=='bloodhound_prepare_collection' for x in a)

def test_planner_netexec_domain_no_duplicate(db_session):
    m=Mission(id='m2',name='m',scenario='s',mode='safe',raw_scope='10.0.0.1',validated_targets=[]); db_session.add(m); db_session.commit()
    plan_after_netexec(db_session,'m2',[{'domain':'LAB'}],[],'netexec_smb_fingerprint')
    plan_after_netexec(db_session,'m2',[{'domain':'LAB'}],[],'netexec_smb_fingerprint')
    assert db_session.query(NextAction).filter_by(mission_id='m2',command_template_id='bloodhound_prepare_collection').count()==1

def test_planner_no_dc_no_action(db_session):
    m=Mission(id='m3',name='m',scenario='s',mode='safe',raw_scope='10.0.0.1',validated_targets=[]); db_session.add(m); db_session.add(Host(mission_id='m3',ip='10.0.0.1',status='up')); db_session.commit()
    _,a=plan_for_mission(db_session,'m3'); assert not any(x.command_template_id=='bloodhound_prepare_collection' for x in a)

def test_plan_after_valid_upload(db_session):
    m=Mission(id='m4',name='m',scenario='s',mode='safe',raw_scope='10.0.0.1',validated_targets=[]); db_session.add(m); db_session.commit()
    a=plan_after_bloodhound_upload(db_session,'m4',True); assert a[0].command_template_id=='bloodhound_analyze_imported_data'
