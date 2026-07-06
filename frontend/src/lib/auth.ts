const STORAGE_KEY = 'openadzero.localApiToken';

export function getApiToken(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

export function setApiToken(token: string): void {
  const trimmed = token.trim();
  if (!trimmed) {
    clearApiToken();
    return;
  }
  localStorage.setItem(STORAGE_KEY, trimmed);
}

export function clearApiToken(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function authHeaders(): Record<string, string> {
  const token = getApiToken();
  return token ? {Authorization: `Bearer ${token}`} : {};
}

export function mergeAuthHeaders(headers?: HeadersInit): Headers {
  const merged = new Headers(headers);
  const token = getApiToken();
  if (token) merged.set('Authorization', `Bearer ${token}`);
  return merged;
}

export function withAuthUrl(url: string): string {
  const token = getApiToken();
  if (!token) return url;
  const parsed = new URL(url, window.location.href);
  parsed.searchParams.set('token', token);
  return parsed.toString();
}
