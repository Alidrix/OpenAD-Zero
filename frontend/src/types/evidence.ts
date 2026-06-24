export interface Evidence {id:string;mission_id:string;label:string;category:string;description?:string|null;filename:string;stored_path:string;sha256:string;size_bytes:number;mime_type?:string|null;source:string;preview_available:boolean;metadata_json?:Record<string,unknown>|null;created_at:string}
export interface EvidenceLink {id:string;mission_id:string;evidence_id:string;target_type:string;target_id:string;created_at:string}
export interface EvidencePreview {available:boolean;format:string;truncated:boolean;content:string}
