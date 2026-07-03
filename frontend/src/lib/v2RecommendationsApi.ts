import {API_URL, ApiError} from './api';

export type V2SafeTemplate = {
  id: string;
  tool_id: string;
  name: string;
  description: string;
  category: string;
  risk_level: string;
  mode: string;
  requires_human_approval: boolean;
  requires_terms_acceptance: boolean;
  template_ref: string;
  expected_inputs: string[];
  expected_outputs: string[];
  recommendation_signals: string[];
  safety_notes: string[];
};

export type V2Recommendation = {
  recommendation_id: string;
  template_id: string;
  name: string;
  reason: string;
  priority: string;
  risk_level: string;
  mode: string;
  requires_human_approval: boolean;
  safety_notes: string[];
};

export type V2CommandPreview = {
  template_id: string;
  tool_id: string;
  name: string;
  argv_preview: string[];
  required_params: string[];
  missing_params: string[];
  safety_notes: string[];
  risk_level: string;
  mode: string;
  executable: boolean;
  automatic_execution_allowed: boolean;
};

export type V2RecommendationCatalog = {
  templates: V2SafeTemplate[];
  rules: unknown[];
  safety_policy: Record<string, unknown>;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {headers: {'Content-Type': 'application/json'}, ...options});
  if (!response.ok) {
    let details: unknown = null;
    try { details = await response.json(); } catch { details = await response.text(); }
    throw new ApiError(`V2 recommendations request failed: ${response.status}`, response.status, details);
  }
  return response.json() as Promise<T>;
}

export const getRecommendationCatalog = () => request<V2RecommendationCatalog>('/api/v2/recommendations/catalog');
export const getScanRecommendations = (scanId: string) => request<V2Recommendation[]>(`/api/v2/scans/${encodeURIComponent(scanId)}/recommendations`);
export const buildCommandPreview = (templateId: string, params: Record<string, string>) =>
  request<V2CommandPreview>('/api/v2/recommendations/preview', {method: 'POST', body: JSON.stringify({template_id: templateId, params})});
