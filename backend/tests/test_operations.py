import pytest

from app.db.models import Evidence, Host, Mission, Report, Service
from app.operations.objective import ensure_default_objective, update_objective
from app.operations.phases import ensure_default_phases, update_phase_status
from app.operations.progress import calculate_progress_score
from app.operations.schemas import MissionObjectiveUpdate, TimelineEventCreate
from app.operations.service import sync_operations_from_current_data
from app.operations.timeline import create_timeline_event, list_timeline_events


def mission(db):
    m = Mission(
        name='m',
        scenario='windows_ad_internal',
        mode='safe',
        status='scope_validated',
        raw_scope='10.0.0.0/24',
        validated_targets=['10.0.0.1'],
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def test_default_phases_no_duplicates(db_session):
    m = mission(db_session)
    assert len(ensure_default_phases(db_session, m.id)) == 10
    assert len(ensure_default_phases(db_session, m.id)) == 10


def test_default_objective_and_update(db_session):
    m = mission(db_session)
    o = ensure_default_objective(db_session, m.id)
    assert o.objective_type == 'domain_admin_path'
    o = update_objective(db_session, m.id, MissionObjectiveUpdate(objective_status='in_progress'))
    assert o.objective_status == 'in_progress'


def test_phase_update_and_invalid(db_session):
    m = mission(db_session)
    ensure_default_phases(db_session, m.id)
    p = update_phase_status(db_session, m.id, 'network_discovery', 'running', 'started')
    assert p.started_at and p.status == 'running'
    with pytest.raises(ValueError):
        update_phase_status(db_session, m.id, 'network_discovery', 'bad')


def test_timeline_create_ordered(db_session):
    m = mission(db_session)
    a = create_timeline_event(db_session, m.id, TimelineEventCreate(event_type='manual.a', title='A'))
    b = create_timeline_event(db_session, m.id, TimelineEventCreate(event_type='manual.b', title='B'))
    rows = list_timeline_events(db_session, m.id)
    assert rows[0].id == b.id and rows[1].id == a.id


def test_progress_empty_hosts_services_evidence_report(db_session):
    m = mission(db_session)
    ensure_default_phases(db_session, m.id)
    assert calculate_progress_score(db_session, m.id)['score'] == 0
    h = Host(mission_id=m.id, ip='10.0.0.1', hostname=None, status='up')
    db_session.add(h)
    db_session.flush()
    db_session.add(
        Service(
            mission_id=m.id, host_id=h.id, port=80, protocol='tcp', name='http', product='', version='', state='open'
        )
    )
    db_session.commit()
    assert calculate_progress_score(db_session, m.id)['score'] == 20
    db_session.add(
        Evidence(
            mission_id=m.id,
            label='e',
            category='external',
            filename='a.txt',
            stored_path='/tmp/a',
            sha256='0' * 64,
            size_bytes=1,
            mime_type='text/plain',
            source='external_upload',
            preview_available=False,
            metadata_json={},
        )
    )
    db_session.commit()
    assert 'evidence_consolidation' in calculate_progress_score(db_session, m.id)['completed_items']
    db_session.add(Report(mission_id=m.id, title='r', status='generated'))
    db_session.commit()
    assert 'reporting' in calculate_progress_score(db_session, m.id)['completed_items']


def test_operations_summary_and_sync(db_session, monkeypatch):
    from app.api.routes_operations import summary

    m = mission(db_session)
    h = Host(mission_id=m.id, ip='10.0.0.1', hostname=None, status='up')
    db_session.add(h)
    db_session.commit()
    sync_operations_from_current_data(db_session, m.id)
    assert calculate_progress_score(db_session, m.id)['score'] >= 10
    data = summary(m.id, db_session)
    assert 'progress' in data and data['counts']['hosts'] == 1
