from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.approvals.errors import ApprovalConflict, ApprovalError, ApprovalNotFound
from app.approvals.service import (
    _build_preview,
    _record_approval_event,
    _scope_snapshot,
    _validated_scope_for,
    approval_level_for,
    compute_approval_hash,
)
from app.core.config import get_settings
from app.core.parameter_validation import ParameterValidationError, mask_sensitive_params, validate_action_parameters
from app.db.models import ApprovedActionRun, OperatorApproval, PentestAction, Scan
from app.queue.connection import get_action_queue
from app.services.scan_service import add_scan_event
from app.tool_automation.command_templates import COMMAND_TEMPLATE_DEFINITIONS
from app.tool_catalog.registry import SUPPORTED_RUN_TEMPLATE_IDS, get_template, normalize_template_id
from app.tool_catalog.risk_policy import classify_execution_allowed

SUPPORTED_EXECUTABLE_TEMPLATES = SUPPORTED_RUN_TEMPLATE_IDS
RUN_STATUSES = {'queued', 'running', 'completed', 'failed', 'timeout', 'cancelled', 'blocked'}


@dataclass(frozen=True)
class ApprovedActionRunContext:
    approval: OperatorApproval
    action: PentestAction
    scan: Scan
    template_id: str
    tool_id: str
    argv: list[str]
    masked_argv: list[str]
    resolved_inputs: dict[str, Any]
    command_hash: str
    artifact_dir: str | None = None


def _event_payload(ctx: ApprovedActionRunContext, **extra: Any) -> dict[str, Any]:
    payload = {
        'approval_id': ctx.approval.id,
        'action_id': ctx.action.id,
        'scan_id': ctx.scan.id,
        'tool_id': ctx.tool_id,
        'template_id': ctx.template_id,
        'status': extra.pop('status', None),
    }
    payload.update({k: v for k, v in extra.items() if v is not None})
    return payload


def _record_run_event(db: Session, ctx: ApprovedActionRunContext, event_type: str, **extra: Any) -> None:
    add_scan_event(db, ctx.scan.id, event_type, event_type.replace('.', ' ').title(), _event_payload(ctx, **extra))


def _normalize_template_id(action: PentestAction) -> str:
    return normalize_template_id(action.tool_id, action.template_id)


def _render_arg(arg: str, values: dict[str, Any]) -> str:
    rendered = arg
    for key, value in values.items():
        rendered = rendered.replace('{' + key + '}', str(value))
    return rendered


def build_run_context(db: Session, approval_id: str, *, artifact_dir: str | None = None) -> ApprovedActionRunContext:
    approval = db.query(OperatorApproval).filter_by(id=approval_id).first()
    if approval is None:
        raise ApprovalNotFound('Approval not found')
    scan = db.query(Scan).filter_by(id=approval.scan_id).first()
    action = db.query(PentestAction).filter_by(id=approval.action_id, scan_id=approval.scan_id).first()
    if scan is None or action is None:
        raise ApprovalNotFound('Approval action not found')
    template_id = _normalize_template_id(action)
    template = COMMAND_TEMPLATE_DEFINITIONS.get(template_id)
    if template is None:
        raise ApprovalError('Template not found', 501)
    meta = get_template(template_id)
    if meta is None:
        raise ApprovalError('Template not found in tool catalog', 501)
    allowed, status_code, reason = classify_execution_allowed(meta.execution_mode, meta.supported_for_run)
    if not allowed:
        raise ApprovalError(reason, status_code)
    scope = _validated_scope_for(scan, action)
    try:
        resolved = validate_action_parameters(
            action.resolved_inputs_json or {}, template, scope, reject_unexpected=False, job_dir=artifact_dir
        )
    except ParameterValidationError as exc:
        raise ApprovalError(str(exc), 422) from exc
    masked_inputs = mask_sensitive_params(resolved, template.credential_params)
    argv = [_render_arg(arg, resolved) for arg in template.argv]
    masked_argv = [_render_arg(arg, masked_inputs) for arg in template.argv]
    preview, _missing, validated_scope_values = _build_preview(action, scan)
    scope_snapshot = _scope_snapshot(scan, action)
    scope_snapshot['validated_scope_values'] = validated_scope_values
    command_hash = compute_approval_hash(
        tool_id=action.tool_id,
        template_id=action.template_id,
        rendered_argv=preview['rendered_argv'],
        resolved_inputs=mask_sensitive_params(action.resolved_inputs_json or {}, template.credential_params),
        scope_snapshot=scope_snapshot,
        risk_level=action.risk_level,
        approval_level=approval_level_for(action.execution_mode),
    )
    return ApprovedActionRunContext(
        approval, action, scan, template_id, action.tool_id, argv, masked_argv, resolved, command_hash, artifact_dir
    )


