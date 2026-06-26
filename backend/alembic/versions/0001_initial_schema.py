"""Initial OpenAD Zero schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'missions',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('scenario', sa.String(100), nullable=False),
        sa.Column('mode', sa.String(50), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('raw_scope', sa.Text(), nullable=False),
        sa.Column('validated_targets', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
    )
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('tool', sa.String(50), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('command_preview', sa.Text(), nullable=False),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('return_code', sa.Integer()),
        sa.Column('stdout_path', sa.Text()),
        sa.Column('stderr_path', sa.Text()),
        sa.Column('output_path', sa.Text()),
        sa.Column('rq_job_id', sa.String(255)),
        sa.Column('queued_at', sa.DateTime()),
        sa.Column('cancel_requested_at', sa.DateTime()),
        sa.Column('last_heartbeat_at', sa.DateTime()),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text()),
    )
    op.create_table(
        'job_logs',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('job_id', sa.String(), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('stream', sa.String(40), nullable=False),
        sa.Column('line', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'mission_events',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('event_type', sa.String(120), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('payload_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('redis_stream_id', sa.String(255)),
    )
    op.create_table(
        'hosts',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('ip', sa.String(80), nullable=False),
        sa.Column('hostname', sa.String(255)),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('os_guess', sa.String(255)),
        sa.Column('is_domain_controller_candidate', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'services',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('hosts.id'), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('product', sa.String(255), nullable=False),
        sa.Column('version', sa.String(255), nullable=False),
        sa.Column('state', sa.String(40), nullable=False),
    )
    op.create_table(
        'findings',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('hosts.id')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(40), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('confidence', sa.String(40), nullable=False),
        sa.Column('template_id', sa.String(255)),
        sa.Column('template_name', sa.String(255)),
        sa.Column('matcher_name', sa.String(255)),
        sa.Column('matched_at', sa.Text()),
        sa.Column('host', sa.String(255)),
        sa.Column('ip', sa.String(80)),
        sa.Column('port', sa.Integer()),
        sa.Column('scheme', sa.String(20)),
        sa.Column('tags', sa.JSON()),
        sa.Column('references', sa.JSON()),
        sa.Column('raw_json', sa.JSON()),
        sa.Column('raw_event_path', sa.Text()),
        sa.Column('evidence_path', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'next_actions',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.Integer(), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('command_template_id', sa.String(120)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'manual_action_cards',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('capability_id', sa.String(120), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('risk_level', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('operator_note', sa.Text()),
        sa.Column('evidence_reference', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('label', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('stored_path', sa.Text(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(255)),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('preview_available', sa.Boolean(), nullable=False),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'evidence_links',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('evidence_id', sa.String(), sa.ForeignKey('evidence.id'), nullable=False),
        sa.Column('target_type', sa.String(80), nullable=False),
        sa.Column('target_id', sa.String(120), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'smb_facts',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('hosts.id')),
        sa.Column('ip', sa.String(80), nullable=False),
        sa.Column('hostname', sa.String(255)),
        sa.Column('domain', sa.String(255)),
        sa.Column('os', sa.String(255)),
        sa.Column('smb_signing_required', sa.Boolean()),
        sa.Column('smbv1_enabled', sa.Boolean()),
        sa.Column('null_session_possible', sa.Boolean()),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('raw_line', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'smb_shares',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('hosts.id')),
        sa.Column('ip', sa.String(80), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('access', sa.String(80)),
        sa.Column('remark', sa.Text()),
        sa.Column('anonymous', sa.Boolean(), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'web_targets',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('host_id', sa.String(), sa.ForeignKey('hosts.id'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('ip', sa.String(80), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('scheme', sa.String(20), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'bloodhound_collections',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('filename', sa.String(255)),
        sa.Column('stored_path', sa.Text()),
        sa.Column('sha256', sa.String(64)),
        sa.Column('size_bytes', sa.Integer()),
        sa.Column('zip_valid', sa.Boolean()),
        sa.Column('zip_summary_json', sa.JSON()),
        sa.Column('ingestion_enabled', sa.Boolean(), nullable=False),
        sa.Column('ingestion_status', sa.String(80)),
        sa.Column('ingestion_job_id', sa.String(255)),
        sa.Column('ingestion_error', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime()),
        sa.Column('validated_at', sa.DateTime()),
        sa.Column('ingested_at', sa.DateTime()),
    )
    op.create_table(
        'bloodhound_stats',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('collection_id', sa.String(), sa.ForeignKey('bloodhound_collections.id')),
        sa.Column('domain_name', sa.String(255)),
        sa.Column('users_count', sa.Integer()),
        sa.Column('computers_count', sa.Integer()),
        sa.Column('groups_count', sa.Integer()),
        sa.Column('ous_count', sa.Integer()),
        sa.Column('gpos_count', sa.Integer()),
        sa.Column('domains_count', sa.Integer()),
        sa.Column('edges_count', sa.Integer()),
        sa.Column('raw_stats_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'reports',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('status', sa.String(40), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('markdown_path', sa.Text()),
        sa.Column('html_path', sa.Text()),
        sa.Column('metadata_path', sa.Text()),
        sa.Column('sections_json', sa.JSON()),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'mission_objectives',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('objective_name', sa.String(255), nullable=False),
        sa.Column('objective_description', sa.Text()),
        sa.Column('objective_type', sa.String(80), nullable=False),
        sa.Column('objective_target', sa.String(255)),
        sa.Column('objective_status', sa.String(80), nullable=False),
        sa.Column('operator_note', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'mission_phases',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('phase_key', sa.String(120), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('status', sa.String(80), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('summary', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'mission_timeline_events',
        sa.Column('id', sa.String(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.String(), sa.ForeignKey('missions.id'), nullable=False),
        sa.Column('event_type', sa.String(120), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('source', sa.String(80), nullable=False),
        sa.Column('severity', sa.String(40), nullable=False),
        sa.Column('related_host_id', sa.String(120)),
        sa.Column('related_service_id', sa.String(120)),
        sa.Column('related_finding_id', sa.String(120)),
        sa.Column('related_evidence_id', sa.String(120)),
        sa.Column('related_job_id', sa.String(120)),
        sa.Column('related_report_id', sa.String(120)),
        sa.Column('related_bloodhound_collection_id', sa.String(120)),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('mission_timeline_events')
    op.drop_table('mission_phases')
    op.drop_table('mission_objectives')
    op.drop_table('reports')
    op.drop_table('bloodhound_stats')
    op.drop_table('bloodhound_collections')
    op.drop_table('web_targets')
    op.drop_table('smb_shares')
    op.drop_table('smb_facts')
    op.drop_table('evidence_links')
    op.drop_table('evidence')
    op.drop_table('manual_action_cards')
    op.drop_table('next_actions')
    op.drop_table('findings')
    op.drop_table('services')
    op.drop_table('hosts')
    op.drop_table('mission_events')
    op.drop_table('job_logs')
    op.drop_table('jobs')
    op.drop_table('missions')
