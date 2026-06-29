from __future__ import annotations

import re
from app.tool_automation.results import ParsedFinding, make_finding
from app.tool_automation.metasploit_allowlist import mask_metasploit_secrets


def parse_tool_output(tool_id: str, template_id: str, output: str, target: str | None = None, artifact_path: str | None = None) -> list[ParsedFinding]:
    name = template_id.lower()
    if "kerbrute" in name: return parse_kerbrute(output, tool_id, template_id, target)
    if "getnpusers" in name: return parse_impacket_getnpusers(output, tool_id, template_id, target, artifact_path)
    if "getuserspns" in name: return parse_impacket_getuserspns(output, tool_id, template_id, target, artifact_path)
    if "lookupsid" in name or "samrdump" in name: return parse_identity_lines(output, tool_id, template_id, target)
    if "smbclient" in name: return parse_smbclient(output, tool_id, template_id, target)
    if "gmsadumper" in name: return parse_gmsadumper(output, tool_id, template_id, target, artifact_path)
    if "donpapi" in name: return parse_donpapi(output, tool_id, template_id, target, artifact_path)
    if "coercer" in name: return parse_coercer(output, tool_id, template_id, target)
    if "bloodyad" in name: return parse_bloodyad(output, tool_id, template_id, target)
    if "responder" in name: return parse_responder(output, tool_id, template_id, target, artifact_path)
    if "metasploit" in name: return parse_metasploit(output, tool_id, template_id, target)
    if "nmap" in name: return parse_nmap(output, tool_id, template_id, target)
    if "nuclei" in name: return parse_nuclei(output, tool_id, template_id, target)
    return []


def parse_kerbrute(output, tool_id="kerbrute", template_id="kerbrute_userenum", target=None):
    findings=[]
    for line in output.splitlines():
        if "VALID USERNAME" in line.upper() or "VALID LOGIN" in line.upper():
            user = line.split()[-1]
            findings.append(make_finding(tool_id, template_id, target, "user", "info", f"Valid Kerberos user {user}", "Kerbrute reported a valid user.", line, {"username": user}))
        if "LOCKED" in line.upper():
            findings.append(make_finding(tool_id, template_id, target, "user", "high", "Potential account lockout", "Kerbrute output indicates a locked account.", line, {"locked": True}))
        if "ERROR" in line.upper() or "KDC_ERR" in line.upper():
            findings.append(make_finding(tool_id, template_id, target, "domain", "medium", "Kerbrute domain/DC error", "Kerbrute reported a domain or DC error.", line, {"error": line}))
    m=re.search(r"(\d+)\s+valid", output, re.I)
    if m: findings.append(make_finding(tool_id, template_id, target, "user", "info", "Kerbrute statistics", "Kerbrute summary statistics.", m.group(0), {"valid_users": int(m.group(1))}))
    return findings


def parse_impacket_getnpusers(output, tool_id="impacket_sensitive", template_id="impacket_getnpusers", target=None, artifact_path=None):
    return [make_finding(tool_id, template_id, target, "asrep", "high", "AS-REP roastable hash", "Impacket GetNPUsers produced AS-REP material.", l, {"hash_type": "krb5asrep", "masked": True}, artifact_path) for l in output.splitlines() if "$krb5asrep$" in l.lower()]

def parse_impacket_getuserspns(output, tool_id="impacket_sensitive", template_id="impacket_getuserspns", target=None, artifact_path=None):
    fs=[]
    for l in output.splitlines():
        if "$krb5tgs$" in l.lower() or re.search(r"\b[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", l):
            fs.append(make_finding(tool_id, template_id, target, "spn", "high", "Kerberoastable SPN", "Impacket GetUserSPNs identified SPN material.", l, {"masked": "$krb5tgs$" in l.lower()}, artifact_path))
    return fs

