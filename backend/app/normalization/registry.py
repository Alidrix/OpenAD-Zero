from pathlib import Path


def infer_artifact_kind(artifact) -> str:
    text = f'{getattr(artifact, "artifact_type", "")} {getattr(artifact, "path", "")}'.lower()
    if 'bloodhound' in text or text.endswith('.zip'):
        return 'bloodhound'
    if 'nuclei' in text or text.endswith('.jsonl'):
        return 'nuclei'
    if (
        'netexec' in text
        or 'nxc' in text
        or 'smb' in text
        and Path(str(getattr(artifact, 'path', ''))).suffix in {'.log', '.txt', '.json'}
    ):
        return 'netexec_smb'
    if 'ldap' in text:
        return 'ldap'
    if 'kerberos' in text:
        return 'kerberos'
    if 'adcs' in text:
        return 'adcs'
    if 'nmap' in text or text.endswith('.xml'):
        return 'nmap'
    return 'unknown'
