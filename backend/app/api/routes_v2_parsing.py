from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.models import ParseDiagnostic, ParsedAsset, ParsedFinding, ParsedService, ParsedSignal, Scan
from app.db.session import get_db
from app.parsing.schemas import ParseDiagnosticRead, ParsedAssetRead, ParsedFindingRead, ParsedServiceRead, ParsedSignalRead, ParsePersistedResult
from app.parsing.service import parse_persisted_scan

router = APIRouter(prefix='/v2/scans', tags=['v2-parsing'])

def _scan_or_404(db: Session, scan_id: str):
    scan=db.get(Scan, scan_id)
    if scan is None: raise HTTPException(status_code=404, detail='Scan not found')
    return scan

@router.post('/{scan_id}/parse-persisted', response_model=ParsePersistedResult)
def parse_persisted(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    try: return parse_persisted_scan(db, scan_id)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@router.get('/{scan_id}/parsed/assets', response_model=list[ParsedAssetRead])
def assets(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id); return db.query(ParsedAsset).filter_by(scan_id=scan_id).order_by(ParsedAsset.ip_address.asc()).all()

@router.get('/{scan_id}/parsed/services', response_model=list[ParsedServiceRead])
def services(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id); return db.query(ParsedService).filter_by(scan_id=scan_id).order_by(ParsedService.ip_address.asc(), ParsedService.port.asc()).all()

@router.get('/{scan_id}/parsed/findings', response_model=list[ParsedFindingRead])
def findings(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id); return db.query(ParsedFinding).filter_by(scan_id=scan_id).order_by(ParsedFinding.created_at.asc()).all()

@router.get('/{scan_id}/parsed/signals', response_model=list[ParsedSignalRead])
def signals(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id); return db.query(ParsedSignal).filter_by(scan_id=scan_id).order_by(ParsedSignal.signal.asc()).all()

@router.get('/{scan_id}/parsed/diagnostics', response_model=list[ParseDiagnosticRead])
def diagnostics(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id); return db.query(ParseDiagnostic).filter_by(scan_id=scan_id).order_by(ParseDiagnostic.created_at.asc()).all()
