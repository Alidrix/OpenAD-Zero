#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

EXPECTED_UID = int(os.environ.get('APP_UID', '10001'))
EXPECTED_GID = int(os.environ.get('APP_GID', '10001'))

REQUIRED_DIRS = [
    Path('/app/evidence'),
    Path('/app/evidence/tool-runs'),
    Path('/app/evidence/findings'),
    Path('/app/evidence/artifacts'),
    Path('/app/runtime'),
    Path('/app/runtime/home'),
    Path('/app/runtime/home/.nxc'),
    Path('/app/runtime/config'),
    Path('/app/runtime/config/nuclei'),
    Path('/app/runtime/cache'),
    Path('/app/runtime/data'),
    Path('/app/runtime/tmp'),
]


def check_dir(path: Path) -> dict[str, object]:
    result: dict[str, object] = {'path': str(path), 'exists': path.exists(), 'writable': False}
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f'.openadzero-permissions-{uuid4().hex}'
        probe.write_text('ok', encoding='utf-8')
        probe.unlink(missing_ok=True)
        result['exists'] = True
        result['writable'] = True
        stat = path.stat()
        result['uid'] = stat.st_uid
        result['gid'] = stat.st_gid
    except OSError as exc:
        result['error'] = str(exc)
    return result


def main() -> int:
    runtime = {
        'uid': os.getuid(),
        'gid': os.getgid(),
        'expected_uid': EXPECTED_UID,
        'expected_gid': EXPECTED_GID,
        'uid_matches': os.getuid() == EXPECTED_UID,
        'gid_matches': os.getgid() == EXPECTED_GID,
    }
    checks = [check_dir(path) for path in REQUIRED_DIRS]
    identity_required = any(path.is_absolute() and path.parts[:2] == ('/', 'app') for path in REQUIRED_DIRS)
    runtime['identity_required'] = identity_required
    payload = {'runtime_identity': runtime, 'runtime_permissions': checks}
    print(json.dumps(payload, indent=2))
    identity_ok = (runtime['uid_matches'] and runtime['gid_matches']) or not identity_required
    ok = identity_ok and all(item['writable'] for item in checks)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
