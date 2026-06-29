from scripts import check_runtime_permissions


def test_runtime_permissions_success(monkeypatch, tmp_path):
    dirs = [tmp_path / 'evidence', tmp_path / 'runtime' / 'home']
    monkeypatch.setattr(check_runtime_permissions, 'REQUIRED_DIRS', dirs)
    assert check_runtime_permissions.main() == 0


def test_runtime_permissions_fails_for_unwritable_dir(monkeypatch, tmp_path):
    missing_parent_file = tmp_path / 'not-a-dir'
    missing_parent_file.write_text('blocking file', encoding='utf-8')
    dirs = [missing_parent_file / 'child']
    monkeypatch.setattr(check_runtime_permissions, 'REQUIRED_DIRS', dirs)
    assert check_runtime_permissions.main() == 1
