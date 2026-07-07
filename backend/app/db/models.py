import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def uid():
    return str(uuid.uuid4())


class Mission(Base):
    __tablename__ = 'missions'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    scenario: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(50), default='safe')
    status: Mapped[str] = mapped_column(String(40), default='created')
    raw_scope: Mapped[str] = mapped_column(Text)
    validated_targets: Mapped[list] = mapped_column(JSON)
    client_name: Mapped[str | None] = mapped_column(String(255))
    scope: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    jobs = relationship('Job', cascade='all, delete-orphan')
    hosts = relationship('Host', cascade='all, delete-orphan')
    findings = relationship('Finding', cascade='all, delete-orphan')
    next_actions = relationship('NextAction', cascade='all, delete-orphan')
    smb_facts = relationship('SMBFact', cascade='all, delete-orphan')
    smb_shares = relationship('SMBShare', cascade='all, delete-orphan')
    web_targets = relationship('WebTarget', cascade='all, delete-orphan')
    bloodhound_collections = relationship('BloodHoundCollection', cascade='all, delete-orphan')
    bloodhound_stats = relationship('BloodHoundStat', cascade='all, delete-orphan')
    manual_action_cards = relationship('ManualActionCard', cascade='all, delete-orphan')
    evidence = relationship('Evidence', cascade='all, delete-orphan')
    evidence_links = relationship('EvidenceLink', cascade='all, delete-orphan')
    reports = relationship('Report', cascade='all, delete-orphan')
    objective = relationship('MissionObjective', cascade='all, delete-orphan')
    phases = relationship('MissionPhase', cascade='all, delete-orphan')
    timeline_events = relationship('MissionTimelineEvent', cascade='all, delete-orphan')
    scans = relationship('Scan', cascade='all, delete-orphan')


class Scan(Base):
    __tablename__ = 'scans'
    __table_args__ = (
        CheckConstraint('progress_percent >= 0 AND progress_percent <= 100', name='ck_scans_progress_percent_range'),
        Index('ix_scans_status', 'status'),
        Index('ix_scans_created_at', 'created_at'),
        Index('ix_scans_deleted_at', 'deleted_at'),
        Index('ix_scans_mission_id', 'mission_id'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str | None] = mapped_column(ForeignKey('missions.id'), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    scan_type: Mapped[str] = mapped_column(String(120))
    tool_name: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default='draft')
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(String(255))
    rq_job_id: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    renamed_at: Mapped[datetime | None] = mapped_column(DateTime)
    steps = relationship('ScanStep', cascade='all, delete-orphan')
    events = relationship('ScanEvent', cascade='all, delete-orphan')
    artifacts = relationship('ScanArtifact', cascade='all, delete-orphan')
    parsed_assets = relationship('ParsedAsset', cascade='all, delete-orphan')
    parsed_services = relationship('ParsedService', cascade='all, delete-orphan')
    parsed_findings = relationship('ParsedFinding', cascade='all, delete-orphan')
    parsed_signals = relationship('ParsedSignal', cascade='all, delete-orphan')
    parse_diagnostics = relationship('ParseDiagnostic', cascade='all, delete-orphan')


class ScanStep(Base):
    __tablename__ = 'scan_steps'
    __table_args__ = (
        CheckConstraint(
            'progress_percent >= 0 AND progress_percent <= 100', name='ck_scan_steps_progress_percent_range'
        ),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), default='pending')
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanEvent(Base):
    __tablename__ = 'scan_events'
    __table_args__ = (Index('ix_scan_events_scan_id', 'scan_id'), Index('ix_scan_events_created_at', 'created_at'))
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    event_type: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ScanArtifact(Base):
    __tablename__ = 'scan_artifacts'
    __table_args__ = (Index('ix_scan_artifacts_scan_id', 'scan_id'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    artifact_type: Mapped[str] = mapped_column(String(120))
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ParsedAsset(Base):
    __tablename__ = 'parsed_assets'
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_assets_confidence_range'),
        Index('ix_parsed_assets_scan_id', 'scan_id'),
        Index('ix_parsed_assets_ip_address', 'ip_address'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(80))
    hostname: Mapped[str | None] = mapped_column(String(255))
    fqdn: Mapped[str | None] = mapped_column(String(255))
    mac_address: Mapped[str | None] = mapped_column(String(80))
    os_family: Mapped[str | None] = mapped_column(String(80))
    os_name: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    tags_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ParsedService(Base):
    __tablename__ = 'parsed_services'
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_services_confidence_range'),
        Index('ix_parsed_services_scan_id', 'scan_id'),
        Index('ix_parsed_services_ip_address', 'ip_address'),
        Index('ix_parsed_services_port', 'port'),
        Index('ix_parsed_services_protocol', 'protocol'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_assets.id'), nullable=True)
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(80))
    port: Mapped[int] = mapped_column(Integer)
    protocol: Mapped[str] = mapped_column(String(20), default='tcp')
    service_name: Mapped[str | None] = mapped_column(String(120))
    product: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(40), default='open')
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    tags_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ParsedFinding(Base):
    __tablename__ = 'parsed_findings'
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_findings_confidence_range'),
        CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')", name='ck_parsed_findings_severity'
        ),
        Index('ix_parsed_findings_scan_id', 'scan_id'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_assets.id'), nullable=True)
    service_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_services.id'), nullable=True)
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(40), default='info')
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    tags_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ParsedSignal(Base):
    __tablename__ = 'parsed_signals'
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_parsed_signals_confidence_range'),
        Index('ix_parsed_signals_scan_id', 'scan_id'),
        Index('ix_parsed_signals_signal', 'signal'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_assets.id'), nullable=True)
    service_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_services.id'), nullable=True)
    finding_id: Mapped[str | None] = mapped_column(ForeignKey('parsed_findings.id'), nullable=True)
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    signal: Mapped[str] = mapped_column(String(120))
    value: Mapped[str] = mapped_column(Text, default='true')
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ParseDiagnostic(Base):
    __tablename__ = 'parse_diagnostics'
    __table_args__ = (Index('ix_parse_diagnostics_scan_id', 'scan_id'),)
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    source_type: Mapped[str] = mapped_column(String(80))
    source_id: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[str] = mapped_column(String(40), default='warning')
    message: Mapped[str] = mapped_column(Text)
    details_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = 'jobs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    type: Mapped[str] = mapped_column(String(50))
    tool: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(40), default='pending')
    command_preview: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    return_code: Mapped[int | None] = mapped_column(Integer)
    stdout_path: Mapped[str | None] = mapped_column(Text)
    stderr_path: Mapped[str | None] = mapped_column(Text)
    output_path: Mapped[str | None] = mapped_column(Text)
    rq_job_id: Mapped[str | None] = mapped_column(String(255))
    queued_at: Mapped[datetime | None] = mapped_column(DateTime)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    error_message: Mapped[str | None] = mapped_column(Text)


