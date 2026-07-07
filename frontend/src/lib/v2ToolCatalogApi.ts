import {API_URL, ApiError} from './api';
import {mergeAuthHeaders} from './auth';

export type ToolFamily={id:string;name:string;description:string;phase_id:string;default_risk_level:string;supported_tools:string[];default_execution_mode:string;safety_notes:string[]};
export type ToolTemplate={template_id:string;tool_id:string;family:string;name:string;description:string;risk_level:string;execution_mode:string;supported_for_run:boolean;integration_status:string;blocked_reason?:string|null};
export type ToolReadiness={tool_id:string;binary?:string|null;available:boolean;version?:string|null;integration_status:string;supported_templates:string[];blocked_templates:string[];missing_reason?:string|null;risk_summary:Record<string,number>};
export type ToolCatalog={families:ToolFamily[];tools:unknown[];templates:ToolTemplate[]};

async function request<T>(path:string):Promise<T>{
  const response=await fetch(`${API_URL}${path}`,{headers:mergeAuthHeaders({'Content-Type':'application/json'})});
  if(!response.ok){let details:unknown=null;try{details=await response.json()}catch{details=await response.text()}throw new ApiError(`Tool catalog request failed: ${response.status}`,response.status,details)}
  return response.json() as Promise<T>;
}
export const getToolCatalog=()=>request<ToolCatalog>('/api/v2/tool-catalog');
export const getToolReadiness=()=>request<ToolReadiness[]>('/api/v2/tool-catalog/readiness');
