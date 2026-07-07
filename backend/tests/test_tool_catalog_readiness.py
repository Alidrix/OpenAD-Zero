import socket
import subprocess

from app.tool_catalog.readiness import tool_readiness


def test_readiness_uses_which_only(monkeypatch):
    called = []
    monkeypatch.setattr('shutil.which', lambda binary: called.append(binary) or None)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('subprocess used')))
    monkeypatch.setattr(
        socket, 'create_connection', lambda *a, **kw: (_ for _ in ()).throw(AssertionError('network used'))
    )
    rows = tool_readiness()
    assert rows
    assert called
    assert all('version' in row and row['version'] is None for row in rows)
