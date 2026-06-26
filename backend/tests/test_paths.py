def test_evidence_root_uses_env_tmp_path(tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.core.paths import get_evidence_root

    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'ev'))
    get_settings.cache_clear()

    root = get_evidence_root()
    assert root.exists()
    assert root.is_dir()
    assert str(root).startswith(str(tmp_path))


def test_mission_evidence_dir_stays_under_root(tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.core.paths import mission_evidence_dir

    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'ev'))
    get_settings.cache_clear()

    path = mission_evidence_dir('mission-1', 'reports', 'r1')
    assert path.exists()
    assert path.is_dir()
    assert str(path).startswith(str(tmp_path / 'ev'))


def test_safe_join_blocks_path_traversal(tmp_path, monkeypatch):
    import pytest
    from app.core.config import get_settings
    from app.core.paths import EvidencePathError, get_evidence_root, safe_join_under_root

    monkeypatch.setenv('EVIDENCE_DIR', str(tmp_path / 'ev'))
    get_settings.cache_clear()

    root = get_evidence_root()

    with pytest.raises(EvidencePathError):
        safe_join_under_root(root, '..', 'evil')


def test_evidence_root_refuses_filesystem_root(monkeypatch):
    import pytest
    from app.core.config import get_settings
    from app.core.paths import EvidencePathError, get_evidence_root

    monkeypatch.setenv('EVIDENCE_DIR', '/')
    get_settings.cache_clear()

    with pytest.raises(EvidencePathError):
        get_evidence_root()
