import { request } from './client';

export const adminApi = {
  getAdminStats: () => request<any>('/admin/stats'),
  getAdminPermissions: () => request<{ permissions: string[] }>('/admin/permissions'),
  getAdminReports: () => request<any>('/admin/reports/overview'),
  getAdminMembers: (params?: { status?: string; q?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.q) query.set('q', params.q);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    return request<any[]>(`/admin/members?${query.toString()}`);
  },
  reviewMember: (memberId: number, action: 'APPROVE' | 'REJECT' | 'REVIEW' | 'SUSPEND' | 'REACTIVATE') =>
    request<any>(`/admin/members/${memberId}/review?action=${action}`, { method: 'POST' }),
  previewMemberImport: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<{ total_rows: number; valid_count: number; error_count: number; rows: any[] }>(
      '/admin/imports/members/preview',
      { method: 'POST', body: formData }
    );
  },
  commitMemberImport: (rows: any[]) =>
    request<{ ok: boolean; imported_count: number; skipped_count: number; message: string }>(
      '/admin/imports/members/commit',
      { method: 'POST', body: JSON.stringify({ rows }) }
    ),
  broadcastNotification: (data: { channel: string; role?: string; title_bn: string; body_bn: string; notification_type?: string }) =>
    request<any>('/admin/notifications/broadcast', { method: 'POST', body: JSON.stringify(data) }),
  getAuditLogs: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    return request<any[]>(`/admin/audit?${query.toString()}`);
  },
  getUsers: () => request<any[]>('/admin/users'),
  createUser: (data: any) => request<any>('/admin/users', { method: 'POST', body: JSON.stringify(data) }),
  updateUser: (userId: number, data: any) =>
    request<any>(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) }),
};
