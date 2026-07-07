from pathlib import Path


def test_no_asyncio_wait_for_processes_in_netexec_or_nuclei():
    for path in ['app/jobs/netexec_job.py', 'app/jobs/nuclei_job.py']:
        source = Path(path).read_text()
        assert 'asyncio.wait_for' not in source
        assert 'create_subprocess_exec' not in source
        assert 'run_process(' in source
