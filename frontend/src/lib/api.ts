import type {Capability, CapabilityConfig} from '../types/capabilities';
export const API_URL=(import.meta.env.VITE_API_URL as string)||'';
export const API=API_URL;

export class ApiError extends Error {
  status: number
  details?: unknown

  constructor(message: string, status: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

export type Service={id?:string;port:number;protocol:string;name:string;product:string;version:string;state:string};
export type SMBFact={hostname?:string;domain?:string;os?:string;smb_signing_required?:boolean;smbv1_enabled?:boolean;null_session_possible?:boolean;source?:string};
export type SMBShare={name:string;access?:string;remark?:string;anonymous:boolean;source?:string};
export type Host={id:string;ip:string;hostname?:string;status:string;is_domain_controller_candidate:boolean;services:Service[];smb_facts?:SMBFact[];smb_shares?:SMBShare[]};
export type Mission={id:string;name:string;status:string;validated_targets:string[];jobs:any[];hosts:Host[];findings:any[];next_actions:any[];web_targets?:any[]};
async function request<T>(path:string,options?:RequestInit):Promise<T>{
  const response=await fetch(`${API_URL}${path}`,{headers:{'Content-Type':'application/json'},...options});
  if(!response.ok){
    let details:unknown=null;
    try{details=await response.json()}catch{details=await response.text()}
    throw new ApiError(`API request failed: ${response.status}`, response.status, details);
  }
  if(response.status===204)return undefined as T;
  return response.json() as Promise<T>;
}
const req=request;
export const createMission=(p:{name:string;scope:string;mode:string;scenario:string})=>req<{mission_id:string;status:string;validated_targets:string[]}>('/api/missions',{method:'POST',body:JSON.stringify(p)});
export const startMission=(id:string)=>req<{mission_id:string;status:string;job_id:string}>(`/api/missions/${id}/start`,{method:'POST',body:JSON.stringify({mission_id:id,action:'start_scenario'})});
export const getMission=(id:string)=>req<Mission>(`/api/missions/${id}`);
export const approveAction=(missionId:string,actionId:string,note:string)=>req<{mission_id:string;action_id:string;status:string;job_id:string}>(`/api/missions/${missionId}/actions/${actionId}/approve`,{method:'POST',body:JSON.stringify({approved:true,note})});
export const ignoreAction=(missionId:string,actionId:string,reason:string)=>req<{status:string}>(`/api/missions/${missionId}/actions/${actionId}/ignore`,{method:'POST',body:JSON.stringify({reason})});
export const health=()=>req<{status:string;service?:string}>('/api/health');
export const dbHealth=()=>req<any>('/api/health/db');
export const redisHealth=()=>req<any>('/api/health/redis');
export const toolHealth=()=>req<any>('/api/health/tools');
export interface VersionInfo {
  name: string
  version: string
  release_stage: string
}

export async function getVersion(): Promise<VersionInfo> {
  return request<VersionInfo>('/api/version')
}


export const getWebTargets=(id:string)=>req<any[]>(`/api/missions/${id}/web-targets`);

export const getBloodHoundCommand=(id:string)=>req<any>(`/api/missions/${id}/bloodhound/sharphound-command`);
export const getBloodHoundStatus=(id:string)=>req<any>(`/api/missions/${id}/bloodhound/status`);
export const getBloodHoundCollections=(id:string)=>req<any[]>(`/api/missions/${id}/bloodhound/collections`);
export async function uploadBloodHoundZip(id:string,file:File){const fd=new FormData();fd.append('file',file);const r=await fetch(API_URL+`/api/missions/${id}/bloodhound/upload`,{method:'POST',body:fd});if(!r.ok)throw new Error(await r.text());return r.json()}
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
import type {Evidence,EvidenceLink,EvidencePreview} from '../types/evidence';
export const listEvidence=(missionId:string,filters?:{category?:string;q?:string;source?:string})=>{const qs=new URLSearchParams();Object.entries(filters||{}).forEach(([k,v])=>{if(v)qs.set(k,v)});return req<Evidence[]>(`/api/missions/${missionId}/evidence${qs.toString()?`?${qs}`:''}`)};
export const getEvidence=(missionId:string,evidenceId:string)=>req<Evidence>(`/api/missions/${missionId}/evidence/${evidenceId}`);
export const getEvidencePreview=(missionId:string,evidenceId:string)=>req<EvidencePreview>(`/api/missions/${missionId}/evidence/${evidenceId}/preview`);
export async function importEvidence(missionId:string,formData:FormData){const r=await fetch(API_URL+`/api/missions/${missionId}/evidence/import`,{method:'POST',body:formData});if(!r.ok)throw new Error(await r.text());return r.json() as Promise<Evidence>}
export const deleteEvidence=(missionId:string,evidenceId:string)=>req<{deleted:boolean}>(`/api/missions/${missionId}/evidence/${evidenceId}`,{method:'DELETE'});
export const createEvidenceLink=(missionId:string,evidenceId:string,payload:{target_type:string;target_id:string})=>req<EvidenceLink>(`/api/missions/${missionId}/evidence/${evidenceId}/links`,{method:'POST',body:JSON.stringify(payload)});
export const listEvidenceLinks=(missionId:string,evidenceId:string)=>req<EvidenceLink[]>(`/api/missions/${missionId}/evidence/${evidenceId}/links`);
export const deleteEvidenceLink=(missionId:string,evidenceId:string,linkId:string)=>req<{deleted:boolean}>(`/api/missions/${missionId}/evidence/${evidenceId}/links/${linkId}`,{method:'DELETE'});
import type {Report,ReportPreview} from '../types/report';
export const generateReport=(missionId:string,payload?:{include_sections?:string[]|null})=>req<Report>(`/api/missions/${missionId}/report/generate`,{method:'POST',body:JSON.stringify(payload||{include_sections:null})});
export const getLatestReport=(missionId:string)=>req<{report:Report|null}>(`/api/missions/${missionId}/report`);
export const getReportPreview=(missionId:string,format:'markdown'|'html')=>req<ReportPreview>(`/api/missions/${missionId}/report/preview?format=${format}`);
export const getReportDownloadUrl=(missionId:string,format:'markdown'|'html')=>`${API}/api/missions/${missionId}/report/download?format=${format}`;
import type {MissionObjective,MissionPhase,TimelineEvent,ProgressScore,OperationsSummary} from '../types/operations';
export const getMissionObjective=(missionId:string)=>req<MissionObjective>(`/api/missions/${missionId}/objective`);
export const updateMissionObjective=(missionId:string,payload:Partial<MissionObjective>)=>req<MissionObjective>(`/api/missions/${missionId}/objective`,{method:'PATCH',body:JSON.stringify(payload)});
export const getMissionPhases=(missionId:string)=>req<MissionPhase[]>(`/api/missions/${missionId}/phases`);
export const updateMissionPhase=(missionId:string,phaseId:string,payload:{status?:string;summary?:string})=>req<MissionPhase>(`/api/missions/${missionId}/phases/${phaseId}`,{method:'PATCH',body:JSON.stringify(payload)});
export const getMissionTimeline=(missionId:string,filters?:{source?:string;severity?:string;limit?:number})=>{const qs=new URLSearchParams();Object.entries(filters||{}).forEach(([k,v])=>{if(v)qs.set(k,String(v))});return req<TimelineEvent[]>(`/api/missions/${missionId}/timeline${qs.toString()?`?${qs}`:''}`)};
export const createTimelineEvent=(missionId:string,payload:Partial<TimelineEvent>)=>req<TimelineEvent>(`/api/missions/${missionId}/timeline`,{method:'POST',body:JSON.stringify(payload)});
export const getMissionProgress=(missionId:string)=>req<ProgressScore>(`/api/missions/${missionId}/progress`);
export const getOperationsSummary=(missionId:string)=>req<OperationsSummary>(`/api/missions/${missionId}/operations/summary`);
export const syncOperations=(missionId:string)=>req<ProgressScore>(`/api/missions/${missionId}/operations/sync`,{method:'POST',body:JSON.stringify({})});
import type {Job,JobLog} from '../types/jobs';
import type {MissionEvent as PersistentMissionEvent} from '../types/events';
export const listMissionJobs=(missionId:string)=>req<Job[]>(`/api/missions/${missionId}/jobs`);
export const getMissionJob=(missionId:string,jobId:string)=>req<Job>(`/api/missions/${missionId}/jobs/${jobId}`);
export const getMissionJobLogs=(missionId:string,jobId:string)=>req<JobLog[]>(`/api/missions/${missionId}/jobs/${jobId}/logs`);
export const cancelJob=(missionId:string,jobId:string)=>req<Job>(`/api/missions/${missionId}/jobs/${jobId}/cancel`,{method:'POST',body:JSON.stringify({})});
export const retryJob=(missionId:string,jobId:string)=>req<Job>(`/api/missions/${missionId}/jobs/${jobId}/retry`,{method:'POST',body:JSON.stringify({})});
export const listMissionEvents=(missionId:string,filters?:{after_id?:string;limit?:number;event_type?:string;source?:string})=>{const qs=new URLSearchParams();Object.entries(filters||{}).forEach(([k,v])=>{if(v)qs.set(k,String(v))});return req<PersistentMissionEvent[]>(`/api/missions/${missionId}/events${qs.toString()?`?${qs}`:''}`)};
export const workerHealth=()=>req<any>('/api/health/worker');
