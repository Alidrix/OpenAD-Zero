export type IntegrationStatus='safe_auto'|'assisted_safe'|'executable_after_human_approval'|'manual_only'|'blocked_auto'|'planned';
export interface ToolAutomationTool{ id:string; name:string; integration_status:IntegrationStatus; risk_level?:string; requires_human_approval?:boolean; requires_terms_acceptance?:boolean; templates:string[]; notes?:string }
export interface CommandTemplate{ id:string; argv:string[]; placeholders:string[] }
export interface ToolActionPayload{ tool_id:string; template_id?:string; params:Record<string,string>; target?:string; human_approved:boolean; terms_accepted:boolean; preview_generated:boolean }
export interface ToolRunRecord{ run_id:string; tool_id:string; template_id?:string; status:string; command_preview:string; stdout:string[]; stderr:string[]; artifacts:string[] }
