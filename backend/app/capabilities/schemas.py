from typing import Literal

from pydantic import BaseModel, Field

CapabilityStatus = Literal['implemented', 'partial', 'planned', 'manual_only', 'lab_only', 'disabled', 'out_of_scope']
CapabilityMode = Literal['safe', 'assisted', 'ctf_lab', 'none']
CapabilityExecution = Literal['backend', 'manual', 'manual_card', 'external_import', 'none']


class Capability(BaseModel):
    id: str
    name: str
    category: str
    status: CapabilityStatus
    mode: CapabilityMode
    risk_level: int = Field(ge=1, le=5)
    requires_approval: bool
    execution: CapabilityExecution
    description: str
    evidence: bool


class CapabilityConfig(BaseModel):
    default_mode: str
    assisted_mode_enabled: bool
    ctf_lab_mode_enabled: bool
    manual_action_cards_enabled: bool
    external_evidence_import_enabled: bool
    reporting_enabled: bool
    ai_planner_enabled: bool
    advanced_automation_enabled: bool
