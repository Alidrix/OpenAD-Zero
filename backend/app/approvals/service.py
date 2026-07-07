from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.approvals.errors import ApprovalConflict, ApprovalError, ApprovalNotFound
from app.core.config import get_settings
from app.core.parameter_validation import (
    ParameterValidationError,
    mask_sensitive_params,
    validate_action_parameters,
    validate_scope_sensitive_params,
)
from app.db.models import OperatorApproval, PentestAction, Scan
from app.services.scan_service import add_scan_event
from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS
from app.tool_automation.policy import load_tool_catalog

SECRET_KEYS = {'password', 'pass', 'secret', 'token', 'key', 'hash', 'ntlm_hash', 'credential', 'api_key'}
BLOCKING_STATUSES = {'queued', 'running', 'completed', 'failed', 'rejected'}
TEMPLATE_ALIASES = {
    ('netexec', 'smb_fingerprint'): ('netexec_smb_fingerprint', 'netexec_smb_fingerprint'),
    ('netexec', 'smb_signing_check'): ('netexec_smb_signing_check', 'netexec_smb_signing_check'),
    ('netexec', 'smb_null_session_check'): ('netexec_smb_null_session_check', 'netexec_smb_null_session_check'),
    ('nuclei', 'safe_templates'): ('nuclei_safe_templates', 'nuclei_safe_templates'),
    ('kerberos', 'kerberos_user_enumeration'): ('kerbrute', 'kerbrute_userenum'),
    ('bloodhound', 'path_analysis'): ('bloodhound_pathfinding', 'bloodhound_pathfinding'),
}


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SECRET_KEYS)


def _mask(value: Any, key: str = '') -> Any:
    if _is_secret_key(key):
        return '***REDACTED***' if value not in (None, '') else value
    if isinstance(value, dict):
        return {k: _mask(v, k) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_mask(v, key) for v in value]
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def _resolve_catalog(action: PentestAction):
    tools = load_tool_catalog()
    tool_id = action.tool_id
    template_id = action.template_id
    if tool_id in tools and template_id in set(tools[tool_id].get('templates') or []):
        resolved_tool_id, resolved_template_id = tool_id, template_id
    else:
        resolved_tool_id, resolved_template_id = TEMPLATE_ALIASES.get((tool_id, template_id), (tool_id, template_id))
    tool = tools.get(resolved_tool_id)
    template = COMMAND_TEMPLATE_DEFINITIONS.get(resolved_template_id)
    if tool is None or template is None or resolved_template_id not in set(tool.get('templates') or []):
        raise ApprovalError('Action tool/template is not allowlisted', 400)
    return tool, template


def _render_arg(arg: str, values: dict[str, Any]) -> str:
    rendered = arg
    for key, value in values.items():
        rendered = rendered.replace('{' + key + '}', str(_mask(value, key)))
    return rendered


def _validated_scope_for(scan: Scan, action: PentestAction) -> list[str]:
    mission = None
    if scan.mission_id:
        mission = getattr(scan, 'mission', None) or None
    return list(
        getattr(mission, 'validated_targets', None)
        or (action.scope_sensitive_params_json or {}).get('validated_scope')
        or []
    )


def _validate_action(action: PentestAction, scan: Scan) -> tuple[dict[str, Any], list[str]]:
    _tool, template = _resolve_catalog(action)
    resolved = action.resolved_inputs_json or {}
    scope = _validated_scope_for(scan, action)
    if action.missing_inputs_json:
        return resolved, scope
    try:
        validate_action_parameters(resolved, template, scope, reject_unexpected=False)
    except ParameterValidationError as exc:
        raise ApprovalError(str(exc), 400) from exc
    return resolved, validate_scope_sensitive_params(resolved, template, scope)


