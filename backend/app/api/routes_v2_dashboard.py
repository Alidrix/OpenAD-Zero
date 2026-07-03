from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.dashboard.schemas import V2DashboardSummary
from app.dashboard.service import build_v2_dashboard_summary
from app.db.session import get_db

router = APIRouter(prefix='/v2/dashboard', tags=['v2-dashboard'])


@router.get('/summary', response_model=V2DashboardSummary)
def dashboard_summary(
    include_deleted: bool = False,
    scan_id: str | None = None,
    limit_recent: int = Query(default=5, ge=0, le=50),
    db: Session = Depends(get_db),
):
    try:
        return build_v2_dashboard_summary(db, include_deleted=include_deleted, scan_id=scan_id, limit_recent=limit_recent)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail='Scan not found') from exc
