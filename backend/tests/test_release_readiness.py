import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_release_docs_present():
    for path in ['docs/RELEASE_READINESS.md', 'docs/INSTALL.md', 'docs/AUTHENTICATION.md']:
        assert (ROOT / path).exists()


def test_security_check_refuses_binary_normalization_fixture(tmp_path):
    fixture = ROOT / 'backend/tests/fixtures/normalization/prompt15_tmp.bin'
    fixture.write_bytes(b'bin')
    try:
        result = subprocess.run(
            ['bash', 'scripts/security-check.sh'], cwd=ROOT, text=True, capture_output=True, timeout=60
        )
        assert result.returncode != 0
        assert 'Binary fixture' in result.stdout + result.stderr
    finally:
        fixture.unlink(missing_ok=True)


def test_release_check_contains_alembic_head_guard():
    text = (ROOT / 'scripts/release-check.sh').read_text()
    assert 'alembic heads' in text
    assert 'head_count' in text