class JobLog(Base):
    __tablename__ = 'job_logs'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'))
    source: Mapped[str] = mapped_column(String(80), default='backend')
    stream: Mapped[str] = mapped_column(String(40), default='stdout')
    line: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MissionEvent(Base):
    __tablename__ = 'mission_events'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    event_type: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(80), default='system')
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    redis_stream_id: Mapped[str | None] = mapped_column(String(255))


class Host(Base):
    __tablename__ = 'hosts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    ip: Mapped[str] = mapped_column(String(80))
    hostname: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40))
    os_guess: Mapped[str | None] = mapped_column(String(255))
    is_domain_controller_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    services = relationship('Service', cascade='all, delete-orphan')


class Service(Base):
    __tablename__ = 'services'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    host_id: Mapped[str] = mapped_column(ForeignKey('hosts.id'))
    port: Mapped[int] = mapped_column(Integer)
    protocol: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(100))
    product: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(40))


class Finding(Base):
    __tablename__ = 'findings'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    host_id: Mapped[str | None] = mapped_column(ForeignKey('hosts.id'))
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80))
    confidence: Mapped[str] = mapped_column(String(40))
    template_id: Mapped[str | None] = mapped_column(String(255))
    template_name: Mapped[str | None] = mapped_column(String(255))
    matcher_name: Mapped[str | None] = mapped_column(String(255))
    matched_at: Mapped[str | None] = mapped_column(Text)
    host: Mapped[str | None] = mapped_column(String(255))
    ip: Mapped[str | None] = mapped_column(String(80))
    port: Mapped[int | None] = mapped_column(Integer)
    scheme: Mapped[str | None] = mapped_column(String(20))
    tags: Mapped[list | None] = mapped_column(JSON)
    references: Mapped[list | None] = mapped_column(JSON)
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    raw_event_path: Mapped[str | None] = mapped_column(Text)
    evidence_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NextAction(Base):
    __tablename__ = 'next_actions'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[int] = mapped_column(Integer)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(40), default='proposed')
    command_template_id: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ManualActionCard(Base):
    __tablename__ = 'manual_action_cards'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    capability_id: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), default='draft')
    operator_note: Mapped[str | None] = mapped_column(Text)
    evidence_reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Evidence(Base):
    __tablename__ = 'evidence'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    label: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), default='external')
    description: Mapped[str | None] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100), default='external_upload')
    preview_available: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceLink(Base):
    __tablename__ = 'evidence_links'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    evidence_id: Mapped[str] = mapped_column(ForeignKey('evidence.id'))
    target_type: Mapped[str] = mapped_column(String(80))
    target_id: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SMBFact(Base):
    __tablename__ = 'smb_facts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    host_id: Mapped[str | None] = mapped_column(ForeignKey('hosts.id'))
    ip: Mapped[str] = mapped_column(String(80))
    hostname: Mapped[str | None] = mapped_column(String(255))
    domain: Mapped[str | None] = mapped_column(String(255))
    os: Mapped[str | None] = mapped_column(String(255))
    smb_signing_required: Mapped[bool | None] = mapped_column(Boolean)
    smbv1_enabled: Mapped[bool | None] = mapped_column(Boolean)
    null_session_possible: Mapped[bool | None] = mapped_column(Boolean)
    source: Mapped[str] = mapped_column(String(80), default='netexec')
    raw_line: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SMBShare(Base):
    __tablename__ = 'smb_shares'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    host_id: Mapped[str | None] = mapped_column(ForeignKey('hosts.id'))
    ip: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(255))
    access: Mapped[str | None] = mapped_column(String(80))
    remark: Mapped[str | None] = mapped_column(Text)
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(80), default='netexec')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WebTarget(Base):
    __tablename__ = 'web_targets'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    host_id: Mapped[str] = mapped_column(ForeignKey('hosts.id'))
    url: Mapped[str] = mapped_column(String(500))
    ip: Mapped[str] = mapped_column(String(80))
    port: Mapped[int] = mapped_column(Integer)
    scheme: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(80), default='nmap')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BloodHoundCollection(Base):
    __tablename__ = 'bloodhound_collections'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    status: Mapped[str] = mapped_column(String(40), default='created')
    source: Mapped[str] = mapped_column(String(80), default='upload')
    filename: Mapped[str | None] = mapped_column(String(255))
    stored_path: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str | None] = mapped_column(String(64))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    zip_valid: Mapped[bool | None] = mapped_column(Boolean)
    zip_summary_json: Mapped[dict | None] = mapped_column(JSON)
    ingestion_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    ingestion_status: Mapped[str | None] = mapped_column(String(80))
    ingestion_job_id: Mapped[str | None] = mapped_column(String(255))
    ingestion_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime)
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime)


