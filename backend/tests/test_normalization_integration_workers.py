import inspect

from app.workers import approved_action_jobs, initial_discovery_jobs


def test_workers_call_normalization_and_recompute():
    assert 'normalize_artifact' in inspect.getsource(initial_discovery_jobs)
    assert 'PentestOrchestrator(db).recompute' in inspect.getsource(initial_discovery_jobs)
    assert 'normalize_artifact' in inspect.getsource(approved_action_jobs)
    assert 'PentestOrchestrator(db).recompute' in inspect.getsource(approved_action_jobs)
    assert 'normalization.completed' in inspect.getsource(approved_action_jobs)
