import sys

import pytest

from app.recommendations.preview_builder import PreviewBuildError, build_preview


def test_preview_rebuilds_argv_from_allowlisted_template():
    preview = build_preview('v2_netexec_smb_fingerprint_preview', {'target': '10.0.0.5'})
    assert preview.argv_preview == [
        'nxc',
        'smb',
        '10.0.0.5',
        '--shares',
        '--no-bruteforce',
    ]
    assert preview.executable is False
    assert preview.automatic_execution_allowed is False


def test_preview_refuses_raw_command_param():
    with pytest.raises(PreviewBuildError, match='Raw frontend commands'):
        build_preview('v2_netexec_smb_fingerprint_preview', {'raw_command': 'nxc smb 10.0.0.5'})


def test_preview_refuses_unknown_template():
    with pytest.raises(PreviewBuildError, match='Unknown V2 template'):
        build_preview('unknown', {})


def test_preview_reports_missing_params():
    preview = build_preview('v2_netexec_smb_fingerprint_preview', {})
    assert preview.missing_params == ['target']
    assert '<target>' in preview.argv_preview


def test_preview_does_not_import_execution_modules():
    before = set(sys.modules)
    build_preview('v2_netexec_smb_fingerprint_preview', {'target': '10.0.0.5'})
    added = set(sys.modules) - before
    assert 'subprocess' not in added
    assert 'app.jobs.netexec_job' not in added
    assert not any(name.lower() == 'netexec' for name in added)
