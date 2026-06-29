from app.tool_automation.parsers import parse_tool_output


def test_parsers_core_ad_tools():
    samples = [
        ('kerbrute','kerbrute_userenum','[+] VALID USERNAME: alice@example.local'),
        ('impacket_sensitive','impacket_getnpusers','$krb5asrep$23$alice@example'),
        ('impacket_sensitive','impacket_getuserspns','MSSQLSvc/sql.example.local:1433'),
        ('gmsadumper','gmsadumper_assessment_password','gMSA svc$ msDS-ManagedPassword hash recovered'),
        ('donpapi','donpapi_collect_target','credential found in C:/Users/a/AppData'),
        ('coercer','coercer_check_single_target','MS-RPRN vulnerable'),
        ('bloodyad','bloodyad_get_acl','GenericAll on CN=Admin'),
        ('responder','responder_lab_capture','NTLMv2-SSP Hash captured from 10.0.0.5'),
        ('metasploit','metasploit_search_smb','exploit/windows/smb/ms17_010_eternalblue excellent check'),
    ]
    for tool, template, output in samples:
        assert parse_tool_output(tool, template, output, '10.0.0.5'), (tool, template)


def test_nmap_and_nuclei_parsers():
    assert parse_tool_output('nmap_safe_discovery','nmap_safe_discovery','445/tcp open microsoft-ds Windows Server','10.0.0.5')[0].parsed_fields['port'] == 445
    assert parse_tool_output('nuclei_safe_templates','nuclei_safe_templates','[CVE-2020-1472] [critical] target','10.0.0.5')[0].parsed_fields['cves'] == ['CVE-2020-1472']
