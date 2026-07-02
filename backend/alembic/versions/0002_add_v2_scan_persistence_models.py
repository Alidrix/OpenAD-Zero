"""add v2 scan persistence models

Revision ID: 0002_add_v2_scan_persistence_models
Revises: 0001_initial_schema
Create Date: 2026-07-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_v2_scan_persistence_models'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    return column in {c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if not _has_column('missions', 'client_name'):
        op.add_column('missions', sa.Column('client_name', sa.String(length=255), nullable=True))
    if not _has_column('missions', 'scope'):
        op.add_column('missions', sa.Column('scope', sa.JSON(), nullable=True))
    if not _has_column('missions', 'updated_at'):
        op.add_column('missions', sa.Column('updated_at', sa.DateTime(), nullable=True))

    if not _has_table('scans'):
        op.create_table(
            'scans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('mission_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('scan_type', sa.String(length=120), nullable=False),
        sa.Column('tool_name', sa.String(length=120), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('progress_percent', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('rq_job_id', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('renamed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_scans_progress_percent_range'),
        sa.ForeignKeyConstraint(['mission_id'], ['missions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
        op.create_index('ix_scans_status', 'scans', ['status'])
        op.create_index('ix_scans_created_at', 'scans', ['created_at'])
        op.create_index('ix_scans_deleted_at', 'scans', ['deleted_at'])
        op.create_index('ix_scans_mission_id', 'scans', ['mission_id'])

    if not _has_table('scan_steps'):
        op.create_table(
            'scan_steps',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('progress_percent', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_scan_steps_progress_percent_range'),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    if not _has_table('scan_events'):
        op.create_table(
            'scan_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
        op.create_index('ix_scan_events_scan_id', 'scan_events', ['scan_id'])
        op.create_index('ix_scan_events_created_at', 'scan_events', ['created_at'])

    if not _has_table('scan_artifacts'):
        op.create_table(
            'scan_artifacts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('scan_id', sa.String(), nullable=False),
        sa.Column('artifact_type', sa.String(length=120), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scan_id'], ['scans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
        op.create_index('ix_scan_artifacts_scan_id', 'scan_artifacts', ['scan_id'])


def downgrade() -> None:
    op.drop_index('ix_scan_artifacts_scan_id', table_name='scan_artifacts')
    op.drop_table('scan_artifacts')
    op.drop_index('ix_scan_events_created_at', table_name='scan_events')
    op.drop_index('ix_scan_events_scan_id', table_name='scan_events')
    op.drop_table('scan_events')
    op.drop_table('scan_steps')
    op.drop_index('ix_scans_mission_id', table_name='scans')
    op.drop_index('ix_scans_deleted_at', table_name='scans')
    op.drop_index('ix_scans_created_at', table_name='scans')
    op.drop_index('ix_scans_status', table_name='scans')
    op.drop_table('scans')
    op.drop_column('missions', 'updated_at')
    op.drop_column('missions', 'scope')
    op.drop_column('missions', 'client_name')
