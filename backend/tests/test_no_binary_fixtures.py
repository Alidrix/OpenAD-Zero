from pathlib import Path

FIXTURE_ROOT = Path(__file__).parent / 'fixtures/normalization'
TEXT_EXTENSIONS = {'.json', '.jsonl', '.xml', '.log', '.txt', '.md'}
BANNED_EXTENSIONS = {
    '.zip',
    '.bin',
    '.dat',
    '.sqlite',
    '.db',
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.pdf',
    '.7z',
    '.tar',
    '.gz',
}


def test_normalization_fixtures_are_text_only():
    offenders: list[str] = []
    for path in sorted(p for p in FIXTURE_ROOT.rglob('*') if p.is_file()):
        suffix = path.suffix.lower()
        if suffix in BANNED_EXTENSIONS or suffix not in TEXT_EXTENSIONS:
            offenders.append(str(path.relative_to(FIXTURE_ROOT)))
            continue
        data = path.read_bytes()
        if b'\x00' in data:
            offenders.append(str(path.relative_to(FIXTURE_ROOT)))
            continue
        try:
            data.decode('utf-8')
        except UnicodeDecodeError:
            offenders.append(str(path.relative_to(FIXTURE_ROOT)))
    assert offenders == []
