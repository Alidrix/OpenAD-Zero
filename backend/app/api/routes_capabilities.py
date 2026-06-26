from fastapi import APIRouter, HTTPException, Query

from app.capabilities.catalog import CapabilityCatalogError, get_capability, load_capabilities
from app.capabilities.policy import disabled_reason, is_executable, is_visible
from app.capabilities.schemas import Capability, CapabilityConfig
from app.core.config import get_settings
from app.core.errors import error_response

router = APIRouter(prefix='/capabilities', tags=['capabilities'])


def _config() -> CapabilityConfig:
    settings = get_settings()
    return CapabilityConfig(
        default_mode=settings.openadzero_default_mode,
        assisted_mode_enabled=settings.openadzero_enable_assisted_mode,
        ctf_lab_mode_enabled=settings.openadzero_enable_ctf_lab_mode,
        manual_action_cards_enabled=settings.openadzero_enable_manual_action_cards,
        external_evidence_import_enabled=settings.openadzero_enable_external_evidence_import,
        reporting_enabled=settings.openadzero_enable_reporting,
        ai_planner_enabled=settings.openadzero_enable_ai_planner,
        advanced_automation_enabled=settings.openadzero_enable_advanced_automation,
    )


def _serialize(capability: Capability, include_reason: bool = False) -> dict:
    config = _config()
    data = capability.model_dump()
    data['executable'] = is_executable(capability, config)
    data['visible'] = is_visible(capability, config)
    if include_reason:
        data['disabled_reason'] = disabled_reason(capability, config)
    return data


def _catalog_or_500() -> list[Capability]:
    try:
        return load_capabilities()
    except CapabilityCatalogError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get('')
def capabilities(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    q: str | None = Query(default=None),
):
    capabilities = _catalog_or_500()
    if status:
        capabilities = [c for c in capabilities if c.status == status]
    if category:
        capabilities = [c for c in capabilities if c.category == category]
    if mode:
        capabilities = [c for c in capabilities if c.mode == mode]
    if q:
        needle = q.lower()
        capabilities = [
            c
            for c in capabilities
            if needle in c.name.lower() or needle in c.description.lower() or needle in c.id.lower()
        ]
    return [_serialize(c) for c in capabilities]


@router.get('/config')
def capabilities_config() -> CapabilityConfig:
    return _config()


@router.get('/{capability_id}')
def capability(capability_id: str):
    try:
        item = get_capability(capability_id)
    except CapabilityCatalogError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail=error_response('capability_not_found', 'Capability not found'))
    return _serialize(item, include_reason=True)
