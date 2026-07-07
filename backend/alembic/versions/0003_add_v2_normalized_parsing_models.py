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

def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())

def _indexes(table: str) -> set[str]:
    if table not in _tables():
        return set()
    return {i['name'] for i in sa.inspect(op.get_bind()).get_indexes(table)}

def _create_index(name: str, table: str, cols: list[str]) -> None:
    if name not in _indexes(table):
        op.create_index(name, table, cols)

def upgrade() -> None:
    existing = _tables()
    if 'parsed_assets' not in existing:
        op.create_table('parsed_assets',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(length=80), nullable=False), sa.Column('hostname', sa.String(length=255)), sa.Column('fqdn', sa.String(length=255)),
        sa.Column('mac_address', sa.String(length=80)), sa.Column('os_family', sa.String(length=80)), sa.Column('os_name', sa.String(length=255)),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_assets_confidence_range'))
    _create_index('ix_parsed_assets_scan_id','parsed_assets',['scan_id']); _create_index('ix_parsed_assets_ip_address','parsed_assets',['ip_address'])
    if 'parsed_services' not in existing:
        op.create_table('parsed_services',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('ip_address', sa.String(length=80), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False), sa.Column('protocol', sa.String(length=20), nullable=False), sa.Column('service_name', sa.String(length=120)), sa.Column('product', sa.String(length=255)), sa.Column('version', sa.String(length=255)), sa.Column('state', sa.String(length=40), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_services_confidence_range'))
    for col in ['scan_id','ip_address','port','protocol']: _create_index(f'ix_parsed_services_{col}','parsed_services',[col])
    if 'parsed_findings' not in existing:
        op.create_table('parsed_findings',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')), sa.Column('service_id', sa.String(), sa.ForeignKey('parsed_services.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('title', sa.String(length=255), nullable=False), sa.Column('description', sa.Text(), nullable=False), sa.Column('severity', sa.String(length=40), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False), sa.Column('tags_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False), sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_findings_confidence_range'), sa.CheckConstraint("severity IN ('info', 'low', 'medium', 'high', 'critical')", name='ck_parsed_findings_severity'))
    _create_index('ix_parsed_findings_scan_id','parsed_findings',['scan_id'])
    if 'parsed_signals' not in existing:
        op.create_table('parsed_signals',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('asset_id', sa.String(), sa.ForeignKey('parsed_assets.id')), sa.Column('service_id', sa.String(), sa.ForeignKey('parsed_services.id')), sa.Column('finding_id', sa.String(), sa.ForeignKey('parsed_findings.id')),
        sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('signal', sa.String(length=120), nullable=False), sa.Column('value', sa.Text(), nullable=False), sa.Column('confidence', sa.Float(), nullable=False), sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_signals_confidence_range'))
    _create_index('ix_parsed_signals_scan_id','parsed_signals',['scan_id']); _create_index('ix_parsed_signals_signal','parsed_signals',['signal'])
    if 'parse_diagnostics' not in existing:
        op.create_table('parse_diagnostics',
        sa.Column('id', sa.String(), primary_key=True), sa.Column('scan_id', sa.String(), sa.ForeignKey('scans.id'), nullable=False), sa.Column('source_type', sa.String(length=80), nullable=False), sa.Column('source_id', sa.String()), sa.Column('level', sa.String(length=40), nullable=False), sa.Column('message', sa.Text(), nullable=False), sa.Column('details_json', sa.JSON()), sa.Column('created_at', sa.DateTime(), nullable=False))
    _create_index('ix_parse_diagnostics_scan_id','parse_diagnostics',['scan_id'])

def downgrade() -> None:
    for table in ['parse_diagnostics','parsed_signals','parsed_findings','parsed_services','parsed_assets']:
        if table in _tables():
            op.drop_table(table)
