"""add v2 normalized parsing models

Revision ID: 0003_add_v2_normalized_parsing_models
Revises: 0002_add_v2_scan_persistence_models
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_add_v2_normalized_parsing_models'
down_revision = '0002_add_v2_scan_persistence_models'
branch_labels = None
depends_on = None

def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)

def upgrade() -> None:
    if _has_table('parsed_assets'):
        return
    op.create_table('parsed_assets',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(length=80), nullable=False), sa.Column('hostname', sa.String(length=255)), sa.Column('fqdn', sa.String(length=255)),
        sa.Column('mac_address', sa.String(length=80)), sa.Column('os_family', sa.String(length=80)), sa.Column('os_name', sa.String(length=255)),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_assets_confidence_range'))
    op.create_index('ix_parsed_assets_scan_id','parsed_assets',['scan_id']); op.create_index('ix_parsed_assets_ip_address','parsed_assets',['ip_address'])
    op.create_table('parsed_services',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('ip_address', sa.String(length=80), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False), sa.Column('protocol', sa.String(length=20), nullable=False), sa.Column('service_name', sa.String(length=120)), sa.Column('product', sa.String(length=255)), sa.Column('version', sa.String(length=255)), sa.Column('state', sa.String(length=40), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_services_confidence_range'))
    for col in ['scan_id','ip_address','port','protocol']: op.create_index(f'ix_parsed_services_{col}','parsed_services',[col])
    op.create_table('parsed_findings',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')), sa.Column('service_id', sa.String(), sa.ForeignKey('parsed_services.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('title', sa.String(length=255), nullable=False), sa.Column('description', sa.Text(), nullable=False), sa.Column('severity', sa.String(length=40), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_findings_confidence_range'), sa.CheckConstraint("severity IN ('info', 'low', 'medium', 'high', 'critical')", name='ck_parsed_findings_severity'))
    op.create_index('ix_parsed_findings_scan_id','parsed_findings',['scan_id'])
    op.create_table('parsed_signals',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')), sa.Column('service_id', sa.String(), sa.ForeignKey('parsed_services.id')), sa.Column('finding_id', sa.String(), sa.ForeignKey('parsed_findings.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('signal', sa.String(length=120), nullable=False), sa.Column('value', sa.Text(), nullable=False), sa.Column('confidence', sa.Float(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_signals_confidence_range'))
    op.create_index('ix_parsed_signals_scan_id','parsed_signals',['scan_id']); op.create_index('ix_parsed_signals_signal','parsed_signals',['signal'])
    op.create_table('parse_diagnostics',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('level', sa.String(length=40), nullable=False), sa.Column('message', sa.Text(), nullable=False), sa.Column('details_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_index('ix_parse_diagnostics_scan_id','parse_diagnostics',['scan_id'])

def downgrade() -> None:
    op.drop_table('parse_diagnostics'); op.drop_table('parsed_signals'); op.drop_table('parsed_findings'); op.drop_table('parsed_services'); op.drop_table('parsed_assets')
