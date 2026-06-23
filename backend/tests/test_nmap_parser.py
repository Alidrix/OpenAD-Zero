from pathlib import Path
import pytest
from app.parsers.nmap_xml import parse_nmap_xml
def test_parse_sample():
    data=parse_nmap_xml(Path(__file__).parent/'fixtures/nmap_sample.xml')
    assert len(data['hosts'])==2
    h=data['hosts'][0]
    assert h['ip']=='192.168.1.10' and h['hostname']=='DC01'
    assert len(h['services'])==2
    assert h['services'][0]['name']=='kerberos'
    assert h['services'][0]['product']=='Microsoft Windows Kerberos'
    assert h['services'][0]['version']=='10'
def test_invalid_xml(tmp_path):
    p=tmp_path/'bad.xml'; p.write_text('<bad')
    with pytest.raises(ValueError): parse_nmap_xml(p)
