from pathlib import Path
from app.parsers.nmap_xml import parse_nmap_xml
from app.parsers.nuclei_jsonl import parse_nuclei_jsonl
from app.parsers.netexec_smb import parse_netexec_smb_output

FIXTURES=Path('app/demo/fixtures')

def test_parse_nmap_sample():
    data=parse_nmap_xml(FIXTURES/'sample_nmap.xml')
    assert len(data['hosts']) == 3
    assert any(h['ip']=='192.168.56.10' and len(h['services']) >= 4 for h in data['hosts'])

def test_parse_nuclei_sample():
    findings=parse_nuclei_jsonl(FIXTURES/'sample_nuclei.jsonl')
    assert len(findings) == 1
    assert findings[0].template_id == 'exposed-panel'
    assert findings[0].severity == 'medium'

def test_parse_netexec_sample():
    data=parse_netexec_smb_output((FIXTURES/'sample_netexec.log').read_text())
    assert len(data['facts']) == 2
    assert any(f['domain']=='LAB.LOCAL' for f in data['facts'])
    assert any(f['ip']=='192.168.56.20' and f['smb_signing_required'] is False for f in data['facts'])
