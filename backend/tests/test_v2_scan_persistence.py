import pytest

from app.services import scan_orchestrator, scan_service
from app.services.scan_schemas import ScanCreate


def test_create_scan(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Initial enum', scan_type='manual'))
    assert scan.id
    assert scan.status == 'draft'
    assert scan.progress_percent == 0
    assert scan.events[0].event_type == 'scan.created'


def test_list_scans_excludes_deleted(db_session):
    kept = scan_service.create_scan(db_session, ScanCreate(name='Kept', scan_type='manual'))
    deleted = scan_service.create_scan(db_session, ScanCreate(name='Deleted', scan_type='manual'))
    scan_service.soft_delete_scan(db_session, deleted.id)
    rows = scan_service.list_scans(db_session)
    assert [row.id for row in rows] == [kept.id]
    assert {row.id for row in scan_service.list_scans(db_session, include_deleted=True)} == {kept.id, deleted.id}


def test_get_scan(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Lookup', scan_type='manual'))
    found = scan_service.get_scan(db_session, scan.id)
    assert found.id == scan.id


def test_rename_scan(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Old', scan_type='manual'))
    renamed = scan_service.rename_scan(db_session, scan.id, 'New')
    assert renamed.name == 'New'
    assert renamed.renamed_at is not None
    assert any(event.event_type == 'scan.renamed' for event in renamed.events)


def test_soft_delete_scan(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Delete me', scan_type='manual'))
    deleted = scan_service.soft_delete_scan(db_session, scan.id)
    assert deleted.status == 'deleted'
    assert deleted.deleted_at is not None


def test_add_scan_event(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Events', scan_type='manual'))
    event = scan_service.add_scan_event(db_session, scan.id, 'scan.note', 'Operator note', {'safe': True})
    db_session.commit()
    assert event.id
    assert event.payload_json == {'safe': True}


def test_update_scan_progress(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Progress', scan_type='manual'))
    updated = scan_service.update_scan_progress(db_session, scan.id, 50, current_step='Parsing', status='running')
    assert updated.progress_percent == 50
    assert updated.current_step == 'Parsing'
    assert updated.status == 'running'


@pytest.mark.parametrize('percent', [-1, 101])
def test_update_scan_progress_rejects_invalid_percent(db_session, percent):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Invalid progress', scan_type='manual'))
    with pytest.raises(ValueError, match='between 0 and 100'):
        scan_service.update_scan_progress(db_session, scan.id, percent)


def test_request_stop_without_rq_job(db_session):
    scan = scan_service.create_scan(db_session, ScanCreate(name='Stop', scan_type='manual'))
    stopped = scan_orchestrator.request_scan_stop(db_session, scan.id)
    assert stopped.status == 'stopped'
    assert stopped.stopped_at is not None
    assert stopped.finished_at is not None
