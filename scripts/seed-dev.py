from app.db.session import SessionLocal
from app.db.models import Mission, Host, Finding

db = SessionLocal()
try:
    exists = db.query(Mission).filter(Mission.name == 'Sample Dev Mission').first()
    if exists:
        print('Sample dev seed already exists')
    else:
        m = Mission(name='Sample Dev Mission', scenario='dev', mode='safe', status='created', raw_scope='192.0.2.10', validated_targets=['192.0.2.10'])
        db.add(m); db.flush()
        h = Host(mission_id=m.id, ip='192.0.2.10', hostname='sample-host', status='up')
        db.add(h); db.flush()
        db.add(Finding(mission_id=m.id, host_id=h.id, title='Sample informational finding', severity='info', description='Development seed data only.', source='seed-dev', confidence='low'))
        db.commit(); print(f'Seeded mission {m.id}')
finally:
    db.close()
