"""Executable command templates for the Tool Automation Library.

Only read-only assisted-safe templates are declared here. Manual-only and
blocked automation categories intentionally have no runnable templates.
"""

COMMAND_TEMPLATES: dict[str, list[str]] = {
    "nmap_safe_discovery": ["nmap", "-sV", "--version-light", "{target}"],
    "netexec_smb_fingerprint": ["nxc", "smb", "{target}", "--shares", "--no-bruteforce"],
    "netexec_smb_signing_check": ["nxc", "smb", "{target}", "--gen-relay-list", "{output}"],
    "netexec_smb_null_session_check": ["nxc", "smb", "{target}", "-u", "", "-p", ""],
    "nuclei_safe_templates": ["nuclei", "-target", "{target}", "-t", "nuclei-templates-safe/"],
    "enum4linux_ng_basic": ["enum4linux-ng", "-A", "-oJ", "{output}", "{target}"],
}
