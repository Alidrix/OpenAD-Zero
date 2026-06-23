from app.parsers.netexec_smb import parse_netexec_smb_output

def test_empty_output():
    assert parse_netexec_smb_output('') == {'facts': [], 'shares': []}

def test_parse_fingerprint_signing_and_smbv1():
    text = 'SMB 192.168.1.10 445 DC01 [*] Windows Server 2019 (domain:LAB.LOCAL) (signing:True) (SMBv1:False)\n'
    result = parse_netexec_smb_output(text)
    fact = result['facts'][0]
    assert fact['ip'] == '192.168.1.10'
    assert fact['hostname'] == 'DC01'
    assert fact['domain'] == 'LAB.LOCAL'
    assert fact['os'] == 'Windows Server 2019'
    assert fact['smb_signing_required'] is True
    assert fact['smbv1_enabled'] is False

def test_parse_signing_false_null_session_and_share():
    text = '''invalid line
SMB 192.168.1.20 445 FILE01 Windows 10 (signing:False) (SMBv1:False)
SMB 192.168.1.20 445 FILE01 [+] Null session possible
SMB 192.168.1.20 445 FILE01 IPC$ READ Remote IPC
'''
    result = parse_netexec_smb_output(text)
    fact = result['facts'][0]
    assert fact['smb_signing_required'] is False
    assert fact['smbv1_enabled'] is False
    assert fact['null_session_possible'] is True
    assert result['shares'][0]['name'] == 'IPC$'
    assert result['shares'][0]['access'] == 'READ'
