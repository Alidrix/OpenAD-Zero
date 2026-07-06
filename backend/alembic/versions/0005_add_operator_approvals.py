"""add operator approvals

Revision ID: 0005_add_operator_approvals
Revises: 0004_add_pentest_orchestrator_models
Create Date: 2026-07-06
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_add_operator_approvals'
down_revision = '0004_add_pentest_orchestrator_models'
branch_labels = None
depends_on = None

INDEXES = [
    ('ix_operator_approvals_scan_id', ['scan_id']),
    ('ix_operator_approvals_mission_id', ['mission_id']),
    ('ix_operator_approvals_action_id', ['action_id']),
    ('ix_operator_approvals_status', ['status']),
    ('ix_operator_approvals_tool_id', ['tool_id']),
    ('ix_operator_approvals_template_id', ['template_id']),
    ('ix_operator_approvals_command_hash', ['command_hash']),
    ('ix_operator_approvals_expires_at', ['expires_at']),
]


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _index_names(table_name: str) -> set[str]:
    return {index['name'] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if not _has_table('operator_approvals'):
        op.create_table(
            'operator_approvals',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False),
            sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=True),
            sa.Column('action_id', sa.String(), sa.ForeignKey('pentest_actions.id'), nullable=False),
            sa.Column('phase_id', sa.String(length=120), nullable=False),
            sa.Column('tool_id', sa.String(length=120), nullable=False),
            sa.Column('template_id', sa.String(length=160), nullable=False),
            sa.Column('command_hash', sa.String(length=64), nullable=False),
            sa.Column('masked_preview_json', sa.JSON(), nullable=False),
            sa.Column('resolved_inputs_json', sa.JSON(), nullable=True),
            sa.Column('missing_inputs_json', sa.JSON(), nullable=True),
            sa.Column('scope_snapshot_json', sa.JSON(), nullable=True),
            sa.Column('risk_level', sa.String(length=40), nullable=False),
            sa.Column('approval_level', sa.String(length=40), nullable=False),
            sa.Column('status', sa.String(length=40), nullable=False),
            sa.Column('approved_by', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('approved_at', sa.DateTime(), nullable=True),
            sa.Column('rejected_at', sa.DateTime(), nullable=True),
            sa.Column('consumed_at', sa.DateTime(), nullable=True),
            sa.Column('rejection_reason', sa.Text(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.CheckConstraint("approval_level IN ('standard', 'reinforced', 'manual_only_blocked')", name='ck_operator_approvals_approval_level'),
            sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'expired', 'consumed', 'blocked')", name='ck_operator_approvals_status'),
        )
    existing = _index_names('operator_approvals')
    for name, columns in INDEXES:
        if name not in existing:
            op.create_index(name, 'operator_approvals', columns)


def downgrade() -> None:
    if _has_table('operator_approvals'):
        existing = _index_names('operator_approvals')
        for name, _columns in reversed(INDEXES):
            if name in existing:
                op.drop_index(name, table_name='operator_approvals')
        op.drop_table('operator_approvals')
