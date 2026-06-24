import type {Capability, CapabilityConfig} from '../types/capabilities';
export const API=(import.meta.env.VITE_API_URL as string)||'';
export type Service={id?:string;port:number;protocol:string;name:string;product:string;version:string;state:string};
export type SMBFact={hostname?:string;domain?:string;os?:string;smb_signing_required?:boolean;smbv1_enabled?:boolean;null_session_possible?:boolean;source?:string};
export type SMBShare={name:string;access?:string;remark?:string;anonymous:boolean;source?:string};
export type Host={id:string;ip:string;hostname?:string;status:string;is_domain_controller_candidate:boolean;services:Service[];smb_facts?:SMBFact[];smb_shares?:SMBShare[]};
export type Mission={id:string;name:string;status:string;validated_targets:string[];jobs:any[];hosts:Host[];findings:any[];next_actions:any[];web_targets?:any[]};
async function req<T>(url:string,init?:RequestInit):Promise<T>{const r=await fetch(API+url,{headers:{'Content-Type':'application/json'},...init}); if(!r.ok) throw new Error(await r.text()); return r.json();}
export const createMission=(p:{name:string;scope:string;mode:string;scenario:string})=>req<{mission_id:string;status:string;validated_targets:string[]}>('/api/missions',{method:'POST',body:JSON.stringify(p)});
export const startMission=(id:string)=>req<{mission_id:string;status:string;job_id:string}>(`/api/missions/${id}/start`,{method:'POST',body:JSON.stringify({mission_id:id,action:'start_scenario'})});
export const getMission=(id:string)=>req<Mission>(`/api/missions/${id}`);
export const approveAction=(missionId:string,actionId:string,note:string)=>req<{mission_id:string;action_id:string;status:string;job_id:string}>(`/api/missions/${missionId}/actions/${actionId}/approve`,{method:'POST',body:JSON.stringify({approved:true,note})});
export const ignoreAction=(missionId:string,actionId:string,reason:string)=>req<{status:string}>(`/api/missions/${missionId}/actions/${actionId}/ignore`,{method:'POST',body:JSON.stringify({reason})});
export const health=()=>req<{status:string}>('/api/health');
export const toolHealth=()=>req<any>('/api/health/tools');

export const getWebTargets=(id:string)=>req<any[]>(`/api/missions/${id}/web-targets`);

export const getBloodHoundCommand=(id:string)=>req<any>(`/api/missions/${id}/bloodhound/sharphound-command`);
export const getBloodHoundStatus=(id:string)=>req<any>(`/api/missions/${id}/bloodhound/status`);
export const getBloodHoundCollections=(id:string)=>req<any[]>(`/api/missions/${id}/bloodhound/collections`);
export async function uploadBloodHoundZip(id:string,file:File){const fd=new FormData();fd.append('file',file);const r=await fetch(API+`/api/missions/${id}/bloodhound/upload`,{method:'POST',body:fd});if(!r.ok)throw new Error(await r.text());return r.json()}
export const getBloodHoundExplorerStatus=(id:string)=>req<any>(`/api/missions/${id}/bloodhound/explorer/status`);
export const searchBloodHoundObjects=(id:string,q:string,types:string,limit=20)=>req<any[]>(`/api/missions/${id}/bloodhound/objects/search?q=${encodeURIComponent(q)}&types=${encodeURIComponent(types)}&limit=${limit}`);
export const getBloodHoundObject=(id:string,oid:string)=>req<any>(`/api/missions/${id}/bloodhound/objects/${encodeURIComponent(oid)}`);
export const getBloodHoundRelations=(id:string,oid:string,direction:string,limit=100)=>req<any[]>(`/api/missions/${id}/bloodhound/objects/${encodeURIComponent(oid)}/relations?direction=${direction}&limit=${limit}`);
export const getBloodHoundPermissions=(id:string,oid:string,limit=100)=>req<any[]>(`/api/missions/${id}/bloodhound/objects/${encodeURIComponent(oid)}/permissions?limit=${limit}`);
export const runBloodHoundPathfinding=(id:string,p:any)=>req<any>(`/api/missions/${id}/bloodhound/pathfinding`,{method:'POST',body:JSON.stringify(p)});

export const getCapabilities=(filters?:{status?:string;category?:string;mode?:string;q?:string})=>{const qs=new URLSearchParams();Object.entries(filters||{}).forEach(([k,v])=>{if(v)qs.set(k,v)});return req<Capability[]>(`/api/capabilities${qs.toString()?`?${qs}`:''}`)};
export const getCapability=(id:string)=>req<Capability>(`/api/capabilities/${encodeURIComponent(id)}`);
export const getCapabilitiesConfig=()=>req<CapabilityConfig>('/api/capabilities/config');
export const getCapabilityConfig=getCapabilitiesConfig;
