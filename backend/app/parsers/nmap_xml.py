import xml.etree.ElementTree as ET
from pathlib import Path


def parse_nmap_xml(path: str | Path) -> dict:
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        raise ValueError(f'Invalid Nmap XML: {e}') from e
    hosts = []
    for h in root.findall('host'):
        status = h.find('status').get('state', 'unknown') if h.find('status') is not None else 'unknown'
        addr = h.find("address[@addrtype='ipv4']")
        if addr is None:
            addr = h.find('address')
        if addr is None:
            continue
        hn = ''
        hostnames = h.find('hostnames')
        if hostnames is not None:
            first = hostnames.find('hostname')
            if first is not None:
                hn = first.get('name', '')
        services = []
        ports = h.find('ports')
        if ports is not None:
            for p in ports.findall('port'):
                st = p.find('state')
                if st is None or st.get('state') != 'open':
                    continue
                svc = p.find('service')
                services.append(
                    {
                        'port': int(p.get('portid', '0')),
                        'protocol': p.get('protocol', 'tcp'),
                        'state': 'open',
                        'name': svc.get('name', '') if svc is not None else '',
                        'product': svc.get('product', '') if svc is not None else '',
                        'version': svc.get('version', '') if svc is not None else '',
                    }
                )
        hosts.append({'ip': addr.get('addr', ''), 'hostname': hn, 'status': status, 'services': services})
    return {'hosts': hosts}
