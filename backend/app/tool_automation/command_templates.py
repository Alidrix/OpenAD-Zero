"""Executable command templates for the Tool Automation Library.

Templates are argv lists only. The backend reconstructs commands from these
allowlisted templates; no raw shell commands are accepted.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandTemplate:
    id: str
    tool_id: str
    name: str
    description: str
    argv: list[str]
    required_params: list[str]
    optional_params: list[str]
    parser: str
    risk_level: str = "low"
    output_artifact_type: str | None = None


COMMAND_TEMPLATE_DEFINITIONS: dict[str, CommandTemplate] = {
    "nmap_safe_discovery": CommandTemplate("nmap_safe_discovery", "nmap_safe_discovery", "Nmap safe discovery", "Lightweight service/version discovery against one validated target.", ["nmap", "-sV", "--version-light", "{target}"], ["target"], [], "nmap", "low", "scan"),
    "netexec_smb_fingerprint": CommandTemplate("netexec_smb_fingerprint", "netexec_smb_fingerprint", "NetExec SMB fingerprint", "Read-only SMB fingerprinting.", ["nxc", "smb", "{target}", "--shares", "--no-bruteforce"], ["target"], [], "netexec", "low", "smb"),
    "netexec_smb_signing_check": CommandTemplate("netexec_smb_signing_check", "netexec_smb_signing_check", "NetExec SMB signing", "Generate a relay list for SMB signing state review.", ["nxc", "smb", "{target}", "--gen-relay-list", "{output}"], ["target", "output"], [], "netexec", "low", "smb"),
    "netexec_smb_null_session_check": CommandTemplate("netexec_smb_null_session_check", "netexec_smb_null_session_check", "NetExec null session", "Check null-session exposure without brute force.", ["nxc", "smb", "{target}", "-u", "", "-p", ""], ["target"], [], "netexec", "low", "smb"),
    "nuclei_safe_templates": CommandTemplate("nuclei_safe_templates", "nuclei_safe_templates", "Nuclei safe templates", "Run the curated safe template directory only.", ["nuclei", "-target", "{target}", "-t", "nuclei-templates-safe/"], ["target"], [], "nuclei", "low", "scan"),
    "enum4linux_ng_basic": CommandTemplate("enum4linux_ng_basic", "enum4linux_ng_basic", "enum4linux-ng basic", "Basic read-only SMB enumeration with JSON output.", ["enum4linux-ng", "-A", "-oJ", "{output}", "{target}"], ["target", "output"], [], "enum4linux", "low", "json"),
    "bloodhound_sharphound_upload": CommandTemplate("bloodhound_sharphound_upload", "bloodhound_sharphound_upload", "BloodHound upload", "Import an existing SharpHound archive for path analysis.", ["bloodhound-import", "{artifact}"], ["artifact"], [], "bloodhound", "low", "bloodhound"),
    "bloodhound_explorer": CommandTemplate("bloodhound_explorer", "bloodhound_explorer", "BloodHound explorer", "Explore already-imported BloodHound data.", ["bloodhound-query", "explore", "{query}"], ["query"], [], "bloodhound", "low", "bloodhound"),
    "bloodhound_pathfinding": CommandTemplate("bloodhound_pathfinding", "bloodhound_pathfinding", "BloodHound pathfinding", "Find paths in already-imported BloodHound data.", ["bloodhound-query", "path", "--from", "{source}", "--to", "{target}"], ["source", "target"], [], "bloodhound", "low", "bloodhound_path"),
    "kerbrute_userenum": CommandTemplate("kerbrute_userenum", "kerbrute", "Kerbrute userenum", "Enumerate valid users via Kerberos pre-auth responses.", ["kerbrute", "userenum", "--dc", "{dc_ip}", "-d", "{domain}", "{userlist}"], ["dc_ip", "domain", "userlist"], [], "kerbrute", "high", "users"),
    "kerbrute_passwordspray_safe_preview": CommandTemplate("kerbrute_passwordspray_safe_preview", "kerbrute", "Kerbrute password spray preview", "Account-lockout risk: password spraying requires reinforced human validation.", ["kerbrute", "passwordspray", "--dc", "{dc_ip}", "-d", "{domain}", "{userlist}", "{password}"], ["dc_ip", "domain", "userlist", "password"], [], "kerbrute", "high", "users"),
    "gmsadumper_assessment_password": CommandTemplate("gmsadumper_assessment_password", "gmsadumper", "gMSADumper password", "Assess readable gMSA secrets using a password.", ["python3", "gMSADumper.py", "-u", "{username}", "-p", "{password}", "-d", "{domain}", "-l", "{dc_ip}"], ["username", "password", "domain", "dc_ip"], [], "gmsadumper", "high", "credential_artifact"),
    "gmsadumper_assessment_hash": CommandTemplate("gmsadumper_assessment_hash", "gmsadumper", "gMSADumper hash", "Assess readable gMSA secrets using an NTLM hash.", ["python3", "gMSADumper.py", "-u", "{username}", "-H", "{ntlm_hash}", "-d", "{domain}", "-l", "{dc_ip}"], ["username", "ntlm_hash", "domain", "dc_ip"], [], "gmsadumper", "high", "credential_artifact"),
    "donpapi_collect_target": CommandTemplate("donpapi_collect_target", "donpapi", "DonPAPI target collect", "Bounded DPAPI/credential artifact collection for one target.", ["DonPAPI", "collect", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "--target", "{target}", "-o", "{output}"], ["domain", "username", "password", "target", "output"], [], "donpapi", "high", "credential_artifact"),
    "donpapi_collect_target_hash": CommandTemplate("donpapi_collect_target_hash", "donpapi", "DonPAPI target collect hash", "Bounded DPAPI/credential artifact collection for one target using a hash.", ["DonPAPI", "collect", "-d", "{domain}", "-u", "{username}", "-H", "{ntlm_hash}", "--target", "{target}", "-o", "{output}"], ["domain", "username", "ntlm_hash", "target", "output"], [], "donpapi", "high", "credential_artifact"),
    "coercer_check_single_target": CommandTemplate("coercer_check_single_target", "coercer", "Coercer single target", "Check coercion methods against one target and explicit listener.", ["coercer", "coerce", "-t", "{target}", "-l", "{listener}", "-d", "{domain}", "-u", "{username}", "-p", "{password}"], ["target", "listener", "domain", "username", "password"], [], "coercer", "high", "coercion"),
    "coercer_list_methods": CommandTemplate("coercer_list_methods", "coercer", "Coercer list methods", "List supported coercion methods without targeting hosts.", ["coercer", "list"], [], [], "coercer", "high", "coercion"),
    "bloodyad_get_object": CommandTemplate("bloodyad_get_object", "bloodyad", "BloodyAD get object", "Read an AD object.", ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "object", "{object}"], ["dc_ip", "domain", "username", "password", "object"], [], "bloodyad", "high", "ad_object"),
    "bloodyad_get_membership": CommandTemplate("bloodyad_get_membership", "bloodyad", "BloodyAD get membership", "Read AD memberships.", ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "membership", "{object}"], ["dc_ip", "domain", "username", "password", "object"], [], "bloodyad", "high", "membership"),
    "bloodyad_get_children": CommandTemplate("bloodyad_get_children", "bloodyad", "BloodyAD get children", "Read AD child objects.", ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "children", "{object}"], ["dc_ip", "domain", "username", "password", "object"], [], "bloodyad", "high", "ad_object"),
    "bloodyad_get_acl": CommandTemplate("bloodyad_get_acl", "bloodyad", "BloodyAD get ACL", "Read AD ACLs only; no write templates are provided.", ["bloodyAD", "--host", "{dc_ip}", "-d", "{domain}", "-u", "{username}", "-p", "{password}", "get", "acl", "{object}"], ["dc_ip", "domain", "username", "password", "object"], [], "bloodyad", "high", "acl"),
    "impacket_getnpusers": CommandTemplate("impacket_getnpusers", "impacket_sensitive", "GetNPUsers unauth", "Collect AS-REP roastable users from a users file.", ["GetNPUsers.py", "{domain}/", "-usersfile", "{userlist}", "-dc-ip", "{dc_ip}", "-outputfile", "{output}"], ["domain", "userlist", "dc_ip", "output"], [], "impacket_getnpusers", "high", "asrep"),
    "impacket_getnpusers_auth": CommandTemplate("impacket_getnpusers_auth", "impacket_sensitive", "GetNPUsers auth", "Request AS-REP material with valid credentials.", ["GetNPUsers.py", "{domain}/{username}:{password}", "-dc-ip", "{dc_ip}", "-request", "-outputfile", "{output}"], ["domain", "username", "password", "dc_ip", "output"], [], "impacket_getnpusers", "high", "asrep"),
    "impacket_getuserspns": CommandTemplate("impacket_getuserspns", "impacket_sensitive", "GetUserSPNs", "Collect Kerberoastable SPN material.", ["GetUserSPNs.py", "{domain}/{username}:{password}", "-dc-ip", "{dc_ip}", "-outputfile", "{output}"], ["domain", "username", "password", "dc_ip", "output"], [], "impacket_getuserspns", "high", "spn"),
    "impacket_lookupsid": CommandTemplate("impacket_lookupsid", "impacket_sensitive", "LookupSID", "Enumerate domain SID information.", ["lookupsid.py", "{domain}/{username}:{password}@{target}"], ["domain", "username", "password", "target"], [], "impacket_lookupsid", "high", "sid"),
    "impacket_smbclient_list": CommandTemplate("impacket_smbclient_list", "impacket_sensitive", "smbclient list", "List SMB shares.", ["smbclient.py", "{domain}/{username}:{password}@{target}", "-list"], ["domain", "username", "password", "target"], [], "impacket_smbclient", "high", "share"),
    "impacket_rpcdump": CommandTemplate("impacket_rpcdump", "impacket_sensitive", "rpcdump", "List RPC endpoints.", ["rpcdump.py", "{domain}/{username}:{password}@{target}"], ["domain", "username", "password", "target"], [], "impacket_rpcdump", "high", "service"),
    "impacket_samrdump": CommandTemplate("impacket_samrdump", "impacket_sensitive", "samrdump", "Enumerate SAMR users/groups when visible.", ["samrdump.py", "{domain}/{username}:{password}@{target}"], ["domain", "username", "password", "target"], [], "impacket_samrdump", "high", "user"),
    "responder_analyze": CommandTemplate("responder_analyze", "responder", "Responder analyze", "Analyze traffic without poisoning.", ["responder", "-I", "{interface}", "-A"], ["interface"], [], "responder", "high", "captured_hash"),
    "responder_lab_capture": CommandTemplate("responder_lab_capture", "responder", "Responder lab capture", "Capture traffic in an authorized LAB on an explicitly selected interface.", ["responder", "-I", "{interface}", "-wrf"], ["interface"], [], "responder", "high", "captured_hash"),
    "metasploit_db_status": CommandTemplate("metasploit_db_status", "metasploit", "Metasploit DB status", "Show Metasploit database status.", ["msfconsole", "-q", "-x", "db_status; exit"], [], [], "metasploit", "high", "metasploit"),
    "metasploit_search_by_cve": CommandTemplate("metasploit_search_by_cve", "metasploit", "Search by CVE", "Search Metasploit modules by CVE.", ["msfconsole", "-q", "-x", "search cve:{cve}; exit"], ["cve"], [], "metasploit", "high", "metasploit_module"),
    "metasploit_search_by_service": CommandTemplate("metasploit_search_by_service", "metasploit", "Search by service", "Search Metasploit modules by service name.", ["msfconsole", "-q", "-x", "search name:{service}; exit"], ["service"], [], "metasploit", "high", "metasploit_module"),
    "metasploit_search_by_platform_windows": CommandTemplate("metasploit_search_by_platform_windows", "metasploit", "Search Windows keyword", "Search Windows modules by keyword.", ["msfconsole", "-q", "-x", "search platform:windows name:{keyword}; exit"], ["keyword"], [], "metasploit", "high", "metasploit_module"),
    "metasploit_search_smb": CommandTemplate("metasploit_search_smb", "metasploit", "Search SMB", "Search Windows SMB modules.", ["msfconsole", "-q", "-x", "search type:auxiliary type:exploit platform:windows smb; exit"], [], [], "metasploit", "high", "metasploit_module"),
    "metasploit_search_ldap": CommandTemplate("metasploit_search_ldap", "metasploit", "Search LDAP", "Search Windows LDAP modules.", ["msfconsole", "-q", "-x", "search ldap platform:windows; exit"], [], [], "metasploit", "high", "metasploit_module"),
    "metasploit_search_kerberos": CommandTemplate("metasploit_search_kerberos", "metasploit", "Search Kerberos", "Search Windows Kerberos modules.", ["msfconsole", "-q", "-x", "search kerberos platform:windows; exit"], [], [], "metasploit", "high", "metasploit_module"),
    "metasploit_info_module": CommandTemplate("metasploit_info_module", "metasploit", "Module info", "Show module information only.", ["msfconsole", "-q", "-x", "info {module}; exit"], ["module"], [], "metasploit_info", "high", "metasploit_module"),
    "metasploit_check_ms17_010": CommandTemplate("metasploit_check_ms17_010", "metasploit", "Check MS17-010", "Run the explicitly allowed non-destructive MS17-010 check.", ["msfconsole", "-q", "-x", "use auxiliary/scanner/smb/smb_ms17_010; set RHOSTS {target}; check; exit"], ["target"], [], "metasploit_check", "high", "vulnerability"),
    "metasploit_smb_version": CommandTemplate("metasploit_smb_version", "metasploit", "SMB version scanner", "Run the auxiliary SMB version scanner only.", ["msfconsole", "-q", "-x", "use auxiliary/scanner/smb/smb_version; set RHOSTS {target}; run; exit"], ["target"], [], "metasploit_check", "high", "service"),
}

COMMAND_TEMPLATES: dict[str, list[str]] = {k: v.argv for k, v in COMMAND_TEMPLATE_DEFINITIONS.items()}