def validate_approval_can_run(
    db: Session, approval_id: str, *, allow_consumed_active: bool = True
) -> ApprovedActionRunContext:
    ctx = build_run_context(db, approval_id)
    approval, action = ctx.approval, ctx.action
    if approval.expires_at <= datetime.utcnow() and approval.status == 'approved':
        approval.status = 'expired'
        _record_approval_event(db, approval, 'approval.expired')
        db.commit()
        raise ApprovalError('Approval expired', 410)
    if approval.status == 'consumed' and allow_consumed_active:
        run = db.query(ApprovedActionRun).filter_by(approval_id=approval.id).first()
        if run and run.status in {'queued', 'running'}:
            return ctx
    if approval.status in {'pending', 'rejected', 'consumed', 'blocked'}:
        raise ApprovalConflict(f'Approval status {approval.status} cannot run')
    if approval.status == 'expired':
        raise ApprovalError('Approval expired', 410)
    if approval.status != 'approved':
        raise ApprovalConflict(f'Approval status {approval.status} cannot run')
    if action.execution_mode == 'manual_only' or approval.approval_level == 'manual_only_blocked':
        raise ApprovalError('Manual-only actions cannot be run', 403)
    if action.status != 'approved':
        raise ApprovalConflict(f'Action status {action.status} cannot run')
    if action.status in {'queued', 'running', 'completed'}:
        raise ApprovalConflict(f'Action status {action.status} cannot run')
    if ctx.command_hash != approval.command_hash:
        _record_run_event(db, ctx, 'approval.run_refused', status='refused', error_message='hash mismatch')
        db.commit()
        raise ApprovalError('Approval command hash mismatch', 409)
    return ctx


def mark_approval_consumed(db: Session, approval: OperatorApproval) -> None:
    approval.status = 'consumed'
    approval.consumed_at = datetime.utcnow()


def mark_action_queued(db: Session, action: PentestAction) -> None:
    action.status = 'queued'
    action.updated_at = datetime.utcnow()


def prepare_approved_action_run(
    db: Session, approval_id: str, operator: str, operator_note: str | None = None
) -> ApprovedActionRunContext:
    ctx = validate_approval_can_run(db, approval_id)
    _record_run_event(db, ctx, 'approval.run_requested', status='requested')
    ctx.approval.metadata_json = {
        **(ctx.approval.metadata_json or {}),
        'run_operator': operator,
        **({'run_operator_note': operator_note} if operator_note else {}),
    }
    return ctx


def enqueue_approved_action_run(
    db: Session, approval_id: str, operator: str, operator_note: str | None = None
) -> ApprovedActionRun:
    ctx = prepare_approved_action_run(db, approval_id, operator, operator_note)
    existing = db.query(ApprovedActionRun).filter_by(approval_id=approval_id).first()
    if existing and existing.status in {'queued', 'running'}:
        return existing
    rq_job_id = f'approval-run:{approval_id}'
    run = existing or ApprovedActionRun(
        approval_id=ctx.approval.id,
        scan_id=ctx.scan.id,
        mission_id=ctx.scan.mission_id,
        action_id=ctx.action.id,
        tool_id=ctx.tool_id,
        template_id=ctx.template_id,
        rq_job_id=rq_job_id,
        status='queued',
        command_hash=ctx.command_hash,
        masked_command_json={'argv': ctx.masked_argv},
        queued_at=datetime.utcnow(),
    )
    if existing is None:
        db.add(run)
    db.flush()
    settings = get_settings()
    try:
        rq_job = get_action_queue().enqueue(
            'app.workers.approved_action_jobs.run_approved_action',
            approval_id,
            job_id=rq_job_id,
            job_timeout=settings.openadzero_action_job_timeout_seconds,
            ttl=settings.openadzero_action_job_ttl_seconds,
            result_ttl=settings.openadzero_action_result_ttl_seconds,
            failure_ttl=settings.openadzero_action_result_ttl_seconds,
        )
        run.rq_job_id = rq_job.id
    except Exception as exc:
        db.rollback()
        raise ApprovalError(f'Failed to enqueue approved action: {exc}', 503) from exc
    mark_approval_consumed(db, ctx.approval)
    mark_action_queued(db, ctx.action)
    _record_run_event(db, ctx, 'approval.run_queued', status='queued', rq_job_id=run.rq_job_id)
    db.commit()
    db.refresh(run)
    return run
