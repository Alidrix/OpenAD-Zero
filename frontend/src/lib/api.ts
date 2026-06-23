export const API=(import.meta.env.VITE_API_URL as string)||'';
export type Service={id?:string;port:number;protocol:string;name:string;product:string;version:string;state:string};
export type Host={id:string;ip:string;hostname?:string;status:string;is_domain_controller_candidate:boolean;services:Service[]};
export type SMBFact={id?:string;host_id?:string;ip:string;hostname?:string;domain?:string;os?:string;smb_signing_required?:boolean|null;smbv1_enabled?:boolean|null;null_session_possible?:boolean|null;source?:string;raw_line?:string};
export type SMBShare={id?:string;host_id?:string;ip:string;name:string;access?:string;remark?:string;anonymous:boolean;source?:string};
export type NextAction={id:string;title:string;description?:string;reason?:string;risk_level:number;requires_approval:boolean;status:string;command_template_id?:string};
export type Mission={id:string;name:string;status:string;validated_targets:string[];jobs:any[];hosts:Host[];findings:any[];next_actions:NextAction[];smb_facts:SMBFact[];smb_shares:SMBShare[]};
async function req<T>(url:string,init?:RequestInit):Promise<T>{const r=await fetch(API+url,{headers:{'Content-Type':'application/json'},...init}); if(!r.ok) throw new Error(await r.text()); return r.json();}
export const createMission=(p:{name:string;scope:string;mode:string;scenario:string})=>req<{mission_id:string;status:string;validated_targets:string[]}>('/api/missions',{method:'POST',body:JSON.stringify(p)});
export const startMission=(id:string)=>req<{mission_id:string;status:string;job_id:string}>(`/api/missions/${id}/start`,{method:'POST',body:JSON.stringify({mission_id:id,action:'start_scenario'})});
export const getMission=(id:string)=>req<Mission>(`/api/missions/${id}`);
export const approveAction=(missionId:string, actionId:string, note:string)=>req<{mission_id:string;action_id:string;status:string;job_id:string}>(`/api/missions/${missionId}/actions/${actionId}/approve`,{method:'POST',body:JSON.stringify({approved:true,note})});
export const ignoreAction=(missionId:string, actionId:string, reason:string)=>req<{status:string}>(`/api/missions/${missionId}/actions/${actionId}/ignore`,{method:'POST',body:JSON.stringify({reason})});
export const health=()=>req<{status:string}>('/api/health');
export const toolHealth=()=>req<Record<string,{available:boolean;version:string}>>('/api/health/tools');