def _build_preview(action: PentestAction, scan: Scan) -> tuple[dict[str, Any], list[str], list[str]]:
    _tool, template = _resolve_catalog(action)
    resolved, validated_scope_values = _validate_action(action, scan)
    missing = [name for name in template.required_params if name not in resolved]
    argv = [_render_arg(arg, mask_sensitive_params(resolved, template.credential_params)) for arg in template.argv]
    return (
        {
            'tool_id': action.tool_id,
            'template_id': action.template_id,
            'rendered_argv': argv,
            'description': template.description,
            'parser': template.parser,
            'output_artifact_type': template.output_artifact_type,
        },
        missing,
        validated_scope_values,
    )


def _scope_snapshot(scan: Scan, action: PentestAction) -> dict[str, Any]:
    return {
        'scan_id': scan.id,
        'mission_id': scan.mission_id,
        'scan_type': scan.scan_type,
        'action_scope_sensitive_params': _mask(action.scope_sensitive_params_json or {}),
        'validated_scope_values': [],
    }


def approval_level_for(execution_mode: str) -> str:
    if execution_mode == 'reinforced_approval_required':
        return 'reinforced'
    if execution_mode == 'manual_only':
        return 'manual_only_blocked'
    return 'standard'


def compute_approval_hash(
    *,
    tool_id: str,
    template_id: str,
    rendered_argv: list[str],
    resolved_inputs: dict[str, Any],
    scope_snapshot: dict[str, Any],
    risk_level: str,
    approval_level: str,
) -> str:
    payload = {
        'tool_id': tool_id,
        'template_id': template_id,
        'rendered_argv': rendered_argv,
        'resolved_inputs': _mask(resolved_inputs),
        'scope_snapshot': _mask(scope_snapshot),
        'risk_level': risk_level,
        'approval_level': approval_level,
    }
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _approval_event_payload(approval: OperatorApproval) -> dict[str, Any]:
    return {
        'approval_id': approval.id,
        'scan_id': approval.scan_id,
        'action_id': approval.action_id,
        'phase_id': approval.phase_id,
        'tool_id': approval.tool_id,
        'template_id': approval.template_id,
        'risk_level': approval.risk_level,
        'approval_level': approval.approval_level,
        'status': approval.status,
    }


def _record_approval_event(db: Session, approval: OperatorApproval, event_type: str) -> None:
    add_scan_event(
        db, approval.scan_id, event_type, event_type.replace('.', ' ').title(), _approval_event_payload(approval)
    )


def to_read(row: OperatorApproval) -> dict[str, Any]:
    return {
        'id': row.id,
        'scan_id': row.scan_id,
        'mission_id': row.mission_id,
        'action_id': row.action_id,
        'phase_id': row.phase_id,
        'tool_id': row.tool_id,
        'template_id': row.template_id,
        'command_hash': row.command_hash,
        'masked_preview': row.masked_preview_json or {},
        'resolved_inputs': _mask(row.resolved_inputs_json or {}),
        'missing_inputs': row.missing_inputs_json or [],
        'scope_snapshot': _mask(row.scope_snapshot_json or {}),
        'risk_level': row.risk_level,
        'approval_level': row.approval_level,
        'status': row.status,
        'approved_by': row.approved_by,
        'created_at': row.created_at,
        'expires_at': row.expires_at,
        'approved_at': row.approved_at,
        'rejected_at': row.rejected_at,
        'consumed_at': row.consumed_at,
        'rejection_reason': row.rejection_reason,
        'metadata': _mask(row.metadata_json or {}),
    }


def expire_approval_if_needed(db: Session, approval: OperatorApproval) -> OperatorApproval:
    if approval.status == 'pending' and approval.expires_at <= datetime.utcnow():
        approval.status = 'expired'
        _record_approval_event(db, approval, 'approval.expired')
        db.commit()
        db.refresh(approval)
    return approval


