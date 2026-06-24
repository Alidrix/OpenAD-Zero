from app.capabilities.catalog import Capability, creates_manual_card_only, is_executable
from app.core.config import get_settings

def should_propose_capability(c: Capability, lab_mode_enabled: bool | None = None) -> bool:
    if c.status in {'disabled','out_of_scope'}: return False
    if lab_mode_enabled is None: lab_mode_enabled=get_settings().openadzero_enable_lab_mode
    if c.mode=='lab' and not lab_mode_enabled and c.status=='lab_only': return False
    return True

def planner_action_kind(c: Capability) -> str:
    if c.status in {'disabled','out_of_scope'}: return 'hidden'
    if creates_manual_card_only(c): return 'manual_card'
    if is_executable(c): return 'executable'
    return 'informational'