class BloodHoundStat(Base):
    __tablename__ = 'bloodhound_stats'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    collection_id: Mapped[str | None] = mapped_column(ForeignKey('bloodhound_collections.id'))
    domain_name: Mapped[str | None] = mapped_column(String(255))
    users_count: Mapped[int | None] = mapped_column(Integer)
    computers_count: Mapped[int | None] = mapped_column(Integer)
    groups_count: Mapped[int | None] = mapped_column(Integer)
    ous_count: Mapped[int | None] = mapped_column(Integer)
    gpos_count: Mapped[int | None] = mapped_column(Integer)
    domains_count: Mapped[int | None] = mapped_column(Integer)
    edges_count: Mapped[int | None] = mapped_column(Integer)
    raw_stats_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = 'reports'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    status: Mapped[str] = mapped_column(String(40), default='generated')
    title: Mapped[str] = mapped_column(String(255))
    markdown_path: Mapped[str | None] = mapped_column(Text)
    html_path: Mapped[str | None] = mapped_column(Text)
    metadata_path: Mapped[str | None] = mapped_column(Text)
    sections_json: Mapped[dict | None] = mapped_column(JSON)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MissionObjective(Base):
    __tablename__ = 'mission_objectives'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    objective_name: Mapped[str] = mapped_column(String(255))
    objective_description: Mapped[str | None] = mapped_column(Text)
    objective_type: Mapped[str] = mapped_column(String(80), default='domain_admin_path')
    objective_target: Mapped[str | None] = mapped_column(String(255))
    objective_status: Mapped[str] = mapped_column(String(80), default='not_started')
    operator_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MissionPhase(Base):
    __tablename__ = 'mission_phases'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    phase_key: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default='pending')
    order_index: Mapped[int] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MissionTimelineEvent(Base):
    __tablename__ = 'mission_timeline_events'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    mission_id: Mapped[str] = mapped_column(ForeignKey('missions.id'))
    event_type: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default='system')
    severity: Mapped[str] = mapped_column(String(40), default='info')
    related_host_id: Mapped[str | None] = mapped_column(String(120))
    related_service_id: Mapped[str | None] = mapped_column(String(120))
    related_finding_id: Mapped[str | None] = mapped_column(String(120))
    related_evidence_id: Mapped[str | None] = mapped_column(String(120))
    related_job_id: Mapped[str | None] = mapped_column(String(120))
    related_report_id: Mapped[str | None] = mapped_column(String(120))
    related_bloodhound_collection_id: Mapped[str | None] = mapped_column(String(120))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PentestPhaseState(Base):
    __tablename__ = 'pentest_phase_states'
    __table_args__ = (
        Index('ix_pentest_phase_states_scan_id', 'scan_id'),
        Index('ix_pentest_phase_states_mission_id', 'mission_id'),
        Index('ix_pentest_phase_states_phase_id', 'phase_id'),
        Index('ix_pentest_phase_states_status', 'status'),
        Index('ix_pentest_phase_states_risk_level', 'risk_level'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    mission_id: Mapped[str | None] = mapped_column(ForeignKey('missions.id'), nullable=True)
    phase_id: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default='not_started')
    summary: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(40), default='info')
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PentestAction(Base):
    __tablename__ = 'pentest_actions'
    __table_args__ = (
        Index('ix_pentest_actions_scan_id', 'scan_id'),
        Index('ix_pentest_actions_mission_id', 'mission_id'),
        Index('ix_pentest_actions_phase_id', 'phase_id'),
        Index('ix_pentest_actions_status', 'status'),
        Index('ix_pentest_actions_risk_level', 'risk_level'),
        Index('ix_pentest_actions_execution_mode', 'execution_mode'),
        Index('ix_pentest_actions_tool_id', 'tool_id'),
        Index('ix_pentest_actions_template_id', 'template_id'),
        Index('ix_pentest_actions_dedupe_key', 'dedupe_key'),
        Index('ix_pentest_actions_priority', 'priority'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    mission_id: Mapped[str | None] = mapped_column(ForeignKey('missions.id'), nullable=True)
    phase_id: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(40), default='low')
    execution_mode: Mapped[str] = mapped_column(String(60), default='approval_required')
    tool_id: Mapped[str] = mapped_column(String(120))
    template_id: Mapped[str] = mapped_column(String(160))
    required_inputs_json: Mapped[list | None] = mapped_column(JSON)
    resolved_inputs_json: Mapped[dict | None] = mapped_column(JSON)
    missing_inputs_json: Mapped[list | None] = mapped_column(JSON)
    scope_sensitive_params_json: Mapped[dict | None] = mapped_column(JSON)
    dedupe_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=20)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default='proposed')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperatorApproval(Base):
    __tablename__ = 'operator_approvals'
    __table_args__ = (
        CheckConstraint(
            "approval_level IN ('standard', 'reinforced', 'manual_only_blocked')",
            name='ck_operator_approvals_approval_level',
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired', 'consumed', 'blocked')",
            name='ck_operator_approvals_status',
        ),
        Index('ix_operator_approvals_scan_id', 'scan_id'),
        Index('ix_operator_approvals_mission_id', 'mission_id'),
        Index('ix_operator_approvals_action_id', 'action_id'),
        Index('ix_operator_approvals_status', 'status'),
        Index('ix_operator_approvals_tool_id', 'tool_id'),
        Index('ix_operator_approvals_template_id', 'template_id'),
        Index('ix_operator_approvals_command_hash', 'command_hash'),
        Index('ix_operator_approvals_expires_at', 'expires_at'),
    )
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uid)
    scan_id: Mapped[str] = mapped_column(ForeignKey('scans.id'))
    mission_id: Mapped[str | None] = mapped_column(ForeignKey('missions.id'), nullable=True)
    action_id: Mapped[str] = mapped_column(ForeignKey('pentest_actions.id'))
    phase_id: Mapped[str] = mapped_column(String(120))
    tool_id: Mapped[str] = mapped_column(String(120))
    template_id: Mapped[str] = mapped_column(String(160))
    command_hash: Mapped[str] = mapped_column(String(64))
    masked_preview_json: Mapped[dict] = mapped_column(JSON)
    resolved_inputs_json: Mapped[dict | None] = mapped_column(JSON)
    missing_inputs_json: Mapped[list | None] = mapped_column(JSON)
    scope_snapshot_json: Mapped[dict | None] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(40), default='low')
    approval_level: Mapped[str] = mapped_column(String(40), default='standard')
    status: Mapped[str] = mapped_column(String(40), default='pending')
    approved_by: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