def prepare_approval(db: Session, scan_id: str, action_id: str, operator_note: str | None = None) -> OperatorApproval:
    scan = db.query(Scan).filter_by(id=scan_id).first()
    if scan is None:
        raise ApprovalNotFound('Scan not found')
    action = db.query(PentestAction).filter_by(id=action_id).first()
    if action is None or action.scan_id != scan_id:
        raise ApprovalNotFound('Pentest action not found')
    if action.execution_mode == 'manual_only':
        raise ApprovalError('Manual-only actions cannot be approved', 400)
    if action.status in BLOCKING_STATUSES:
        raise ApprovalConflict(f'Action status {action.status} cannot be prepared')
    level = approval_level_for(action.execution_mode)
    preview, template_missing, validated_scope_values = _build_preview(action, scan)
    missing = list(dict.fromkeys((action.missing_inputs_json or []) + template_missing))
    scope = _scope_snapshot(scan, action)
    scope['validated_scope_values'] = validated_scope_values
    resolved = mask_sensitive_params(
        action.resolved_inputs_json or {},
        COMMAND_TEMPLATE_DEFINITIONS.get(action.template_id).credential_params
        if COMMAND_TEMPLATE_DEFINITIONS.get(action.template_id)
        else None,
    )
    command_hash = compute_approval_hash(
        tool_id=action.tool_id,
        template_id=action.template_id,
        rendered_argv=preview['rendered_argv'],
        resolved_inputs=resolved,
        scope_snapshot=scope,
        risk_level=action.risk_level,
        approval_level=level,
    )
    existing = (
        db.query(OperatorApproval)
        .filter_by(action_id=action.id, command_hash=command_hash, status='pending')
        .order_by(OperatorApproval.created_at.desc())
        .first()
    )
    if existing is not None:
        existing = expire_approval_if_needed(db, existing)
        if existing.status == 'pending':
            return existing
    now = datetime.utcnow()
    approval = OperatorApproval(
        scan_id=scan.id,
        mission_id=scan.mission_id,
        action_id=action.id,
        phase_id=action.phase_id,
        tool_id=action.tool_id,
        template_id=action.template_id,
        command_hash=command_hash,
        masked_preview_json=preview,
        resolved_inputs_json=resolved,
        missing_inputs_json=missing,
        scope_snapshot_json=scope,
        risk_level=action.risk_level,
        approval_level=level,
        status='pending',
        created_at=now,
        expires_at=now + timedelta(seconds=get_settings().openadzero_approval_ttl_seconds),
        metadata_json={'operator_note': operator_note} if operator_note else {},
    )
    db.add(approval)
    db.flush()
    _record_approval_event(db, approval, 'approval.prepared')
    if action.status == 'proposed':
        action.status = 'waiting_approval'
        action.updated_at = now
    db.commit()
    db.refresh(approval)
    return approval


def get_approval(db: Session, approval_id: str) -> OperatorApproval:
    approval = db.query(OperatorApproval).filter_by(id=approval_id).first()
    if approval is None:
        raise ApprovalNotFound('Approval not found')
    return expire_approval_if_needed(db, approval)


def _latest_for_action(db: Session, scan_id: str, action_id: str) -> OperatorApproval:
    row = (
        db.query(OperatorApproval)
        .filter_by(scan_id=scan_id, action_id=action_id)
        .order_by(OperatorApproval.created_at.desc())
        .first()
    )
    if row is None:
        raise ApprovalNotFound('Approval not found')
    return expire_approval_if_needed(db, row)


