from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import ParsedAsset, ParsedFinding, ParseDiagnostic, ParsedService, ParsedSignal, Scan
from app.db.session import get_db
from app.parsing.schemas import (
    ParsedAssetRead,
    ParsedFindingRead,
    ParseDiagnosticRead,
    ParsedServiceRead,
    ParsedSignalRead,
    ParsePersistedResult,
)
from app.parsing.service import parse_persisted_scan

router = APIRouter(prefix='/v2/scans', tags=['v2-parsing'])


def _scan_or_404(db: Session, scan_id: str):
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail='Scan not found')
    return scan


@router.post('/{scan_id}/parse-persisted', response_model=ParsePersistedResult)
def parse_persisted(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    try:
        return parse_persisted_scan(db, scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/{scan_id}/parsed/assets', response_model=list[ParsedAssetRead])
def assets(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(ParsedAsset).filter_by(scan_id=scan_id).order_by(ParsedAsset.ip_address.asc()).all()


@router.get('/{scan_id}/parsed/services', response_model=list[ParsedServiceRead])
def services(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return (
        db.query(ParsedService)
        .filter_by(scan_id=scan_id)
        .order_by(ParsedService.ip_address.asc(), ParsedService.port.asc())
        .all()
    )


@router.get('/{scan_id}/parsed/findings', response_model=list[ParsedFindingRead])
def findings(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(ParsedFinding).filter_by(scan_id=scan_id).order_by(ParsedFinding.created_at.asc()).all()


@router.get('/{scan_id}/parsed/signals', response_model=list[ParsedSignalRead])
def signals(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(ParsedSignal).filter_by(scan_id=scan_id).order_by(ParsedSignal.signal.asc()).all()


@router.get('/{scan_id}/parsed/diagnostics', response_model=list[ParseDiagnosticRead])
def diagnostics(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return db.query(ParseDiagnostic).filter_by(scan_id=scan_id).order_by(ParseDiagnostic.created_at.asc()).all()


from app.db.models import ParsedADObject, ParsedADRelation, ParsedAttackPath, ParsedCredentialRisk, ScanArtifact
from app.normalization.service import normalize_artifact, normalize_job_outputs
from app.parsing.schemas import (
    NormalizationResultRead,
    NormalizedSummaryRead,
    ParsedADObjectRead,
    ParsedADRelationRead,
    ParsedAttackPathRead,
    ParsedCredentialRiskRead,
)


@router.post('/{scan_id}/normalize', response_model=NormalizationResultRead)
def normalize_scan(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return normalize_job_outputs(db, scan_id).as_dict()


@router.post('/{scan_id}/artifacts/{artifact_id}/normalize', response_model=NormalizationResultRead)
def normalize_one_artifact(scan_id: str, artifact_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    artifact = db.get(ScanArtifact, artifact_id)
    if artifact is None or artifact.scan_id != scan_id:
        raise HTTPException(status_code=404, detail='Artifact not found')
    return normalize_artifact(db, artifact).as_dict()


@router.get('/{scan_id}/normalized/summary', response_model=NormalizedSummaryRead)
def normalized_summary(scan_id: str, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return {
        'scan_id': scan_id,
        'assets_count': db.query(ParsedAsset).filter_by(scan_id=scan_id).count(),
        'services_count': db.query(ParsedService).filter_by(scan_id=scan_id).count(),
        'findings_count': db.query(ParsedFinding).filter_by(scan_id=scan_id).count(),
        'signals_count': db.query(ParsedSignal).filter_by(scan_id=scan_id).count(),
        'diagnostics_count': db.query(ParseDiagnostic).filter_by(scan_id=scan_id).count(),
        'ad_objects_count': db.query(ParsedADObject).filter_by(scan_id=scan_id).count(),
        'high_value_targets_count': db.query(ParsedADObject).filter_by(scan_id=scan_id, high_value=True).count(),
        'ad_relations_count': db.query(ParsedADRelation).filter_by(scan_id=scan_id).count(),
        'attack_paths_count': db.query(ParsedAttackPath).filter_by(scan_id=scan_id).count(),
        'credential_risks_count': db.query(ParsedCredentialRisk).filter_by(scan_id=scan_id).count(),
        'critical_findings_count': db.query(ParsedFinding).filter_by(scan_id=scan_id, severity='critical').count(),
        'exposed_services_count': db.query(ParsedService).filter_by(scan_id=scan_id, state='open').count(),
    }


def _paged(q, limit, offset):
    return q.offset(offset).limit(limit).all()


@router.get('/{scan_id}/normalized/ad-objects', response_model=list[ParsedADObjectRead])
def ad_objects(scan_id: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return _paged(
        db.query(ParsedADObject).filter_by(scan_id=scan_id).order_by(ParsedADObject.name.asc()), limit, offset
    )


@router.get('/{scan_id}/normalized/ad-relations', response_model=list[ParsedADRelationRead])
def ad_relations(scan_id: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return _paged(
        db.query(ParsedADRelation).filter_by(scan_id=scan_id).order_by(ParsedADRelation.relation_type.asc()),
        limit,
        offset,
    )


@router.get('/{scan_id}/normalized/attack-paths', response_model=list[ParsedAttackPathRead])
def attack_paths(scan_id: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return _paged(
        db.query(ParsedAttackPath).filter_by(scan_id=scan_id).order_by(ParsedAttackPath.risk_level.desc()),
        limit,
        offset,
    )


@router.get('/{scan_id}/normalized/credential-risks', response_model=list[ParsedCredentialRiskRead])
def credential_risks(scan_id: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    _scan_or_404(db, scan_id)
    return _paged(
        db.query(ParsedCredentialRisk).filter_by(scan_id=scan_id).order_by(ParsedCredentialRisk.risk_level.desc()),
        limit,
        offset,
    )
