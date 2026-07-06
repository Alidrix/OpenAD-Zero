import {API_URL, ApiError} from './api';
import {mergeAuthHeaders} from './auth';

export type ParsedAsset = {
  id: string;
  scan_id: string;
  source_type: string;
  source_id?: string | null;
  ip_address: string;
  hostname?: string | null;
  fqdn?: string | null;
  mac_address?: string | null;
  os_family?: string | null;
  os_name?: string | null;
  confidence: number;
  tags_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ParsedService = {
  id: string;
  scan_id: string;
  asset_id?: string | null;
  source_type: string;
  source_id?: string | null;
  ip_address: string;
  port: number;
  protocol: string;
  service_name?: string | null;
  product?: string | null;
  version?: string | null;
  state: string;
  confidence: number;
  tags_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ParsedFinding = {
  id: string;
  scan_id: string;
  asset_id?: string | null;
  service_id?: string | null;
  source_type: string;
  source_id?: string | null;
  title: string;
  description: string;
  severity: string;
  confidence: number;
  tags_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ParsedSignal = {
  id: string;
  scan_id: string;
  asset_id?: string | null;
  service_id?: string | null;
  finding_id?: string | null;
  source_type: string;
  source_id?: string | null;
  signal: string;
  value: string;
  confidence: number;
  created_at: string;
};

export type ParseDiagnostic = {
  id: string;
  scan_id: string;
  source_type: string;
  source_id?: string | null;
  level: string;
  message: string;
  details_json?: Record<string, unknown> | null;
  created_at: string;
};

export type ParsePersistedResult = {
  scan_id: string;
  assets_created: number;
  services_created: number;
  findings_created: number;
  signals_created: number;
  diagnostics_created: number;
  status: string;
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
    throw new ApiError(`V2 parsing request failed: ${response.status}`, response.status, details);
  }

  return response.json() as Promise<T>;
}

const scanPath = (scanId: string, suffix: string) =>
  `/api/v2/scans/${encodeURIComponent(scanId)}${suffix}`;

export const parsePersistedScan = (scanId: string): Promise<ParsePersistedResult> =>
  request<ParsePersistedResult>(scanPath(scanId, '/parse-persisted'), {
    method: 'POST',
    body: JSON.stringify({}),
  });

export const listParsedAssets = (scanId: string): Promise<ParsedAsset[]> =>
  request<ParsedAsset[]>(scanPath(scanId, '/parsed/assets'));

export const listParsedServices = (scanId: string): Promise<ParsedService[]> =>
  request<ParsedService[]>(scanPath(scanId, '/parsed/services'));

export const listParsedFindings = (scanId: string): Promise<ParsedFinding[]> =>
  request<ParsedFinding[]>(scanPath(scanId, '/parsed/findings'));

export const listParsedSignals = (scanId: string): Promise<ParsedSignal[]> =>
  request<ParsedSignal[]>(scanPath(scanId, '/parsed/signals'));

export const listParseDiagnostics = (scanId: string): Promise<ParseDiagnostic[]> =>
  request<ParseDiagnostic[]>(scanPath(scanId, '/parsed/diagnostics'));
