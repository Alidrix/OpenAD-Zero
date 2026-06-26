import asyncio
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api.routes_missions import cancel_job, get_job, get_job_logs, list_jobs, retry_job
from app.db.models import Job, JobLog, Mission


def setup(db):
    m = Mission(name='m', scenario='s', mode='safe', status='running', raw_scope='x', validated_targets=['x'])
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def test_jobs_api_list_get_logs(db_session):
    m = setup(db_session)
    j = Job(mission_id=m.id, type='nmap_discovery', tool='nmap', status='queued', command_preview='nmap')
    db_session.add(j)
    db_session.commit()
    db_session.refresh(j)
    db_session.add(JobLog(mission_id=m.id, job_id=j.id, line='hello'))
    db_session.commit()
    assert list_jobs(m.id, db_session)[0]['id'] == j.id
    assert get_job(m.id, j.id, db_session)['status'] == 'queued'
    assert get_job_logs(m.id, j.id, db_session)[0]['line'] == 'hello'


def test_cancel_queued_and_running(monkeypatch, db_session):
    monkeypatch.setattr(
        'app.events.persistent.get_redis_connection',
        lambda: (_ for _ in ()).throw(RuntimeError('no redis')),
        raising=False,
    )
    m = setup(db_session)
    j = Job(mission_id=m.id, type='nmap_discovery', tool='nmap', status='queued', command_preview='nmap')
    db_session.add(j)
    db_session.commit()
    db_session.refresh(j)
    res = asyncio.run(cancel_job(m.id, j.id, db_session))
    assert res['status'] == 'cancelled'
    r = Job(
        mission_id=m.id,
        type='nmap_discovery',
        tool='nmap',
        status='running',
        command_preview='nmap',
        started_at=datetime.utcnow(),
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    res = asyncio.run(cancel_job(m.id, r.id, db_session))
    assert res['status'] == 'cancel_requested'


def test_retry_failed_and_refuse_completed(monkeypatch, db_session):
    monkeypatch.setattr('app.api.routes_missions.enqueue_job', lambda db, mid, jid, jt: 'rq-1')
    monkeypatch.setattr(
        'app.events.persistent.get_redis_connection',
        lambda: (_ for _ in ()).throw(RuntimeError('no redis')),
        raising=False,
    )
    m = setup(db_session)
    j = Job(
        mission_id=m.id,
        type='nmap_discovery',
        tool='nmap',
        status='failed',
        command_preview='nmap',
        attempts=0,
        max_attempts=2,
    )
    db_session.add(j)
    db_session.commit()
    db_session.refresh(j)
    assert asyncio.run(retry_job(m.id, j.id, db_session))['status'] == 'pending'
    c = Job(mission_id=m.id, type='nmap_discovery', tool='nmap', status='completed', command_preview='nmap')
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    with pytest.raises(HTTPException):
        asyncio.run(retry_job(m.id, c.id, db_session))
