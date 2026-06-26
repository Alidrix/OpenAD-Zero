import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.models import Evidence, Mission
from app.db.session import Base, get_db
from app.evidence.preview import build_preview, can_preview
from app.evidence.storage import compute_sha256, safe_extension, sanitize_filename
from app.main import app


def client_with_db(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    settings = get_settings()
    monkeypatch.setattr(settings, 'evidence_dir', str(tmp_path))
    monkeypatch.setattr(settings, 'openadzero_enable_external_evidence_import', True)
    monkeypatch.setattr(settings, 'external_evidence_max_upload_mb', 1)
    c = TestClient(app)
    try:
        db = Session()
        m = Mission(
            name='m',
            scenario='s',
            mode='safe',
            status='scope_validated',
            raw_scope='127.0.0.1',
            validated_targets=['127.0.0.1'],
        )
        db.add(m)
        db.commit()
        db.refresh(m)
        mid = m.id
        db.close()
        yield c, mid, Session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)


def upload(c, mid, name, data, label='ev'):
    return c.post(
        f'/api/missions/{mid}/evidence/import',
        data={'label': label, 'category': 'external', 'description': 'd'},
        files={'file': (name, data, 'text/plain')},
    )


def test_storage_helpers(tmp_path):
    assert sanitize_filename('report.txt') == 'report.txt'
    assert safe_extension('report.TXT', {'.txt'}) == '.txt'
    p = tmp_path / 'a.txt'
    p.write_text('abc')
    assert compute_sha256(p) == hashlib.sha256(b'abc').hexdigest()
    for bad in ('../x.txt', '', 'x.exe'):
        try:
            safe_extension(bad, {'.txt'})
            raise AssertionError
        except ValueError:
            pass


def test_preview_helpers(tmp_path):
    p = tmp_path / 'a.json'
    p.write_text('{"a":1}')
    e = Evidence(
        mission_id='m',
        label='l',
        category='external',
        filename='a.json',
        stored_path=str(p),
        sha256='0' * 64,
        size_bytes=7,
        mime_type='application/json',
        source='external_upload',
        preview_available=True,
        metadata_json={},
    )
    assert can_preview(e)
    pv = build_preview(e, 100)
    assert pv['available'] and pv['format'] == 'json' and '"a"' in pv['content']


def test_evidence_api_flow(tmp_path, monkeypatch):
    for c, mid, _Session in client_with_db(tmp_path, monkeypatch):
        r = upload(c, mid, 'note.txt', b'hello')
        assert r.status_code == 200, r.text
        ev = r.json()
        assert ev['sha256'] == hashlib.sha256(b'hello').hexdigest()
        assert ev['preview_available']
        base = Path(ev['stored_path']).parent
        assert (base / 'metadata.json').exists()
        assert (base / 'sha256.txt').exists()
        assert json.loads((base / 'metadata.json').read_text())['original_filename'] == 'note.txt'
        assert c.get(f'/api/missions/{mid}/evidence').json()[0]['id'] == ev['id']
        assert c.get(f'/api/missions/{mid}/evidence/{ev["id"]}').json()['filename'] == 'note.txt'
        pv = c.get(f'/api/missions/{mid}/evidence/{ev["id"]}/preview').json()
        assert pv['available'] and 'hello' in pv['content']
        jr = upload(c, mid, 'data.json', b'{"ok": true}', 'json')
        assert jr.status_code == 200
        assert c.get(f'/api/missions/{mid}/evidence/{jr.json()["id"]}/preview').json()['format'] == 'json'
        zr = upload(c, mid, 'archive.zip', b'PK\x03\x04', 'zip')
        assert zr.status_code == 200
        assert not c.get(f'/api/missions/{mid}/evidence/{zr.json()["id"]}/preview').json()['available']
        assert upload(c, mid, 'bad.exe', b'x').status_code == 400
        assert upload(c, mid, 'empty.txt', b'').status_code == 400
        assert upload(c, mid, '../evil.txt', b'x').status_code == 400
        assert upload(c, mid, 'big.txt', b'a' * (1024 * 1024 + 1)).status_code == 413
        lr = c.post(
            f'/api/missions/{mid}/evidence/{ev["id"]}/links', json={'target_type': 'finding', 'target_id': 'f1'}
        )
        assert lr.status_code == 200
        links = c.get(f'/api/missions/{mid}/evidence/{ev["id"]}/links').json()
        assert len(links) == 1
        assert c.delete(f'/api/missions/{mid}/evidence/{ev["id"]}/links/{links[0]["id"]}').status_code == 200
        assert c.delete(f'/api/missions/{mid}/evidence/{ev["id"]}').status_code == 200
