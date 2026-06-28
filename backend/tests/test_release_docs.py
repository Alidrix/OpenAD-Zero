import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_RELEASE_FILES = [
    'VERSION',
    'CHANGELOG.md',
    'SECURITY.md',
    'docs/GOVERNANCE.md',
    'docs/GITHUB_PROJECT.md',
    'docs/SCOPE_MATRIX.md',
    'docs/RELEASE_PROCESS.md',
    'docs/RELEASE_READINESS.md',
    'docs/POST_RELEASE.md',
    'docs/KNOWN_ISSUES.md',
    'docs/backlog/v0.2.0.md',
    'docs/releases/github-release-draft-v0.1.0-rc1.md',
    '.github/CODEOWNERS',
    '.github/dependabot.yml',
    '.github/workflows/codeql.yml',
]

SENSITIVE_EXCLUSIONS = [
    'Automatic exploitation',
    'Credential dumping',
    'LSASS dump',
    'DCSync',
    'Pass-the-hash',
    'Persistence',
    'EDR bypass',
    'Lateral movement automation',
    'Arbitrary shell command from frontend',
]


def read_repo_file(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding='utf-8')


def test_release_governance_files_exist() -> None:
    for relative_path in REQUIRED_RELEASE_FILES:
        path = REPO_ROOT / relative_path
        assert path.is_file(), f'{relative_path} must exist'
        assert path.stat().st_size > 0, f'{relative_path} must not be empty'


def test_version_remains_release_candidate() -> None:
    assert read_repo_file('VERSION').strip() == '0.1.0-rc1'


def test_security_policy_does_not_include_invented_email_contact() -> None:
    security_policy = read_repo_file('SECURITY.md')
    assert '@' not in security_policy
    assert 'private vulnerability reporting' in security_policy


def test_scope_matrix_lists_sensitive_exclusions() -> None:
    scope_matrix = read_repo_file('docs/SCOPE_MATRIX.md')
    for exclusion in SENSITIVE_EXCLUSIONS:
        assert exclusion in scope_matrix


def test_release_process_marks_github_release_as_prerelease() -> None:
    assert '--prerelease' in read_repo_file('docs/RELEASE_PROCESS.md')


def test_final_release_execution_docs_are_present() -> None:
    release_process = read_repo_file('docs/RELEASE_PROCESS.md')
    assert 'gh release create' in release_process
    assert '--prerelease' in release_process
    assert 'git tag -a v0.1.0-rc1' in release_process


def test_known_issues_documents_release_candidate_limitations() -> None:
    known_issues = read_repo_file('docs/KNOWN_ISSUES.md')
    assert 'release candidate' in known_issues.lower()
    assert 'E2E prerequisites' in known_issues


def test_v020_backlog_is_prioritized() -> None:
    backlog = read_repo_file('docs/backlog/v0.2.0.md')
    assert 'P0' in backlog
    assert 'P1' in backlog
    assert 'P2' in backlog


def test_readme_links_final_release_docs() -> None:
    readme = read_repo_file('README.md')
    assert 'RELEASE_READINESS' in readme
    assert 'KNOWN_ISSUES' in readme
    assert 'POST_RELEASE' in readme


def test_frontend_tailwind_policy() -> None:
    pkg = json.loads((REPO_ROOT / 'frontend' / 'package.json').read_text(encoding='utf-8'))
    version = pkg.get('devDependencies', {}).get('tailwindcss') or pkg.get('dependencies', {}).get('tailwindcss')
    assert version == '3.4.17'
