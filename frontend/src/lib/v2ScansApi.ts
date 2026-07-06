import {API_URL, ApiError} from './api';
import {mergeAuthHeaders} from './auth';

export type V2Scan = {
  id: string;
  mission_id?: string | null;
  name: string;
  scan_type: string;
  tool_name?: string | null;
  status: string;
  progress_percent: number;
  current_step?: string | null;
  rq_job_id?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  stopped_at?: string | null;
  deleted_at?: string | null;
  created_at: string;
  updated_at: string;
  renamed_at?: string | null;
  events?: V2ScanEvent[];
  artifacts?: V2ScanArtifact[];
};

export type V2ScanEvent = {
  id: string;
  scan_id: string;
  event_type: string;
  type?: string;
  message: string;
  payload_json?: Record<string, unknown> | null;
  payload?: Record<string, unknown>;
  status?: string | null;
  progress_percent?: number | null;
  current_step?: string | null;
  created_at: string;
};

export type V2ScanArtifact = {
  id: string;
  scan_id: string;
  artifact_type: string;
  path: string;
  sha256?: string | null;
  size_bytes?: number | null;
  created_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: mergeAuthHeaders({'Content-Type': 'application/json', ...(options?.headers as Record<string,string>|undefined)}),
    ...options,
  });

  if (!response.ok) {
    let details: unknown = null;

    try {
      details = await response.json();
    } catch {
      details = await response.text();
    }

    throw new ApiError(`V2 scans request failed: ${response.status}`, response.status, details);
  }

  return response.json() as Promise<T>;
}

export const listScans = (includeDeleted = false): Promise<V2Scan[]> =>
  request<V2Scan[]>(`/api/v2/scans${includeDeleted ? '?include_deleted=true' : ''}`);

export const getScan = (scanId: string): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}`);

export const renameScan = (scanId: string, name: string): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}/rename`, {
    method: 'PATCH',
    body: JSON.stringify({name}),
  });

export const enqueueDemoScan = (scanId: string): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}/enqueue-demo`, {
    method: 'POST',
    body: JSON.stringify({}),
  });

export const startInitialDiscovery = (scanId: string, profile: 'safe_default' = 'safe_default'): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}/start-initial-discovery`, {
    method: 'POST',
    body: JSON.stringify({profile}),
  });

export const stopScan = (scanId: string): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}/stop`, {
    method: 'POST',
    body: JSON.stringify({}),
  });

export const deleteScan = (scanId: string): Promise<V2Scan> =>
  request<V2Scan>(`/api/v2/scans/${encodeURIComponent(scanId)}`, {method: 'DELETE'});

export const listScanEvents = (scanId: string): Promise<V2ScanEvent[]> =>
  request<V2ScanEvent[]>(`/api/v2/scans/${encodeURIComponent(scanId)}/events`);

export const listScanArtifacts = (scanId: string): Promise<V2ScanArtifact[]> =>
  request<V2ScanArtifact[]>(`/api/v2/scans/${encodeURIComponent(scanId)}/artifacts`);
