import pytest
from app.core.security import CommandPolicyError, validate_netexec_command

@pytest.mark.parametrize('command', [
    ['nxc','smb','192.168.1.10','-x','whoami'],
    ['nxc','smb','192.168.1.10','--sam'],
    ['nxc','smb','192.168.1.10','--lsa'],
    ['nxc','smb','192.168.1.10','--ntds'],
    ['nxc','smb','192.168.1.10','-M','lsassy'],
    ['nxc','smb','192.168.1.10','--spider'],
])
def test_netexec_commands_blocked(command):
    with pytest.raises(CommandPolicyError):
        validate_netexec_command(command)

@pytest.mark.parametrize('command', [
    ['nxc','smb','192.168.1.10','--log','file.log'],
    ['nxc','smb','192.168.1.10','--gen-relay-list','relay.txt','--log','file.log'],
    ['nxc','smb','192.168.1.10','-u','','-p','','--log','file.log'],
    ['nxc','smb','192.168.1.10','-u','','-p','','--shares','--log','file.log'],
])
def test_netexec_commands_allowed(command):
    validate_netexec_command(command)
