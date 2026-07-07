from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.approvals.errors import ApprovalError
from app.approvals.run_service import enqueue_approved_action_run
from app.approvals.schemas import (
    ApprovalApproveRequest,
    ApprovalListItem,
    ApprovalPrepareRequest,
    ApprovalRejectRequest,
    ApprovalRunRead,
    ApprovalRunRequest,
    ApprovalSummaryRead,
    OperatorApprovalRead,
)
from app.approvals.service import (
    approvals_summary,
    approve_approval,
    expire_approval_if_needed,
    get_approval,
    prepare_approval,
    reject_approval,
    to_read,
)
from app.db.models import OperatorApproval, Scan
from app.db.session import get_db

router = APIRouter(prefix='/v2', tags=['v2-approvals'])


def _raise(exc: ApprovalError):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post('/scans/{scan_id}/pentest/actions/{action_id}/approval/prepare', response_model=OperatorApprovalRead)
def prepare(scan_id: str, action_id: str, payload: ApprovalPrepareRequest, db: Session = Depends(get_db)):
    try:
        return to_read(prepare_approval(db, scan_id, action_id, payload.operator_note))
    except ApprovalError as exc:
        _raise(exc)


@router.post('/scans/{scan_id}/pentest/actions/{action_id}/approval/approve', response_model=OperatorApprovalRead)
def approve(scan_id: str, action_id: str, payload: ApprovalApproveRequest, db: Session = Depends(get_db)):
    try:
        return to_read(
            approve_approval(
                db, scan_id, action_id, payload.operator, payload.operator_note, payload.reinforced_confirmation
            )
        )
    except ApprovalError as exc:
        _raise(exc)


@router.post('/scans/{scan_id}/pentest/actions/{action_id}/approval/reject', response_model=OperatorApprovalRead)
def reject(scan_id: str, action_id: str, payload: ApprovalRejectRequest, db: Session = Depends(get_db)):
    try:
        return to_read(reject_approval(db, scan_id, action_id, payload.operator, payload.reason))
    except ApprovalError as exc:
        _raise(exc)


@router.get('/approvals/{approval_id}', response_model=OperatorApprovalRead)
def read_approval(approval_id: str, db: Session = Depends(get_db)):
    try:
        return to_read(get_approval(db, approval_id))
    except ApprovalError as exc:
        _raise(exc)


@router.get('/scans/{scan_id}/approvals', response_model=list[ApprovalListItem])
def list_scan_approvals(scan_id: str, status: str | None = Query(default=None), db: Session = Depends(get_db)):
    if db.query(Scan).filter_by(id=scan_id).first() is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    query = db.query(OperatorApproval).filter_by(scan_id=scan_id)
    if status is not None:
        query = query.filter(OperatorApproval.status == status)
    rows = query.order_by(OperatorApproval.created_at.desc()).all()
    return [to_read(expire_approval_if_needed(db, row)) for row in rows]


@router.get('/scans/{scan_id}/approvals/summary', response_model=ApprovalSummaryRead)
def scan_approvals_summary(scan_id: str, db: Session = Depends(get_db)):
    try:
        return approvals_summary(db, scan_id)
    except ApprovalError as exc:
        _raise(exc)


@router.post('/approvals/{approval_id}/run', response_model=ApprovalRunRead)
def run_approval(approval_id: str, payload: ApprovalRunRequest, db: Session = Depends(get_db)):
    try:
        run = enqueue_approved_action_run(db, approval_id, payload.operator, payload.operator_note)
        return {
            'approval_id': run.approval_id,
            'action_id': run.action_id,
            'scan_id': run.scan_id,
            'status': run.status,
            'rq_job_id': run.rq_job_id,
            'job_id': run.id,
            'message': 'Approved action queued',
        }
    except ApprovalError as exc:
        _raise(exc)
