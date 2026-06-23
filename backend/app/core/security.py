from pathlib import Path

ALLOWED_TOOLS = {"nmap", "nxc"}
NETEXEC_ALLOWED_TEMPLATES = {
    "netexec_smb_fingerprint",
    "netexec_smb_signing_check",
    "netexec_smb_null_session_check",
    "netexec_smb_null_session_shares",
}
NETEXEC_BLOCKED_TOKENS = {
    "-x", "-X", "--exec-method", "--sam", "--lsa", "--ntds", "--dpapi",
    "--mkfile", "--get-file", "--put-file", "--spider", "-M",
    "lsassy", "mimikatz", "nanodump", "dcsync", "secrets", "hash",
    "spray", "brute", "psexec", "smbexec", "wmiexec", "atexec",
}

class CommandPolicyError(ValueError):
    pass

def ensure_allowed_tool(tool: str) -> None:
    binary = Path(tool).name
    if binary not in ALLOWED_TOOLS:
        raise CommandPolicyError(f"Tool not allowed: {tool}")

def ensure_netexec_template_allowed(template_id: str) -> None:
    if template_id not in NETEXEC_ALLOWED_TEMPLATES:
        raise CommandPolicyError(f"NetExec template not allowed: {template_id}")

def validate_netexec_command(command: list[str]) -> None:
    if not command:
        raise CommandPolicyError("Empty command refused")
    if Path(command[0]).name != "nxc":
        raise CommandPolicyError("Only the nxc binary is allowed for NetExec jobs")
    lowered = [part.lower() for part in command]
    for token in lowered:
        if token in NETEXEC_BLOCKED_TOKENS:
            raise CommandPolicyError(f"Blocked NetExec argument: {token}")
    joined = " ".join(lowered)
    for word in NETEXEC_BLOCKED_TOKENS:
        if word.startswith("-"):
            continue
        if word in joined:
            raise CommandPolicyError(f"Blocked NetExec keyword: {word}")
