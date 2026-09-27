import { request } from './client';

export const authApi = {
  login: (data: { email: string; password: string; mfa_code?: string }) =>
    request<{ ok: boolean; role?: string; mfa_required?: boolean; message?: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  register: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  getMe: () => request<any>('/auth/me'),
  changePassword: (data: { old_password: string; new_password: string }) =>
    request<{ ok: boolean; message: string }>('/auth/password/change', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  requestPasswordReset: (email: string) =>
    request<{ ok: boolean; message: string }>('/auth/password-reset/request', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  confirmPasswordReset: (data: { token: string; password: string }) =>
    request<{ ok: boolean }>('/auth/password-reset/confirm', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getSessions: () => request<any[]>('/auth/sessions'),
  revokeSession: (id: number) => request<any>(`/auth/sessions/${id}/revoke`, { method: 'POST' }),
  logoutAll: () => request<any>('/auth/logout-all', { method: 'POST' }),
};
