from sqlalchemy.orm import Session

from app.db.models import MissionTimelineEvent
from app.operations.defaults import TIMELINE_SEVERITIES, TIMELINE_SOURCES
from app.operations.schemas import TimelineEventCreate


def create_timeline_event(db: Session, mission_id: str, event: TimelineEventCreate) -> MissionTimelineEvent:
    if event.source not in TIMELINE_SOURCES:
        raise ValueError('Invalid timeline source')
    if event.severity not in TIMELINE_SEVERITIES:
        raise ValueError('Invalid timeline severity')
    row = MissionTimelineEvent(mission_id=mission_id, **event.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_timeline_events(
    db: Session, mission_id: str, source: str | None = None, severity: str | None = None, limit: int = 200
) -> list[MissionTimelineEvent]:
    if source and source not in TIMELINE_SOURCES:
        raise ValueError('Invalid timeline source')
    if severity and severity not in TIMELINE_SEVERITIES:
        raise ValueError('Invalid timeline severity')
    q = db.query(MissionTimelineEvent).filter_by(mission_id=mission_id)
    if source:
        q = q.filter_by(source=source)
    if severity:
        q = q.filter_by(severity=severity)
    return q.order_by(MissionTimelineEvent.created_at.desc()).limit(min(max(limit, 1), 1000)).all()
