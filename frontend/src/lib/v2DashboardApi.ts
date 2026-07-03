import {API_URL, ApiError} from './api';

export type V2ScanCounters = {
  total: number;
  active: number;
  queued: number;
  running: number;
  completed: number;
  failed: number;
  stopped: number;
  deleted: number;
};

export type V2ParsedCounters = {
  assets: number;
  services: number;
  findings: number;
  signals: number;
  diagnostics: number;
};

export type V2SignalCounters = {
  smb_open: number;
  ldap_open: number;
  kerberos_open: number;
  http_open: number;
  rdp_open: number;
  winrm_open: number;
  mssql_open: number;
  ssh_open: number;
};

export type V2AdSurfaceCounters = {
  domain_controller_hints: number;
  smb_hosts: number;
  ldap_hosts: number;
  kerberos_hosts: number;
  winrm_hosts: number;
  rdp_hosts: number;
};

export type V2TopPort = {port: number; protocol: string; count: number};
export type V2TopService = {service_name: string; count: number};

export type V2RecentScan = {
  id: string;
  name: string;
  status: string;
  scan_type: string;
  tool_name?: string | null;
  progress_percent: number;
  created_at: string;
  updated_at: string;
};

export type V2RecentDiagnostic = {
  id: string;
  scan_id: string;
  level: string;
  message: string;
  source_type: string;
  created_at: string;
};

export type V2DashboardSummary = {
  scans: V2ScanCounters;
  parsed: V2ParsedCounters;
  signals: V2SignalCounters;
  services: {
    top_ports: V2TopPort[];
    top_service_names: V2TopService[];
  };
  assets: {
    windows_hosts: number;
    linux_hosts: number;
    unknown_hosts: number;
  };
  ad_surface: V2AdSurfaceCounters;
  recent_scans: V2RecentScan[];
  recent_diagnostics: V2RecentDiagnostic[];
};

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {headers: {'Content-Type': 'application/json'}});

  if (!response.ok) {
    let details: unknown = null;
    try {
      details = await response.json();
    } catch {
      details = await response.text();
    }
    throw new ApiError(`V2 dashboard request failed: ${response.status}`, response.status, details);
  }

  return response.json() as Promise<T>;
}

export const getV2DashboardSummary = (options?: {
  includeDeleted?: boolean;
  scanId?: string;
  limitRecent?: number;
}): Promise<V2DashboardSummary> => {
  const params = new URLSearchParams();
  if (options?.includeDeleted) params.set('include_deleted', 'true');
  if (options?.scanId) params.set('scan_id', options.scanId);
  if (options?.limitRecent !== undefined) params.set('limit_recent', String(options.limitRecent));
  const query = params.toString();
  return request<V2DashboardSummary>(`/api/v2/dashboard/summary${query ? `?${query}` : ''}`);
};
