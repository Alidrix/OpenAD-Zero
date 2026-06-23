import re
from typing import Any
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

def _clean(line: str) -> str:
    return ANSI_RE.sub("", line).strip()

def _bool_after(line: str, key: str) -> bool | None:
    m = re.search(rf"{key}\s*[:=]\s*(True|False|Yes|No|Required|Disabled|Enabled|Not required)", line, re.I)
    if not m: return None
    val = m.group(1).lower()
    return val in {"true", "yes", "required", "enabled"}

def parse_netexec_smb_output(text: str) -> dict[str, list[dict[str, Any]]]:
    facts_by_ip: dict[str, dict[str, Any]] = {}
    shares: list[dict[str, Any]] = []
    current_ip: str | None = None
    for raw in text.splitlines():
        line = _clean(raw)
        if not line or line.upper().startswith(("WARNING", "ERROR")) or "SMB" not in line.upper():
            continue
        ip_match = IP_RE.search(line)
        ip = ip_match.group(0) if ip_match else current_ip
        if not ip:
            continue
        current_ip = ip
        fact = facts_by_ip.setdefault(ip, {"ip": ip, "hostname": None, "domain": None, "os": None, "smb_signing_required": None, "smbv1_enabled": None, "null_session_possible": None, "raw_line": line})
        fact["raw_line"] = line
        host = re.search(r"\b445\s+([A-Za-z0-9_.-]+)", line)
        if host: fact["hostname"] = host.group(1)
        domain = re.search(r"(?:domain|domain:)\s*[:=]?\s*([A-Za-z0-9_.-]+)", line, re.I) or re.search(r"\(domain:([^\)]+)\)", line, re.I)
        if domain: fact["domain"] = domain.group(1)
        os_match = re.search(r"\((Windows[^\)]*|Unix[^\)]*|Samba[^\)]*)\)", line, re.I)
        if not os_match:
            os_match = re.search(r"\]\s*(Windows.*?)(?:\s*\(|$)", line, re.I)
        if os_match: fact["os"] = os_match.group(1).strip()
        signing = _bool_after(line, "signing")
        if signing is not None: fact["smb_signing_required"] = signing
        smbv1 = _bool_after(line, "SMBv1")
        if smbv1 is not None: fact["smbv1_enabled"] = smbv1
        if re.search(r"(null session|anonymous).*(success|allowed|possible|pwned|\[\+\])", line, re.I) or re.search(r"\[\+\].*(-u ''|-u\s+ -p)", line, re.I):
            fact["null_session_possible"] = True
        elif re.search(r"(null session|anonymous).*(fail|denied|not allowed)", line, re.I):
            fact["null_session_possible"] = False
        share = re.search(r"\b(IPC\$|ADMIN\$|C\$|[A-Za-z0-9_.-]+\$?)\s+(READ|WRITE|READ,WRITE|NO ACCESS|READ ONLY|FULL|CHANGE)\b\s*(.*)$", line, re.I)
        if share and not share.group(1).upper().startswith("SMB"):
            shares.append({"ip": ip, "name": share.group(1), "access": share.group(2).upper(), "remark": share.group(3).strip(), "anonymous": True})
    return {"facts": list(facts_by_ip.values()), "shares": shares}