def parse_identity_lines(output, tool_id, template_id, target=None):
    fs=[]
    for l in output.splitlines():
        if "SidTypeUser" in l or re.search(r"\buser\b", l, re.I): fs.append(make_finding(tool_id, template_id, target, "user", "info", "SAMR/LookupSID user", "Identity enumeration output.", l, {"line": l}))
        elif "SidTypeGroup" in l or re.search(r"\bgroup\b", l, re.I): fs.append(make_finding(tool_id, template_id, target, "group", "info", "SAMR/LookupSID group", "Identity enumeration output.", l, {"line": l}))
    return fs

def parse_smbclient(output, tool_id, template_id, target=None):
    return [make_finding(tool_id, template_id, target, "share", "info", f"SMB share {m.group(1)}", "smbclient listed a share.", l, {"share": m.group(1)}) for l in output.splitlines() for m in [re.search(r"^\s*([A-Za-z0-9_$.-]+)\s+(Disk|IPC|Printer)", l)] if m]

def parse_gmsadumper(output, tool_id="gmsadumper", template_id="gmsadumper_assessment_password", target=None, artifact_path=None):
    fs=[]
    for l in output.splitlines():
        if "gmsa" in l.lower() or "msds-managedpassword" in l.lower(): fs.append(make_finding(tool_id, template_id, target, "gmsa", "high", "gMSA finding", "gMSADumper reported a gMSA account or secret access result.", l, {"secret_recoverable": "hash" in l.lower() or "password" in l.lower()}, artifact_path))
        if "denied" in l.lower(): fs.append(make_finding(tool_id, template_id, target, "gmsa", "low", "gMSA access denied", "gMSADumper reported denied access.", l, {"access_denied": True}, artifact_path))
    return fs

def parse_donpapi(output, tool_id="donpapi", template_id="donpapi_collect_target", target=None, artifact_path=None):
    fs=[]
    for l in output.splitlines():
        if any(x in l.lower() for x in ["credential", "secret", "password", "masterkey", "cookie"]): fs.append(make_finding(tool_id, template_id, target, "credential_artifact", "high", "Credential artifact detected", "DonPAPI reported a credential artifact; values must be masked in UI.", l, {"masked": True}, artifact_path))
        elif "denied" in l.lower(): fs.append(make_finding(tool_id, template_id, target, "credential_artifact", "low", "DonPAPI access denied", "Access denied during collection.", l, {"access_denied": True}, artifact_path))
    return fs

def parse_coercer(output, tool_id="coercer", template_id="coercer_check_single_target", target=None):
    fs=[]
    for l in output.splitlines():
        if any(x in l.lower() for x in ["vulnerable", "success", "coerce"]): fs.append(make_finding(tool_id, template_id, target, "coercion", "high" if "vulnerable" in l.lower() else "medium", "Possible coercion method", "Coercer reported a possible method/status.", l, {"method": l.split()[0] if l.split() else l}))
        elif "rpc" in l.lower() or "smb" in l.lower(): fs.append(make_finding(tool_id, template_id, target, "service", "info", "Coercer service status", "Coercer reported service/RPC status.", l, {"line": l}))
    return fs

def parse_bloodyad(output, tool_id="bloodyad", template_id="bloodyad_get_object", target=None):
    fs=[]
    for l in output.splitlines():
        low=l.lower()
        cat="acl" if any(x in low for x in ["genericall", "writeowner", "writedacl", "allowedtoact"]) else "group" if "member" in low else "computer" if "$" in l else "domain"
        if l.strip(): fs.append(make_finding(tool_id, template_id, target, cat, "medium" if cat=="acl" else "info", "BloodyAD parsed result", "BloodyAD read-oriented output.", l, {"line": l}))
    return fs

