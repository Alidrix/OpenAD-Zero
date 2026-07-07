from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Job, ParsedAsset, ParseDiagnostic, ParsedService, ParsedSignal, Scan
from app.db.session import Base, get_db
from app.main import app


def _client_with_db(client):
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    return Session, engine


def _cleanup(engine):
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def test_v2_dashboard_summary_empty_and_shape(client):
    _, engine = _client_with_db(client)
    try:
        response = client.get('/api/v2/dashboard/summary')

        assert response.status_code == 200
        data = response.json()
        for key in ('scans', 'parsed', 'signals', 'services', 'assets', 'ad_surface'):
            assert key in data
        assert data['parsed'] == {
            'assets': 0,
            'services': 0,
            'findings': 0,
            'signals': 0,
            'diagnostics': 0,
        }
        assert data['signals']['smb_open'] == 0
    finally:
        _cleanup(engine)


def test_v2_dashboard_summary_aggregates_parsed_rows_and_filters_scan_id(client, monkeypatch):
    Session, engine = _client_with_db(client)
    subprocess_called = False

    def fake_subprocess(*_args, **_kwargs):
        nonlocal subprocess_called
        subprocess_called = True
        raise AssertionError('dashboard summary must not call subprocess')

    monkeypatch.setattr('subprocess.run', fake_subprocess)
    try:
        db = Session()
        scan_one = Scan(name='one', scan_type='manual', tool_name='manual', status='completed')
        scan_two = Scan(name='two', scan_type='manual', tool_name='manual', status='completed')
        db.add_all([scan_one, scan_two])
        db.flush()

        asset = ParsedAsset(
            scan_id=scan_one.id,
            source_type='test',
            ip_address='10.0.0.10',
            os_family='windows',
            confidence=0.9,
        )
        db.add(asset)
        db.flush()
        db.add_all(
            [
                ParsedService(
                    scan_id=scan_one.id,
                    asset_id=asset.id,
                    source_type='test',
                    ip_address='10.0.0.10',
                    port=445,
                    protocol='tcp',
                    service_name='smb',
                    state='open',
                    confidence=0.9,
                ),
                ParsedSignal(
                    scan_id=scan_one.id,
                    asset_id=asset.id,
                    source_type='test',
                    signal='ldap_open',
                    value='true',
                    confidence=0.9,
                ),
                ParsedSignal(
                    scan_id=scan_one.id,
                    asset_id=asset.id,
                    source_type='test',
                    signal='kerberos_open',
                    value='true',
                    confidence=0.9,
                ),
                ParsedAsset(
                    scan_id=scan_two.id,
                    source_type='test',
                    ip_address='10.0.0.20',
                    confidence=0.9,
                ),
            ]
        )
        db.commit()
        scan_one_id = scan_one.id
        jobs_before = db.query(Job).count()
        db.close()

        response = client.get(f'/api/v2/dashboard/summary?scan_id={scan_one_id}')
        assert response.status_code == 200
        data = response.json()
        assert data['parsed']['assets'] == 1
        assert data['parsed']['services'] == 1
        assert data['signals']['smb_open'] >= 1
        assert data['ad_surface']['smb_hosts'] == 1
        assert data['signals']['ldap_open'] == 1
        assert data['signals']['kerberos_open'] == 1

        db = Session()
        assert db.query(Job).count() == jobs_before
        db.close()
        assert subprocess_called is False
    finally:
        _cleanup(engine)


def test_v2_dashboard_summary_missing_scan_returns_404(client):
    _, engine = _client_with_db(client)
    try:
        response = client.get('/api/v2/dashboard/summary?scan_id=missing')

        assert response.status_code == 404
    finally:
        _cleanup(engine)


def test_v2_dashboard_summary_limit_recent_and_deleted_filter(client):
    Session, engine = _client_with_db(client)
    try:
        db = Session()
        live_one = Scan(name='live-one', scan_type='manual', tool_name='manual', status='completed')
        live_two = Scan(name='live-two', scan_type='manual', tool_name='manual', status='completed')
        deleted = Scan(
            name='deleted',
            scan_type='manual',
            tool_name='manual',
            status='deleted',
            deleted_at=datetime.utcnow(),
        )
        db.add_all([live_one, live_two, deleted])
        db.flush()
        db.add_all(
            [
                ParseDiagnostic(scan_id=live_one.id, source_type='test', level='warning', message='one'),
                ParseDiagnostic(scan_id=live_two.id, source_type='test', level='warning', message='two'),
                ParsedAsset(scan_id=deleted.id, source_type='test', ip_address='10.0.0.99'),
                ParseDiagnostic(scan_id=deleted.id, source_type='test', level='warning', message='deleted'),
            ]
        )
        db.commit()
        db.close()

        response = client.get('/api/v2/dashboard/summary?limit_recent=1')
        assert response.status_code == 200
        data = response.json()
        assert data['scans']['total'] == 2
        assert data['scans']['deleted'] == 0
        assert data['parsed']['assets'] == 0
        assert len(data['recent_scans']) == 1
        assert len(data['recent_diagnostics']) == 1

        response = client.get('/api/v2/dashboard/summary?include_deleted=true&limit_recent=10')
        assert response.status_code == 200
        data = response.json()
        assert data['scans']['total'] == 3
        assert data['scans']['deleted'] == 1
        assert data['parsed']['assets'] == 1
        assert len(data['recent_scans']) == 3
        assert len(data['recent_diagnostics']) == 3
    finally:
        _cleanup(engine)
