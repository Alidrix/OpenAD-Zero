export type CapabilityStatus = 'implemented' | 'partial' | 'planned' | 'manual_only' | 'lab_only' | 'disabled' | 'out_of_scope'
export type CapabilityMode = 'safe' | 'assisted' | 'ctf_lab' | 'none'
export type CapabilityExecution = 'backend' | 'manual' | 'manual_card' | 'external_import' | 'none'
export interface Capability { id:string; name:string; category:string; status:CapabilityStatus; mode:CapabilityMode; risk_level:number; requires_approval:boolean; execution:CapabilityExecution; description:string; evidence:boolean; executable?:boolean; visible?:boolean; disabled_reason?:string|null }
export interface CapabilityConfig { default_mode:string; assisted_mode_enabled:boolean; ctf_lab_mode_enabled:boolean; manual_action_cards_enabled:boolean; external_evidence_import_enabled:boolean; reporting_enabled:boolean; ai_planner_enabled:boolean; advanced_automation_enabled:boolean }
