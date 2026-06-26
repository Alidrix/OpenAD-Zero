from fastapi.testclient import TestClient

from app.capabilities.catalog import REQUIRED_FIELDS, VALID_MODES, VALID_STATUSES, get_capability, load_capabilities
from app.main import app


def test_catalog_loads_and_validates_required_fields():
    caps = load_capabilities()
    assert caps
    for capability in caps:
        data = capability.model_dump()
        assert set(data) >= REQUIRED_FIELDS
        assert capability.status in VALID_STATUSES
        assert capability.mode in VALID_MODES
        assert 1 <= capability.risk_level <= 5


def test_expected_capabilities_present_with_statuses():
    assert get_capability('nmap_discovery').status == 'implemented'
    assert get_capability('netexec_smb_safe_enum').status == 'implemented'
    assert get_capability('nuclei_web_exposure_scan').status == 'implemented'
    assert get_capability('bloodhound_explorer').status == 'implemented'
    assert get_capability('report_markdown_html').status == 'implemented'
    assert get_capability('reporting_engine_v1').status == 'implemented'


def test_capabilities_endpoint():
    client = TestClient(app)
    response = client.get('/api/capabilities')
    assert response.status_code == 200
    data = response.json()
    assert any(item['id'] == 'nmap_discovery' for item in data)
    assert all('executable' in item and 'visible' in item for item in data)


def test_capability_detail_endpoint():
    client = TestClient(app)
    response = client.get('/api/capabilities/nmap_discovery')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'implemented'
    assert 'disabled_reason' in data
    assert client.get('/api/capabilities/not-real').status_code == 404


def test_config_endpoint_exposes_no_secrets():
    client = TestClient(app)
    response = client.get('/api/capabilities/config')
    assert response.status_code == 200
    data = response.json()
    assert data['default_mode'] == 'safe'
    assert data['assisted_mode_enabled'] is True
    assert data['ctf_lab_mode_enabled'] is False
    assert not any('token' in key.lower() or 'secret' in key.lower() or 'password' in key.lower() for key in data)


def test_capability_filters_work():
    client = TestClient(app)
    by_status = client.get('/api/capabilities?status=planned').json()
    assert by_status and all(item['status'] == 'planned' for item in by_status)
    by_category = client.get('/api/capabilities?category=active_directory_analysis').json()
    assert by_category and all(item['category'] == 'active_directory_analysis' for item in by_category)
    by_mode = client.get('/api/capabilities?mode=assisted').json()
    assert by_mode and all(item['mode'] == 'assisted' for item in by_mode)
