import os
import shlex

BLOCKED_TOKENS = {
    '-x','-X','--exec-method','--sam','--lsa','--ntds','--dpapi','--mkfile','--get-file','--put-file','--spider','-M',
}
BLOCKED_WORDS = {'lsassy','mimikatz','nanodump','dcsync','secrets','hash','spray','brute','psexec','smbexec','wmiexec','atexec'}
ALLOWED_BINARIES = {'nxc'}

class CommandPolicyError(ValueError):
    pass

def validate_netexec_command(command: list[str]) -> None:
    if not command:
        raise CommandPolicyError('Empty command')
    binary = os.path.basename(command[0])
    if binary not in ALLOWED_BINARIES:
        raise CommandPolicyError('NetExec runner only allows nxc')
    lowered = [part.lower() for part in command]
    for token in lowered:
        if token in BLOCKED_TOKENS:
            raise CommandPolicyError(f'Blocked NetExec option: {token}')
    joined = ' '.join(shlex.quote(p) for p in lowered)
    for word in BLOCKED_WORDS:
        if word in joined:
            raise CommandPolicyError(f'Blocked NetExec keyword: {word}')
