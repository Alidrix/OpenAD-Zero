from pathlib import Path

from app.core.config import get_settings


class EvidencePathError(RuntimeError):
    pass


def get_evidence_root(create: bool = True) -> Path:
    raw = get_settings().evidence_dir
    root = Path(raw).expanduser()

    if not root.is_absolute():
        root = Path.cwd() / root

    root = root.resolve()

    if root == Path('/'):
        raise EvidencePathError('Refusing to use filesystem root as evidence directory')

    if create:
        try:
            root.mkdir(parents=True, exist_ok=True)
            root.chmod(0o750)
        except PermissionError as exc:
            raise EvidencePathError(
                f'Evidence directory is not writable: {root}. '
                'Set EVIDENCE_DIR to a writable path.'
            ) from exc

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
        except PermissionError as exc:
            raise EvidencePathError(
                f'Evidence directory is not writable: {root}. '
                'Set EVIDENCE_DIR to a writable path.'
            ) from exc

    return path
