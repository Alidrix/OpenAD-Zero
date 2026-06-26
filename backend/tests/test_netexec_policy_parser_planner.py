import pytest

from app.db.models import Host, Mission, Service
from app.jobs.command_policy import CommandPolicyError, validate_netexec_command
from app.parsers.netexec_smb import parse_netexec_smb_output
from app.planner.next_actions import plan_after_netexec, plan_for_mission


@pytest.mark.parametrize(
    'cmd',
    [
        ['nxc', 'smb', '192.168.1.10', '-x', 'whoami'],
        ['nxc', 'smb', '192.168.1.10', '--sam'],
        ['nxc', 'smb', '192.168.1.10', '--lsa'],
        ['nxc', 'smb', '192.168.1.10', '--ntds'],
        ['nxc', 'smb', '192.168.1.10', '-M', 'lsassy'],
        ['nxc', 'smb', '192.168.1.10', '--spider'],
    ],
)
def test_netexec_policy_blocks(cmd):
    with pytest.raises(CommandPolicyError):
        validate_netexec_command(cmd)


@pytest.mark.parametrize(
    'cmd',
    [
        ['nxc', 'smb', '192.168.1.10', '--log', 'file.log'],
        ['nxc', 'smb', '192.168.1.10', '--gen-relay-list', 'relay.txt', '--log', 'file.log'],
        ['nxc', 'smb', '192.168.1.10', '-u', '', '-p', '', '--log', 'file.log'],
        ['nxc', 'smb', '192.168.1.10', '-u', '', '-p', '', '--shares', '--log', 'file.log'],
    ],
)
def test_netexec_policy_allows(cmd):
    validate_netexec_command(cmd)


def test_parse_netexec_fingerprint_and_flags():
    out = 'SMB 192.168.1.10 445 DC01 [*] Windows Server 2019 (domain:LAB.LOCAL) (signing:True) (SMBv1:False)\nSMB 192.168.1.20 445 WS01 [*] Windows 10 (signing:False) (SMBv1:False)'
    parsed = parse_netexec_smb_output(out)
    assert len(parsed['facts']) == 2
    dc = parsed['facts'][0]
    assert (
        dc['hostname'] == 'DC01'
        and dc['domain'] == 'LAB.LOCAL'
        and dc['smb_signing_required'] is True
        and dc['smbv1_enabled'] is False
    )
    assert parsed['facts'][1]['smb_signing_required'] is False


def test_parse_null_session_and_share_and_invalid_empty():
    assert parse_netexec_smb_output('nonsense\n')['facts'] == []
    assert parse_netexec_smb_output('') == {'facts': [], 'shares': []}
    out = 'SMB 192.168.1.10 445 DC01 [+] LAB\\: \nShare  Permissions  Remark\nIPC$  READ  Remote IPC'
    parsed = parse_netexec_smb_output(out)
    assert parsed['facts'][0]['null_session_possible'] is True
    assert parsed['shares'][0]['name'] == 'IPC$' and parsed['shares'][0]['access'] == 'READ'


def test_planner_after_nmap_smb(db_session):
    m = Mission(name='m', scenario='s', mode='safe', raw_scope='192.168.1.0/24', validated_targets=['192.168.1.0/24'])
    db_session.add(m)
    db_session.commit()
    h = Host(mission_id=m.id, ip='192.168.1.10', status='up')
    db_session.add(h)
    db_session.flush()
    db_session.add(
        Service(
            mission_id=m.id,
            host_id=h.id,
            port=445,
            protocol='tcp',
            name='microsoft-ds',
            product='',
            version='',
            state='open',
        )
    )
    db_session.commit()
    _, actions = plan_for_mission(db_session, m.id)
    tids = {a.command_template_id for a in actions}
    assert 'netexec_smb_fingerprint' in tids and 'netexec_smb_signing_check' in tids


def test_planner_after_netexec(db_session):
    m = Mission(name='m', scenario='s', mode='safe', raw_scope='192.168.1.0/24', validated_targets=['192.168.1.0/24'])
    db_session.add(m)
    db_session.commit()
    findings, actions = plan_after_netexec(
        db_session,
        m.id,
        [
            {
                'ip': '192.168.1.10',
                'hostname': 'DC01',
                'domain': 'LAB.LOCAL',
                'smb_signing_required': False,
                'null_session_possible': True,
            }
        ],
        [],
        'netexec_smb_fingerprint',
    )
    assert any(a.command_template_id == 'bloodhound_prepare_collection' for a in actions)
    findings, actions = plan_after_netexec(
        db_session, m.id, [{'ip': '192.168.1.10', 'null_session_possible': True}], [], 'netexec_smb_null_session_check'
    )
    assert any(a.command_template_id == 'netexec_smb_null_session_shares' for a in actions)
    findings, _ = plan_after_netexec(
        db_session, m.id, [{'ip': '192.168.1.20', 'smb_signing_required': False}], [], 'netexec_smb_signing_check'
    )
    assert findings[0].title == 'SMB signing not required' and findings[0].severity == 'high'
