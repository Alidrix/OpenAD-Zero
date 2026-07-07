from app.db.models import ParseDiagnostic


def add_diagnostic(db, result, scan_id, source_type, source_id, message, level='warning', details=None):
    db.add(
        ParseDiagnostic(
            scan_id=scan_id,
            source_type=source_type,
            source_id=source_id,
            level=level,
            message=message,
            details_json=details,
        )
    )
    result.diagnostics_created += 1
    if level == 'error':
        result.errors.append(message)
    elif level == 'warning':
        result.warnings.append(message)
