from fastapi import APIRouter, HTTPException
from app.capabilities.catalog import list_capabilities, get_capability
from app.core.config import get_settings

router=APIRouter(prefix='/capabilities')

def _ser(c): return c.model_dump()

@router.get('')
def capabilities(): return [_ser(c) for c in list_capabilities()]

@router.get('/config')
def capabilities_config():
    s=get_settings()
    return {'default_mode':s.openadzero_default_mode,'lab_mode_enabled':s.openadzero_enable_lab_mode,'advanced_actions_enabled':s.openadzero_enable_advanced_actions,'ai_planner_enabled':s.openadzero_enable_ai_planner,'reporting_enabled':s.openadzero_enable_reporting,'manual_action_cards_enabled':s.openadzero_enable_manual_action_cards}

@router.get('/{capability_id}')
def capability(capability_id:str):
    c=get_capability(capability_id)
    if not c: raise HTTPException(404,'Capability not found')
    return _ser(c)
