from pathlib import Path

from app.core.version import get_app_version


def test_get_app_version_returns_non_empty_string():
    version = get_app_version()
    assert isinstance(version, str)
    assert version.strip()


def test_api_version(client):
    response = client.get('/api/version')
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'OpenAD Zero'
    assert data['release_stage'] == 'release-candidate'
    assert isinstance(data['version'], str)
    assert data['version']


def test_api_version_matches_version_file_or_rc_prefix(client):
    response = client.get('/api/version')
    assert response.status_code == 200
    version = response.json()['version']
    version_file = Path(__file__).resolve().parents[2] / 'VERSION'
    if version_file.exists():
        assert version == version_file.read_text(encoding='utf-8').strip()
    else:
        assert version.startswith('0.1.0')
