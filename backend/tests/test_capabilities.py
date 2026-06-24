from fastapi.testclient import TestClient
from app.main import app
from app.capabilities.catalog import list_capabilities, get_capability, VALID_STATUSES, VALID_MODES, REQUIRED_FIELDS, is_executable, creates_manual_card_only
from app.capabilities.policy import planner_action_kind, should_propose_capability
from app.core.config import get_settings


def test_catalog_loads_and_validates_required_fields():
    caps=list_capabilities(); assert caps
    for c in caps:
        d=c.model_dump(); assert REQUIRED_FIELDS <= set(d)
        assert c.status in VALID_STATUSES; assert c.mode in VALID_MODES
        assert isinstance(c.risk_level,int) and 1 <= c.risk_level <= 5


def test_implemented_capabilities_present():
    implemented={c.id for c in list_capabilities() if c.status=='implemented'}
    assert {'nmap_discovery','netexec_smb_safe_enum','nuclei_web_exposure_scan','bloodhound_explorer'} <= implemented


def test_non_executable_statuses_and_manual_only_policy():
    assert not is_executable(get_capability('brute_force'))
    assert not is_executable(get_capability('persistence'))
    assert not is_executable(get_capability('lateral_movement'))
    assert creates_manual_card_only(get_capability('lateral_movement'))
    assert planner_action_kind(get_capability('brute_force')) == 'hidden'
    assert planner_action_kind(get_capability('persistence')) == 'hidden'
    assert planner_action_kind(get_capability('lateral_movement')) == 'manual_card'


def test_config_defaults_and_endpoint_no_secrets(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv('OPENADZERO_DEFAULT_MODE', raising=False)
    monkeypatch.delenv('OPENADZERO_ENABLE_LAB_MODE', raising=False)
    monkeypatch.delenv('OPENADZERO_ENABLE_ADVANCED_ACTIONS', raising=False)
    client=TestClient(app); data=client.get('/api/capabilities/config').json()
    assert data['default_mode']=='safe'; assert data['lab_mode_enabled'] is False; assert data['advanced_actions_enabled'] is False
    assert all('secret' not in k.lower() and 'token' not in k.lower() and 'password' not in k.lower() for k in data)
    get_settings.cache_clear()


def test_config_env_override(monkeypatch):
    monkeypatch.setenv('OPENADZERO_DEFAULT_MODE','assisted'); monkeypatch.setenv('OPENADZERO_ENABLE_LAB_MODE','true')
    get_settings.cache_clear(); client=TestClient(app); data=client.get('/api/capabilities/config').json()
    assert data['default_mode']=='assisted'; assert data['lab_mode_enabled'] is True
    get_settings.cache_clear()


def test_capabilities_endpoints():
    client=TestClient(app)
    assert any(c['id']=='nmap_discovery' for c in client.get('/api/capabilities').json())
    assert client.get('/api/capabilities/nmap_discovery').json()['status']=='implemented'
    assert client.get('/api/capabilities/nope').status_code==404


def test_planner_policy_rules():
    assert should_propose_capability(get_capability('brute_force')) is False
    assert should_propose_capability(get_capability('persistence')) is False
    lab_only=type('C',(),{'status':'lab_only','mode':'lab'})()
    assert should_propose_capability(lab_only, lab_mode_enabled=False) is False
    assert planner_action_kind(get_capability('nmap_discovery')) == 'executable'
