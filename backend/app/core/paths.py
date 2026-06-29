import tempfile
from pathlib import Path

from app.core.config import get_settings


class EvidencePathError(RuntimeError):
    pass


EVIDENCE_SUBDIRS = ('tool-runs', 'findings', 'artifacts')


def _writable_error(root: Path) -> EvidencePathError:
    return EvidencePathError(
        f'Evidence directory is not writable: {root}.\n'
        'The container should initialize it automatically. Check Docker volume permissions or EVIDENCE_DIR.'
    )


def ensure_evidence_dir_writable(root: Path | None = None) -> Path:
    if root is None:
        raw = get_settings().evidence_dir
        root = Path(raw).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        root = root.resolve()
    else:
        root = Path(root).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        root = root.resolve()

    if root == Path('/'):
        raise EvidencePathError('Refusing to use filesystem root as evidence directory')

    try:
        root.mkdir(parents=True, exist_ok=True)
        for child in EVIDENCE_SUBDIRS:
            (root / child).mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=root, delete=True) as f:
            f.write(b'ok')
            f.flush()
    except OSError as exc:
        raise _writable_error(root) from exc

    if not root.is_dir():
        raise EvidencePathError(f'Evidence path is not a directory: {root}')

    return root


def get_evidence_root(create: bool = True) -> Path:
    raw = get_settings().evidence_dir
    root = Path(raw).expanduser()

    if not root.is_absolute():
        root = Path.cwd() / root

    root = root.resolve()

    if root == Path('/'):
        raise EvidencePathError('Refusing to use filesystem root as evidence directory')

    if create:
        return ensure_evidence_dir_writable(root)

    if not root.exists():
        raise EvidencePathError(f'Evidence directory does not exist: {root}')

    if not root.is_dir():
        raise EvidencePathError(f'Evidence path is not a directory: {root}')

    return root


def safe_join_under_root(root: Path, *parts: str) -> Path:
    root = root.resolve()
    candidate = root.joinpath(*parts).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidencePathError('Refusing evidence path outside evidence root') from exc

    return candidate


def mission_evidence_dir(mission_id: str, *parts: str, create: bool = True) -> Path:
    root = get_evidence_root(create=create)
    path = safe_join_under_root(root, mission_id, *parts)

    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise _writable_error(root) from exc

    return path
