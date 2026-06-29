"""Executable command templates for the Tool Automation Library.

Templates are argv lists only. The backend reconstructs commands from these
allowlisted templates; no raw shell commands are accepted.
"""

COMMAND_TEMPLATES: dict[str, list[str]] = {
    "nmap_safe_discovery": ["nmap", "-sV", "--version-light", "{target}"],
    "netexec_smb_fingerprint": ["nxc", "smb", "{target}", "--shares", "--no-bruteforce"],
    "netexec_smb_signing_check": ["nxc", "smb", "{target}", "--gen-relay-list", "{output}"],
    "netexec_smb_null_session_check": ["nxc", "smb", "{target}", "-u", "", "-p", ""],
    "nuclei_safe_templates": ["nuclei", "-target", "{target}", "-t", "nuclei-templates-safe/"],
    "enum4linux_ng_basic": ["enum4linux-ng", "-A", "-oJ", "{output}", "{target}"],
    "kerbrute_userenum": ["kerbrute", "userenum", "--dc", "{dc_ip}", "-d", "{domain}", "{userlist}"],
    "gmsadumper_assessment": ["python3", "gMSADumper.py", "-u", "{username}", "-p", "{password}", "-d", "{domain}", "-l", "{dc_ip}"],
    "donpapi_collect_authorized": ["DonPAPI", "collect", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "--target", "{target}", "-o", "{output}"],
    "coercer_check": ["coercer", "coerce", "-t", "{target}", "-l", "{listener}", "-d", "{domain}", "-u", "{username}", "-p", "{password}"],
    "bloodyad_get_object": ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "object", "{object}"],
    "bloodyad_get_membership": ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "membership", "{object}"],
    "responder_analyze": ["responder", "-I", "{interface}", "-A"],
    "impacket_getnpusers": ["GetNPUsers.py", "{domain}/", "-usersfile", "{userlist}", "-dc-ip", "{dc_ip}", "-outputfile", "{output}"],
    "impacket_getuserspns": ["GetUserSPNs.py", "{domain}/{username}:{password}", "-dc-ip", "{dc_ip}", "-outputfile", "{output}"],
    "impacket_lookupsid": ["lookupsid.py", "{domain}/{username}:{password}@{target}"],
    "impacket_smbclient_list": ["smbclient.py", "{domain}/{username}:{password}@{target}", "-list"],
}
