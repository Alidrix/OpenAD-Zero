from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import ScanArtifact, ScanEvent
from app.db.session import get_db
from app.recommendations.catalog_loader import get_catalog
from app.recommendations.engine import build_recommendations
from app.recommendations.models import (
    V2CommandPreview,
    V2PreviewRequest,
    V2Recommendation,
)
from app.recommendations.preview_builder import PreviewBuildError, build_preview
from app.services import scan_service

router = APIRouter(tags=["v2-recommendations"])


def _scan_or_404(db: Session, scan_id: str):
    scan = scan_service.get_scan(db, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/v2/recommendations/catalog")
def recommendation_catalog():
    templates, rules, policy = get_catalog()
    return {
        "templates": templates,
        "rules": rules,
        "safety_policy": {
            "defaults": policy.get("defaults", {}),
            "blocked_categories": policy.get("blocked_categories", []),
            "allowed_modes": policy.get("allowed_modes", []),
            "v2_current_execution_policy": policy.get(
                "v2_current_execution_policy", {}
            ),
        },
    }


@router.get(
    "/v2/scans/{scan_id}/recommendations", response_model=list[V2Recommendation]
)
def scan_recommendations(scan_id: str, db: Session = Depends(get_db)):
    scan = _scan_or_404(db, scan_id)
    events = (
        db.query(ScanEvent)
        .filter_by(scan_id=scan_id)
        .order_by(ScanEvent.created_at.asc())
        .all()
    )
    artifacts = (
        db.query(ScanArtifact)
        .filter_by(scan_id=scan_id)
        .order_by(ScanArtifact.created_at.asc())
        .all()
    )
    return build_recommendations(scan, events, artifacts)


@router.post("/v2/recommendations/preview", response_model=V2CommandPreview)
def command_preview(payload: V2PreviewRequest):
    try:
        return build_preview(payload.template_id, payload.params)
    except PreviewBuildError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
