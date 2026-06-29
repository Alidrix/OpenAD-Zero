#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

REQUIRED_DIRS = [
    Path('/app/evidence'),
    Path('/app/evidence/tool-runs'),
    Path('/app/evidence/findings'),
    Path('/app/evidence/artifacts'),
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
    except OSError as exc:
        result['error'] = str(exc)
    return result


def main() -> int:
    checks = [check_dir(path) for path in REQUIRED_DIRS]
    print(json.dumps({'runtime_permissions': checks}, indent=2))
    return 0 if all(item['writable'] for item in checks) else 1


if __name__ == '__main__':
    sys.exit(main())
