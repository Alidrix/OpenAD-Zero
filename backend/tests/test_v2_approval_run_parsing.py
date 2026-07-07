from app.db.models import ApprovedActionRun, ParsedSignal, Scan
from app.workers.approved_action_jobs import _parse_outputs


class Ctx:
    template_id = 'netexec_smb_signing_check'
    tool_id = 'netexec'

    class scan:
        id = 'scan-parse'

    class approval:
        id = 'approval-parse'

    class action:
        id = 'action-parse'


def test_netexec_parser_creates_signal(db_session, tmp_path):
    db_session.add(Scan(id='scan-parse', name='s', scan_type='manual', status='draft'))
    run = ApprovedActionRun(
        approval_id='approval-parse',
        scan_id='scan-parse',
        action_id='action-parse',
        tool_id='netexec',
        template_id='netexec_smb_signing_check',
        rq_job_id='approval-run:approval-parse',
        status='completed',
        command_hash='a' * 64,
    )
    db_session.add(run)
    db_session.flush()
    stdout = tmp_path / 'stdout.log'
    stderr = tmp_path / 'stderr.log'
    stdout.write_text('SMB 10.0.0.5 signing:false\n')
    stderr.write_text('')
    _parse_outputs(db_session, Ctx(), stdout, stderr, run)
    assert db_session.query(ParsedSignal).filter_by(scan_id='scan-parse', signal='smb_signing_disabled').count() == 1
