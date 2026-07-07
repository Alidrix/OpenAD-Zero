"""add v2 ad normalized models

Revision ID: 0006_add_v2_ad_normalized_models
Revises: 0006_add_approved_action_runs, 0006_add_pentest_decision_rule_metadata
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_add_v2_ad_normalized_models'
down_revision = ('0006_add_approved_action_runs', '0006_add_pentest_decision_rule_metadata')
branch_labels = None
depends_on = None

def _tables(): return set(sa.inspect(op.get_bind()).get_table_names())
def _idx(table): return {i['name'] for i in sa.inspect(op.get_bind()).get_indexes(table)} if table in _tables() else set()
def _create_idx(table, mapping):
    existing=_idx(table)
    for name, cols in mapping.items():
        if name not in existing: op.create_index(name, table, cols)

def upgrade() -> None:
    t=_tables()
    if 'parsed_ad_objects' not in t:
        op.create_table('parsed_ad_objects', sa.Column('id',sa.String(),primary_key=True), sa.Column('scan_id',sa.String(),sa.ForeignKey('scans.id'),nullable=False), sa.Column('source_type',sa.String(80),nullable=False), sa.Column('source_id',sa.String(),nullable=True), sa.Column('object_id',sa.String(255)), sa.Column('object_type',sa.String(80),nullable=False), sa.Column('name',sa.String(255)), sa.Column('domain',sa.String(255)), sa.Column('distinguished_name',sa.Text()), sa.Column('sam_account_name',sa.String(255)), sa.Column('sid',sa.String(255)), sa.Column('enabled',sa.Boolean()), sa.Column('high_value',sa.Boolean(),nullable=False,server_default='0'), sa.Column('owned',sa.Boolean(),nullable=False,server_default='0'), sa.Column('properties_json',sa.JSON()), sa.Column('created_at',sa.DateTime()), sa.Column('updated_at',sa.DateTime()))
    _create_idx('parsed_ad_objects', {'ix_parsed_ad_objects_scan_id':['scan_id'],'ix_parsed_ad_objects_source_type':['source_type'],'ix_parsed_ad_objects_source_id':['source_id'],'ix_parsed_ad_objects_object_id':['object_id'],'ix_parsed_ad_objects_object_type':['object_type'],'ix_parsed_ad_objects_domain':['domain']})
    if 'parsed_ad_relations' not in t:
        op.create_table('parsed_ad_relations', sa.Column('id',sa.String(),primary_key=True), sa.Column('scan_id',sa.String(),sa.ForeignKey('scans.id'),nullable=False), sa.Column('source_type',sa.String(80),nullable=False), sa.Column('source_id',sa.String()), sa.Column('source_object_id',sa.String(255),nullable=False), sa.Column('target_object_id',sa.String(255),nullable=False), sa.Column('relation_type',sa.String(120),nullable=False), sa.Column('is_abusable',sa.Boolean(),nullable=False,server_default='0'), sa.Column('risk_level',sa.String(40),nullable=False), sa.Column('properties_json',sa.JSON()), sa.Column('created_at',sa.DateTime()), sa.Column('updated_at',sa.DateTime()))
    _create_idx('parsed_ad_relations', {'ix_parsed_ad_relations_scan_id':['scan_id'],'ix_parsed_ad_relations_source_type':['source_type'],'ix_parsed_ad_relations_source_id':['source_id'],'ix_parsed_ad_relations_relation_type':['relation_type'],'ix_parsed_ad_relations_risk_level':['risk_level'],'ix_parsed_ad_relations_target_object_id':['target_object_id']})
    if 'parsed_attack_paths' not in t:
        op.create_table('parsed_attack_paths', sa.Column('id',sa.String(),primary_key=True), sa.Column('scan_id',sa.String(),sa.ForeignKey('scans.id'),nullable=False), sa.Column('source_type',sa.String(80),nullable=False), sa.Column('source_id',sa.String()), sa.Column('path_type',sa.String(120),nullable=False), sa.Column('source_object_id',sa.String(255)), sa.Column('target_object_id',sa.String(255)), sa.Column('target_label',sa.String(255)), sa.Column('risk_level',sa.String(40),nullable=False), sa.Column('length',sa.Integer(),nullable=False,server_default='0'), sa.Column('nodes_json',sa.JSON()), sa.Column('edges_json',sa.JSON()), sa.Column('summary',sa.Text()), sa.Column('created_at',sa.DateTime()), sa.Column('updated_at',sa.DateTime()))
    _create_idx('parsed_attack_paths', {'ix_parsed_attack_paths_scan_id':['scan_id'],'ix_parsed_attack_paths_source_type':['source_type'],'ix_parsed_attack_paths_source_id':['source_id'],'ix_parsed_attack_paths_risk_level':['risk_level'],'ix_parsed_attack_paths_target_object_id':['target_object_id']})
    if 'parsed_credential_risks' not in t:
        op.create_table('parsed_credential_risks', sa.Column('id',sa.String(),primary_key=True), sa.Column('scan_id',sa.String(),sa.ForeignKey('scans.id'),nullable=False), sa.Column('source_type',sa.String(80),nullable=False), sa.Column('source_id',sa.String()), sa.Column('risk_type',sa.String(120),nullable=False), sa.Column('principal',sa.String(255)), sa.Column('asset_ip',sa.String(80)), sa.Column('domain',sa.String(255)), sa.Column('risk_level',sa.String(40),nullable=False), sa.Column('evidence',sa.Text()), sa.Column('properties_json',sa.JSON()), sa.Column('created_at',sa.DateTime()), sa.Column('updated_at',sa.DateTime()))
    _create_idx('parsed_credential_risks', {'ix_parsed_credential_risks_scan_id':['scan_id'],'ix_parsed_credential_risks_source_type':['source_type'],'ix_parsed_credential_risks_source_id':['source_id'],'ix_parsed_credential_risks_risk_type':['risk_type'],'ix_parsed_credential_risks_risk_level':['risk_level'],'ix_parsed_credential_risks_domain':['domain']})

def downgrade() -> None:
    for table in ['parsed_credential_risks','parsed_attack_paths','parsed_ad_relations','parsed_ad_objects']:
        if table in _tables(): op.drop_table(table)
