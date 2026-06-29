from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def test_controlled_exploit_tab_and_disabled_run_gates_visible():
    console = read('frontend/src/components/ToolConsole.tsx')
    controlled = read('frontend/src/components/MetasploitControlledExploit.tsx')
    assert "'Search','Check','Controlled Exploit'" in console
    assert 'Run controlled exploit' in controlled
    assert 'canRun=canPreview&&Boolean(preview&&hash)&&checkOk&&approved&&accepted&&finalConfirm' in controlled


def test_frontend_uses_allowlist_and_masks_preview():
    api = read('frontend/src/lib/api.ts')
    controlled = read('frontend/src/components/MetasploitControlledExploit.tsx')
    assert 'getMetasploitAllowlist' in api
    assert 'modules.map' in controlled
    assert 'maskCommand(preview,params)' in controlled
    assert "template_id:'metasploit_controlled_exploit_previewable'" in controlled
    assert 'command' not in controlled.split('previewToolCommand(')[1].split(')')[0]


def test_candidate_suggestions_are_not_directly_executable():
    panel = read('frontend/src/components/MetasploitSearchPanel.tsx')
    assert 'no generic exploit button is available' in panel
    assert 'runToolCommand' not in panel
