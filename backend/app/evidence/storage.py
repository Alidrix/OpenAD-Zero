import hashlib, json, re
from pathlib import Path

class EvidenceStorageError(ValueError):
    pass

def sanitize_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise EvidenceStorageError('Filename is required')
    if '/' in filename or '\\' in filename or '..' in Path(filename).parts:
        raise EvidenceStorageError('Path traversal is not allowed')
    name=Path(filename).name.strip()
    safe=re.sub(r'[^A-Za-z0-9._ -]+','_',name).strip(' .')
    if not safe:
        raise EvidenceStorageError('Filename is invalid')
    return safe[:255]

def safe_extension(filename: str, allowed_extensions: set[str]) -> str:
    safe=sanitize_filename(filename)
    ext=Path(safe).suffix.lower()
    allowed={e.lower() if e.startswith('.') else f'.{e.lower()}' for e in allowed_extensions}
    if not ext or ext not in allowed:
        raise EvidenceStorageError('Extension is not allowed')
    return ext

def compute_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def write_metadata(base: Path, metadata: dict) -> None:
    base.mkdir(parents=True, exist_ok=True)
    (base/'metadata.json').write_text(json.dumps(metadata, indent=2, default=str), encoding='utf-8')
