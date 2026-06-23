import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def uid(): return str(uuid.uuid4())
class Mission(Base):
    __tablename__='missions'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); name:Mapped[str]=mapped_column(String(200)); scenario:Mapped[str]=mapped_column(String(100)); mode:Mapped[str]=mapped_column(String(50), default='safe'); status:Mapped[str]=mapped_column(String(40), default='created'); raw_scope:Mapped[str]=mapped_column(Text); validated_targets:Mapped[list]=mapped_column(JSON); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow); started_at:Mapped[datetime|None]=mapped_column(DateTime); completed_at:Mapped[datetime|None]=mapped_column(DateTime)
    jobs=relationship('Job', cascade='all, delete-orphan'); hosts=relationship('Host', cascade='all, delete-orphan'); findings=relationship('Finding', cascade='all, delete-orphan'); next_actions=relationship('NextAction', cascade='all, delete-orphan')
class Job(Base):
    __tablename__='jobs'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); type:Mapped[str]=mapped_column(String(50)); tool:Mapped[str]=mapped_column(String(50)); status:Mapped[str]=mapped_column(String(40), default='pending'); command_preview:Mapped[str]=mapped_column(Text); started_at:Mapped[datetime|None]=mapped_column(DateTime); completed_at:Mapped[datetime|None]=mapped_column(DateTime); return_code:Mapped[int|None]=mapped_column(Integer); stdout_path:Mapped[str|None]=mapped_column(Text); stderr_path:Mapped[str|None]=mapped_column(Text); output_path:Mapped[str|None]=mapped_column(Text)
class Host(Base):
    __tablename__='hosts'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); ip:Mapped[str]=mapped_column(String(80)); hostname:Mapped[str|None]=mapped_column(String(255)); status:Mapped[str]=mapped_column(String(40)); os_guess:Mapped[str|None]=mapped_column(String(255)); is_domain_controller_candidate:Mapped[bool]=mapped_column(Boolean, default=False); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    services=relationship('Service', cascade='all, delete-orphan')
class Service(Base):
    __tablename__='services'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); host_id:Mapped[str]=mapped_column(ForeignKey('hosts.id')); port:Mapped[int]=mapped_column(Integer); protocol:Mapped[str]=mapped_column(String(20)); name:Mapped[str]=mapped_column(String(100)); product:Mapped[str]=mapped_column(String(255)); version:Mapped[str]=mapped_column(String(255)); state:Mapped[str]=mapped_column(String(40))
class Finding(Base):
    __tablename__='findings'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); host_id:Mapped[str|None]=mapped_column(ForeignKey('hosts.id')); title:Mapped[str]=mapped_column(String(255)); severity:Mapped[str]=mapped_column(String(40)); description:Mapped[str]=mapped_column(Text); source:Mapped[str]=mapped_column(String(80)); confidence:Mapped[str]=mapped_column(String(40)); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class NextAction(Base):
    __tablename__='next_actions'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); title:Mapped[str]=mapped_column(String(255)); description:Mapped[str]=mapped_column(Text); reason:Mapped[str]=mapped_column(Text); risk_level:Mapped[int]=mapped_column(Integer); requires_approval:Mapped[bool]=mapped_column(Boolean, default=True); status:Mapped[str]=mapped_column(String(40), default='proposed'); command_template_id:Mapped[str|None]=mapped_column(String(120)); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class SMBFact(Base):
    __tablename__='smb_facts'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); host_id:Mapped[str|None]=mapped_column(ForeignKey('hosts.id')); ip:Mapped[str]=mapped_column(String(80)); hostname:Mapped[str|None]=mapped_column(String(255)); domain:Mapped[str|None]=mapped_column(String(255)); os:Mapped[str|None]=mapped_column(String(255)); smb_signing_required:Mapped[bool|None]=mapped_column(Boolean); smbv1_enabled:Mapped[bool|None]=mapped_column(Boolean); null_session_possible:Mapped[bool|None]=mapped_column(Boolean); source:Mapped[str]=mapped_column(String(80), default='netexec'); raw_line:Mapped[str|None]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
class SMBShare(Base):
    __tablename__='smb_shares'
    id:Mapped[str]=mapped_column(String, primary_key=True, default=uid); mission_id:Mapped[str]=mapped_column(ForeignKey('missions.id')); host_id:Mapped[str|None]=mapped_column(ForeignKey('hosts.id')); ip:Mapped[str]=mapped_column(String(80)); name:Mapped[str]=mapped_column(String(255)); access:Mapped[str|None]=mapped_column(String(80)); remark:Mapped[str|None]=mapped_column(Text); anonymous:Mapped[bool]=mapped_column(Boolean, default=True); source:Mapped[str]=mapped_column(String(80), default='netexec'); created_at:Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
