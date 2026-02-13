const BASE_URL = import.meta.env.VITE_API_URL ?? "/api/v1";

interface ApiError {
  status: number;
  message: string;
}

type TokenProvider = () => Promise<string>;

let _getAccessToken: TokenProvider | null = null;

/**
 * Set the token provider used by apiFetch to add Authorization headers.
 * Called once from AuthSync after WorkOS initializes.
 */
export function setTokenProvider(provider: TokenProvider): void {
  _getAccessToken = provider;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};

  if (_getAccessToken) {
    try {
      const token = await _getAccessToken();
      if (token) headers["Authorization"] = `Bearer ${token}`;
    } catch {
      // Not authenticated -- continue without token
    }
  }

  const byokKey = localStorage.getItem("ehrlich_api_key");
  if (byokKey) {
    headers["X-Anthropic-Key"] = byokKey;
  }

  return headers;
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const authHeaders = await getAuthHeaders();

  const response = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error: ApiError = {
      status: response.status,
      message: await response.text(),
    };
    throw error;
  }

  return response.json() as Promise<T>;
}

/**
 * Build an SSE stream URL with auth token as query parameter.
 * EventSource does not support custom headers, so we pass the token as ?token=xxx.
 */
export async function buildSSEUrl(path: string): Promise<string> {
  const base = `${BASE_URL}${path}`;

  if (!_getAccessToken) return base;

  try {
    const token = await _getAccessToken();
    if (token) {
      const separator = base.includes("?") ? "&" : "?";
      return `${base}${separator}token=${encodeURIComponent(token)}`;
    }
  } catch {
    // Not authenticated
  }

  return base;
}