def parse_responder(output, tool_id="responder", template_id="responder_analyze", target=None, artifact_path=None):
    fs=[]
    for l in output.splitlines():
        if "hash" in l.lower() or "ntlm" in l.lower(): fs.append(make_finding(tool_id, template_id, target, "captured_hash", "high", "Captured hash indicator", "Responder reported a captured hash or NTLM event.", l, {"masked": True}, artifact_path))
        elif re.search(r"LLMNR|NBT-NS|MDNS|SMB", l, re.I): fs.append(make_finding(tool_id, template_id, target, "service", "info", "Responder protocol event", "Responder observed a protocol event.", l, {"protocol": l.split()[0] if l.split() else l}, artifact_path))
    return fs

def parse_metasploit(output, tool_id="metasploit", template_id="metasploit_search_by_service", target=None):
    fs=[]
    controlled = "controlled_exploit" in template_id
    for l in output.splitlines():
        safe_line = mask_metasploit_secrets(l)
        m=re.search(r"\b((auxiliary|exploit)/\S+)", l)
        if m:
            fs.append(make_finding(tool_id, template_id, target, "metasploit_module", "info", f"Metasploit module {m.group(1)}", "Metasploit output identified a module.", safe_line, {"module": m.group(1), "type": m.group(2), "check_supported": "check" in l.lower()}))
        elif "appears" in l.lower() or "vulnerable" in l.lower():
            fs.append(make_finding(tool_id, template_id, target, "metasploit_check", "high", "Metasploit check result", "Metasploit check reported a vulnerability indicator.", safe_line, {"check_result": safe_line, "vulnerable": True}))
            fs.append(make_finding(tool_id, template_id, target, "vulnerability", "high", "Metasploit vulnerability indicator", "Metasploit reported a vulnerable status.", safe_line, {"vulnerable": True}))
        elif "not exploitable" in l.lower() or "not vulnerable" in l.lower() or "safe" in l.lower():
            fs.append(make_finding(tool_id, template_id, target, "metasploit_check", "info", "Metasploit non-vulnerable result", "Metasploit did not report a vulnerable status.", safe_line, {"vulnerable": False}))
        elif re.search(r"Command shell session\s+(\d+)\s+opened|Meterpreter session\s+(\d+)\s+opened", l, re.I):
            sid = next(x for x in re.search(r"session\s+(\d+)\s+opened", l, re.I).groups() if x)
            fs.append(make_finding(tool_id, template_id, target, "metasploit_session", "critical", f"Metasploit session {sid} opened", "Controlled exploit output reported an opened session.", safe_line, {"session_opened": True, "session_id": sid}))
        elif controlled and any(x in l.lower() for x in ["exploit", "run", "error", "failed"]):
            fs.append(make_finding(tool_id, template_id, target, "metasploit_controlled_exploit", "critical" if "opened" in l.lower() else "medium", "Controlled Metasploit exploit output", "Parsed controlled exploit status/error output.", safe_line, {"status": safe_line, "error": "error" in l.lower() or "failed" in l.lower()}))
    return fs

def parse_nmap(output, tool_id="nmap_safe_discovery", template_id="nmap_safe_discovery", target=None):
    fs=[]
    for l in output.splitlines():
        m=re.search(r"^(\d+)/(tcp|udp)\s+open\s+(\S+)(?:\s+(.*))?", l)
        if m: fs.append(make_finding(tool_id, template_id, target, "service", "info", f"Open {m.group(3)} on {m.group(1)}", "Nmap reported an open service.", l, {"port": int(m.group(1)), "protocol": m.group(2), "service": m.group(3), "version": (m.group(4) or "").strip()}))
    return fs

def parse_nuclei(output, tool_id="nuclei_safe_templates", template_id="nuclei_safe_templates", target=None):
    fs=[]
    for l in output.splitlines():
        cves=re.findall(r"CVE-\d{4}-\d{4,7}", l, re.I)
        if cves or "[" in l: fs.append(make_finding(tool_id, template_id, target, "vulnerability", "medium", "Nuclei finding", "Nuclei reported a finding.", l, {"cves": cves}))
    return fs
