from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ApprovalLevel = Literal['standard', 'reinforced', 'manual_only_blocked']
ApprovalStatus = Literal['pending', 'approved', 'rejected', 'expired', 'consumed', 'blocked']


class StrictApprovalPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ApprovalPrepareRequest(StrictApprovalPayload):
    operator_note: str | None = Field(default=None, max_length=2000)


class ApprovalApproveRequest(StrictApprovalPayload):
    operator: str = Field(min_length=1, max_length=200)
    operator_note: str | None = Field(default=None, max_length=2000)
    reinforced_confirmation: str | None = Field(default=None, max_length=2000)


class ApprovalRejectRequest(StrictApprovalPayload):
    operator: str = Field(min_length=1, max_length=200)
    reason: str | None = Field(default=None, max_length=2000)


class OperatorApprovalRead(BaseModel):
    id: str
    scan_id: str
    mission_id: str | None
    action_id: str
    phase_id: str
    tool_id: str
    template_id: str
    command_hash: str
    masked_preview: dict[str, Any]
    resolved_inputs: dict[str, Any]
    missing_inputs: list[Any]
    scope_snapshot: dict[str, Any]
    risk_level: str
    approval_level: ApprovalLevel
    status: ApprovalStatus
    approved_by: str | None
    created_at: datetime
    expires_at: datetime
    approved_at: datetime | None
    rejected_at: datetime | None
    consumed_at: datetime | None
    rejection_reason: str | None
    metadata: dict[str, Any]


class ApprovalListItem(OperatorApprovalRead):
    pass
