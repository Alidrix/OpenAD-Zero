export const API=(import.meta.env.VITE_API_URL as string)||'';
export type Service={id?:string;port:number;protocol:string;name:string;product:string;version:string;state:string};
export type Host={id:string;ip:string;hostname?:string;status:string;is_domain_controller_candidate:boolean;services:Service[]};
export type Mission={id:string;name:string;status:string;validated_targets:string[];jobs:any[];hosts:Host[];findings:any[];next_actions:any[]};
async function req<T>(url:string,init?:RequestInit):Promise<T>{const r=await fetch(API+url,{headers:{'Content-Type':'application/json'},...init}); if(!r.ok) throw new Error(await r.text()); return r.json();}
export const createMission=(p:{name:string;scope:string;mode:string;scenario:string})=>req<{mission_id:string;status:string;validated_targets:string[]}>('/api/missions',{method:'POST',body:JSON.stringify(p)});
export const startMission=(id:string)=>req<{mission_id:string;status:string;job_id:string}>(`/api/missions/${id}/start`,{method:'POST',body:JSON.stringify({mission_id:id,action:'start_scenario'})});
export const getMission=(id:string)=>req<Mission>(`/api/missions/${id}`);
export const health=()=>req<{status:string}>('/api/health');
