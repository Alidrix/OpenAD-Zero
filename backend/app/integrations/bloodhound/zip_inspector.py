import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

MAX_ENTRY_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 500 * 1024 * 1024
KNOWN = {'users', 'computers', 'groups', 'domains', 'ous', 'gpos', 'containers', 'sessions', 'certtemplates', 'cas'}


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def inspect_sharphound_zip(path: str | Path) -> dict:
    warnings = []
    json_files = []
    types = set()
    total = 0
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            if not infos:
                warnings.append('ZIP archive is empty')
            for info in infos:
                name = info.filename.replace('\\', '/')
                pp = PurePosixPath(name)
                if info.is_dir():
                    continue
                if pp.is_absolute() or '..' in pp.parts:
                    warnings.append('Potential path traversal entry detected')
                    continue
                total += info.file_size
                if info.file_size > MAX_ENTRY_BYTES:
                    warnings.append(f'Large ZIP entry detected: {name}')
                if name.lower().endswith('.json'):
                    json_files.append(name)
                    low = Path(name).stem.lower()
                    for k in KNOWN:
                        if k in low:
                            types.add(k)
                    try:
                        with z.open(info) as fh:
                            sample = fh.read(min(info.file_size, 1024 * 1024))
                            obj = json.loads(sample.decode('utf-8', errors='replace'))
                            meta = obj.get('meta') if isinstance(obj, dict) else None
                            if isinstance(meta, dict):
                                t = (meta.get('type') or meta.get('Type') or '').lower()
                                if t:
                                    types.add(t)
                    except Exception:
                        warnings.append(f'Malformed or oversized JSON sample: {name}')
            if not json_files:
                warnings.append('No JSON files found')
            if total > MAX_TOTAL_BYTES:
                warnings.append('Potential zip bomb: uncompressed size too large')
    except zipfile.BadZipFile:
        return {
            'valid': False,
            'json_files_count': 0,
            'file_types_detected': [],
            'total_uncompressed_size': 0,
            'warnings': ['Invalid ZIP archive'],
        }
    fatal = (
        any(
            w in warnings
            for w in ['No JSON files found', 'Potential path traversal entry detected', 'ZIP archive is empty']
        )
        or total > MAX_TOTAL_BYTES
        or any(w.startswith('Large ZIP entry') for w in warnings)
    )
    return {
        'valid': bool(json_files) and not fatal,
        'json_files_count': len(json_files),
        'file_types_detected': sorted(types),
        'total_uncompressed_size': total,
        'warnings': warnings,
    }
