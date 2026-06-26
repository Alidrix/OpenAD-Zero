from pathlib import Path
from app.parsers.nmap_xml import parse_nmap_xml
from app.parsers.nuclei_jsonl import parse_nuclei_jsonl
from app.parsers.netexec_smb import parse_netexec_smb_output
FIX=Path('app/demo/fixtures')

def test_parse_nmap_sample():
    data=parse_nmap_xml(FIX/'sample_nmap.xml')
    assert len(data['hosts']) == 3
    assert any(s['port']==445 for h in data['hosts'] for s in h['services'])

def test_parse_nuclei_sample():
    rows=parse_nuclei_jsonl(FIX/'sample_nuclei.jsonl')
    assert rows and rows[0].template_id == 'http-missing-security-headers'
    assert rows[0].severity == 'low'

def test_parse_netexec_sample():
    text=(FIX/'sample_netexec.log').read_text()
    data=parse_netexec_smb_output(text)
    assert len(data['facts']) >= 2
    assert any(f.get('smb_signing_required') is False for f in data['facts'])
