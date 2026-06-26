import asyncio

from app.api.routes_events import query_events
from app.db.models import Mission, MissionEvent
from app.events.persistent import publish_mission_event


def test_publish_mission_event_writes_db(monkeypatch, db_session):
    class R:
        def xadd(self, *a, **k):
            return '1-0'

    monkeypatch.setattr('app.queue.connection.get_redis_connection', lambda: R())
    m = Mission(name='m', scenario='s', mode='safe', status='running', raw_scope='x', validated_targets=['x'])
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    e = asyncio.run(publish_mission_event(db_session, m.id, 'job.queued', {'job_id': 'j'}, source='nmap'))
    assert e.id and e.redis_stream_id == '1-0'
    assert db_session.query(MissionEvent).filter_by(mission_id=m.id).count() == 1


def test_event_listing_filters_and_limit(db_session):
    m = Mission(name='m', scenario='s', mode='safe', status='running', raw_scope='x', validated_targets=['x'])
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    db_session.add_all(
        [
            MissionEvent(mission_id=m.id, event_type='a', source='s1', payload_json={}),
            MissionEvent(mission_id=m.id, event_type='b', source='s2', payload_json={}),
        ]
    )
    db_session.commit()
    assert len(query_events(db_session, m.id, limit=5000)) == 2
    assert len(query_events(db_session, m.id, event_type='a')) == 1
    assert len(query_events(db_session, m.id, source='s2')) == 1
