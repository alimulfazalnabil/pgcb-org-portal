/**
 * Core HTTP Client for PGCB Institutional Portal.
 * Enforces unified /backend reverse-proxying in browser to protect credentials and sessions.
 */

function resolveServerApiUrl(): string {
  const internalUrl = (process.env.INTERNAL_API_URL || '').trim();
  const publicUrl = (process.env.NEXT_PUBLIC_API_URL || '').trim();
  const candidate =
    internalUrl ||
    (publicUrl && !publicUrl.startsWith('/') ? publicUrl : '') ||
    'http://127.0.0.1:8000';

  let normalized = candidate.replace(/\/+$/, '').replace(/\/api\/v1$/, '');
  if (!/^https?:\/\//i.test(normalized)) {
    if (normalized.includes(':') || normalized.startsWith('127.0.0.1') || normalized.startsWith('localhost')) {
      normalized = `http://${normalized}`;
    } else if (normalized.includes('.')) {
      normalized = `https://${normalized}`;
    } else {
      normalized = `http://${normalized}:10000`;
    }
  }
  return normalized;
}

export const API_BASE_URL =
  typeof window !== 'undefined' ? '/backend' : resolveServerApiUrl();

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Guarantees HttpOnly auth cookies are sent
  };

  try {
    const res = await fetch(url, config);

    if (res.status === 204) {
      return {} as T;
    }

    const contentType = res.headers.get('content-type') || '';
    let responseData: any;
    if (contentType.includes('application/json')) {
      responseData = await res.json();
    } else {
      responseData = await res.text();
    }

    if (!res.ok) {
      const errorMessage =
        (responseData && typeof responseData === 'object' && (responseData.detail || responseData.message)) ||
        `Request failed with status ${res.status}`;
      throw new ApiError(res.status, errorMessage, responseData);
    }

    return responseData as T;
  } catch (error: any) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, error.message || 'নেটওয়ার্ক সংযোগে সমস্যা হয়েছে (Network Error)');
  }
}
