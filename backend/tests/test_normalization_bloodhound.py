import zipfile
from pathlib import Path

from app.db.models import ParsedADObject, ParsedADRelation, ParseDiagnostic, ParsedSignal, Scan
from app.normalization.service import normalize_bloodhound_zip

FIX = Path(__file__).parent / 'fixtures/normalization/bloodhound'


def make_bloodhound_zip(tmp_path: Path, files: dict[str, str], name: str = 'bloodhound.zip') -> Path:
    archive = tmp_path / name
    with zipfile.ZipFile(archive, 'w') as zf:
        for member_name, content in files.items():
            zf.writestr(member_name, content)
    return archive


def make_traversal_zip(tmp_path: Path) -> Path:
    archive = tmp_path / 'traversal.zip'
    with zipfile.ZipFile(archive, 'w') as zf:
        zf.writestr('../evil.json', '{}')
    return archive


def make_malformed_zip(tmp_path: Path) -> Path:
    archive = tmp_path / 'malformed.zip'
    archive.write_text('not a zip archive', encoding='utf-8')
    return archive


def test_bloodhound_zip_objects_relations_idempotence(db_session, tmp_path):
    s = Scan(name='bh', scan_type='manual', tool_name='bloodhound')
    db_session.add(s)
    db_session.commit()
    archive = make_bloodhound_zip(
        tmp_path,
        {
            'users.json': (FIX / 'users.json').read_text(encoding='utf-8'),
            'groups.json': (FIX / 'groups.json').read_text(encoding='utf-8'),
        },
    )
    normalize_bloodhound_zip(db_session, s.id, archive)
    assert db_session.query(ParsedADObject).filter_by(scan_id=s.id).count() == 2
    assert db_session.query(ParsedADRelation).filter_by(scan_id=s.id).count() == 1
    assert db_session.query(ParsedSignal).filter_by(scan_id=s.id, signal='high_value_target_detected').count() >= 1
    normalize_bloodhound_zip(db_session, s.id, archive)
    assert db_session.query(ParsedADObject).filter_by(scan_id=s.id).count() == 2


def test_bloodhound_zip_safety_malformed_zip_and_malformed_json(db_session, tmp_path):
    s = Scan(name='bh', scan_type='manual', tool_name='bloodhound')
    db_session.add(s)
    db_session.commit()
    normalize_bloodhound_zip(db_session, s.id, make_traversal_zip(tmp_path))
    normalize_bloodhound_zip(db_session, s.id, make_malformed_zip(tmp_path))
    normalize_bloodhound_zip(
        db_session,
        s.id,
        make_bloodhound_zip(
            tmp_path, {'users.json': (FIX / 'malformed.json').read_text(encoding='utf-8')}, 'bad-json.zip'
        ),
    )
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='unsafe_bloodhound_zip_path').count() == 1
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='invalid_bloodhound_zip').count() == 1
    assert db_session.query(ParseDiagnostic).filter_by(scan_id=s.id, message='malformed_bloodhound_json').count() == 1