def approve_approval(
    db: Session,
    scan_id: str,
    action_id: str,
    operator: str,
    operator_note: str | None = None,
    reinforced_confirmation: str | None = None,
) -> OperatorApproval:
    approval = _latest_for_action(db, scan_id, action_id)
    if approval.status != 'pending':
        raise ApprovalConflict(f'Approval status {approval.status} cannot be approved')
    if approval.approval_level == 'manual_only_blocked':
        raise ApprovalError('Manual-only approvals cannot be approved', 400)
    if approval.approval_level == 'reinforced' and not (reinforced_confirmation or '').strip():
        raise ApprovalError('Reinforced approval requires explicit confirmation', 400)
    action = db.query(PentestAction).filter_by(id=action_id, scan_id=scan_id).first()
    scan = db.query(Scan).filter_by(id=scan_id).first()
    if action is not None and scan is not None:
        _validate_action(action, scan)
    if action is None or action.execution_mode == 'manual_only':
        raise ApprovalError('Action cannot be approved', 400)
    now = datetime.utcnow()
    approval.status = 'approved'
    approval.approved_by = operator
    approval.approved_at = now
    approval.metadata_json = {
        **(approval.metadata_json or {}),
        **({'operator_note': operator_note} if operator_note else {}),
        **({'reinforced_confirmation_recorded': True} if reinforced_confirmation else {}),
    }
    action.status = 'approved'
    action.updated_at = now
    _record_approval_event(db, approval, 'approval.approved')
    db.commit()
    db.refresh(approval)
    return approval


def reject_approval(
    db: Session, scan_id: str, action_id: str, operator: str, reason: str | None = None
) -> OperatorApproval:
    approval = _latest_for_action(db, scan_id, action_id)
    if approval.status not in {'pending', 'approved'}:
        raise ApprovalConflict(f'Approval status {approval.status} cannot be rejected')
    action = db.query(PentestAction).filter_by(id=action_id, scan_id=scan_id).first()
    now = datetime.utcnow()
    approval.status = 'rejected'
    approval.approved_by = operator
    approval.rejected_at = now
    approval.rejection_reason = reason
    if action is not None:
        action.status = 'rejected'
        action.updated_at = now
    _record_approval_event(db, approval, 'approval.rejected')
    db.commit()
    db.refresh(approval)
    return approval


def mark_approval_consumed(db: Session, approval_id: str) -> OperatorApproval:
    approval = get_approval(db, approval_id)
    if approval.status != 'approved':
        raise ApprovalConflict(f'Approval status {approval.status} cannot be consumed')
    approval.status = 'consumed'
    approval.consumed_at = datetime.utcnow()
    db.commit()
    db.refresh(approval)
    return approval


def approvals_summary(db: Session, scan_id: str) -> dict[str, Any]:
    if db.query(Scan).filter_by(id=scan_id).first() is None:
        raise ApprovalNotFound('Scan not found')
    rows = [expire_approval_if_needed(db, row) for row in db.query(OperatorApproval).filter_by(scan_id=scan_id).all()]
    summary: dict[str, Any] = {
        'scan_id': scan_id,
        'total': len(rows),
        'pending': 0,
        'approved': 0,
        'rejected': 0,
        'expired': 0,
        'consumed': 0,
        'blocked': 0,
        'reinforced_pending': 0,
        'next_expiration_at': None,
    }
    pending_expirations = []
    for row in rows:
        if row.status in summary:
            summary[row.status] += 1
        if row.status == 'pending' and row.approval_level == 'reinforced':
            summary['reinforced_pending'] += 1
        if row.status == 'pending' and row.expires_at is not None:
            pending_expirations.append(row.expires_at)
    summary['next_expiration_at'] = min(pending_expirations) if pending_expirations else None
    return summary


def run_approval_contract(db: Session, approval_id: str) -> dict[str, Any]:
    approval = get_approval(db, approval_id)
    if approval.status != 'approved':
        raise ApprovalConflict(f'Approval status {approval.status} cannot be run')
    if approval.expires_at <= datetime.utcnow():
        raise ApprovalConflict('Approval expired')
    if approval.consumed_at is not None or approval.status == 'consumed':
        raise ApprovalConflict('Approval already consumed')
    action = db.query(PentestAction).filter_by(id=approval.action_id, scan_id=approval.scan_id).first()
    if action is None:
        raise ApprovalNotFound('Pentest action not found')
    return {
        'ready': False,
        'reason': 'Execution runner is not implemented yet. This endpoint will be enabled in Prompt 10.',
    }
