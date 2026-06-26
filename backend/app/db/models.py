import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
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
