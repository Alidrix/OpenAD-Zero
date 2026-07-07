from __future__ import annotations

import hashlib
import json
from datetime import datetime


def stable_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, separators=(',', ':')).encode()).hexdigest()


def update_fields(row, **fields):
    for k, v in fields.items():
        if v is not None or getattr(row, k, None) in (None, '', {}, []):
            setattr(row, k, v)
    if hasattr(row, 'updated_at'):
        row.updated_at = datetime.utcnow()
    return row


def get_or_create(db, model, filters: dict, defaults: dict | None = None):
    row = db.query(model).filter_by(**filters).first()
    created = False
    if row is None:
        row = model(**filters, **(defaults or {}))
        db.add(row)
        db.flush()
        created = True
    elif defaults:
        update_fields(row, **defaults)
        db.flush()
    return row, created
