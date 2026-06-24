import pytest
from app.db.models import Mission, Job
from app.queue.enqueue import enqueue_job

class FakeRQJob: id='rq-123'
class FakeQueue:
    def enqueue(self,*a,**k): return FakeRQJob()

def mission(db):
    m=Mission(name='m',scenario='s',mode='safe',status='scope_validated',raw_scope='10.0.0.1',validated_targets=['10.0.0.1']); db.add(m); db.commit(); db.refresh(m); return m

def test_allowed_job_type_enqueues(monkeypatch, db_session):
    monkeypatch.setattr('app.queue.enqueue.get_scan_queue', lambda: FakeQueue())
    async def fake_publish(*args, **kwargs): return None
    monkeypatch.setattr('app.events.persistent.publish_mission_event', fake_publish)
    m=mission(db_session); j=Job(mission_id=m.id,type='nmap_discovery',tool='nmap',status='pending',command_preview='nmap'); db_session.add(j); db_session.commit(); db_session.refresh(j)
    assert enqueue_job(db_session,m.id,j.id,j.type)=='rq-123'
    db_session.refresh(j); assert j.status=='queued' and j.rq_job_id=='rq-123' and j.queued_at is not None

def test_unknown_job_type_refused(db_session):
    m=mission(db_session)
    with pytest.raises(ValueError): enqueue_job(db_session,m.id,'job-x','unknown')
