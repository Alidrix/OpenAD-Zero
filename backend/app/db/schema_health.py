from __future__ import annotations

from sqlalchemy import Engine, inspect

REQUIRED_TABLES = {
    'missions',
    'scans',
    'scan_events',
    'scan_artifacts',
    'parsed_assets',
    'parsed_services',
    'parsed_findings',
    'parsed_signals',
    'parse_diagnostics',
    'pentest_phase_states',
    'pentest_actions',
    'operator_approvals',
    'approved_action_runs',
    'parsed_ad_objects',
    'parsed_ad_relations',
    'parsed_attack_paths',
    'parsed_credential_risks',
}
REQUIRED_COLUMNS = {
    'pentest_actions': {'dedupe_key', 'priority'},
    'operator_approvals': {'command_hash'},
    'approved_action_runs': {'rq_job_id'},
    'parsed_ad_objects': {'object_id'},
    'parsed_credential_risks': {'risk_type'},
}
MIGRATION_HINT = 'Run `make migrate` or `cd backend && alembic upgrade head`, then verify with `alembic heads`.'


def check_schema(engine: Engine) -> dict:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(REQUIRED_TABLES - existing_tables)
    missing_columns: dict[str, list[str]] = {}
    for table, required in REQUIRED_COLUMNS.items():
        if table not in existing_tables:
            continue
        existing = {c['name'] for c in inspector.get_columns(table)}
        missing = sorted(required - existing)
        if missing:
            missing_columns[table] = missing
    ok = not missing_tables and not missing_columns
    return {
        'ok': ok,
        'missing_tables': missing_tables,
        'missing_columns': missing_columns,
        'migration_hint': None if ok else MIGRATION_HINT,
    }
