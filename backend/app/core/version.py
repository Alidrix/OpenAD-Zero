from pathlib import Path

DEFAULT_VERSION = '0.1.0-rc1'


def get_app_version() -> str:
    candidates = [
        Path(__file__).resolve().parents[3] / 'VERSION',
        Path.cwd() / 'VERSION',
        Path.cwd().parent / 'VERSION',
    ]

    for candidate in candidates:
        if candidate.exists():
            value = candidate.read_text(encoding='utf-8').strip()
            if value:
                return value

    return DEFAULT_VERSION
