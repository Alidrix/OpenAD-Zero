"""add approved action runs

Revision ID: 0006_add_approved_action_runs
Revises: 0005_add_operator_approvals
Create Date: 2026-07-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_add_approved_action_runs'
down_revision = '0005_add_operator_approvals'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'approved_action_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('approval_id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('mission_id', sa.String(), nullable=True),
        sa.Column('action_id', sa.String(), nullable=False),
        sa.Column('tool_id', sa.String(length=120), nullable=False),
        sa.Column('template_id', sa.String(length=160), nullable=False),
        sa.Column('rq_job_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('command_hash', sa.String(length=64), nullable=False),
        sa.Column('masked_command_json', sa.JSON(), nullable=True),
        sa.Column('stdout_path', sa.Text(), nullable=True),
        sa.Column('stderr_path', sa.Text(), nullable=True),
        sa.Column('artifact_dir', sa.Text(), nullable=True),
        sa.Column('return_code', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('queued_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['action_id'], ['pentest_actions.id']),
        sa.ForeignKeyConstraint(['approval_id'], ['operator_approvals.id']),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id']),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    for name, cols in {
        'ix_approved_action_runs_approval_id':['approval_id'], 'ix_approved_action_runs_scan_id':['scan_id'],
        'ix_approved_action_runs_action_id':['action_id'], 'ix_approved_action_runs_status':['status'],
        'ix_approved_action_runs_rq_job_id':['rq_job_id']}.items():
        op.create_index(name, 'approved_action_runs', cols)


def downgrade() -> None:
    op.drop_table('approved_action_runs')
