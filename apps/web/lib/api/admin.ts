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
  reviewMember: (
    memberId: number,
    action: 'APPROVE' | 'REJECT' | 'REVIEW' | 'DOCUMENTS_REQUIRED' | 'PAYMENT_PENDING' | 'SUSPEND' | 'REACTIVATE',
    note?: string
  ) =>
    request<any>(
      `/admin/members/${memberId}/review?action=${action}${note ? `&note=${encodeURIComponent(note)}` : ''}`,
      { method: 'POST' }
    ),
  getMemberDetail: (memberId: number) => request<any>(`/admin/members/${memberId}`),
  getCircleDashboard: (circleId?: number) =>
    request<any>(`/admin/circle-dashboard${circleId ? `?circle_id=${circleId}` : ''}`),
  getMisReport: () => request<any>('/admin/reports/mis'),
  getFinancialReport: () => request<any>('/admin/reports/financial'),
  getCmsAnalytics: () => request<any>('/admin/analytics/cms'),
  getAdminNews: (params?: { category?: string; q?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.q) query.set('q', params.q);
    if (params?.status) query.set('status', params.status);
    return request<any[]>(`/admin/news?${query.toString()}`);
  },
  adminListNews: (params?: { category?: string; q?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.q) query.set('q', params.q);
    if (params?.status) query.set('status', params.status);
    return request<any[]>(`/admin/news?${query.toString()}`);
  },
  createAdminNews: (data: any) =>
    request<any>('/admin/news', { method: 'POST', body: JSON.stringify(data) }),
  adminCreateNews: (data: any) =>
    request<any>('/admin/news', { method: 'POST', body: JSON.stringify(data) }),
  updateAdminNews: (newsId: number, data: any) =>
    request<any>(`/admin/news/${newsId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteAdminNews: (newsId: number) =>
    request<any>(`/admin/news/${newsId}`, { method: 'DELETE' }),
  adminDeleteNews: (newsId: number) =>
    request<any>(`/admin/news/${newsId}`, { method: 'DELETE' }),
  adminTransitionWorkflow: (entityType: string, entityId: number, status: string, note?: string) =>
    request<any>(`/admin/workflow/${encodeURIComponent(entityType)}/${entityId}`, {
      method: 'POST',
      body: JSON.stringify({ status, note }),
    }),
  getContentRevisions: (entityType: string, entityId: number) =>
    request<any[]>(`/admin/revisions/${encodeURIComponent(entityType)}/${entityId}`),
  getAdminAnnouncements: () => request<any[]>('/admin/announcements'),
  createAdminAnnouncement: (data: any) =>
    request<any>('/admin/announcements', { method: 'POST', body: JSON.stringify(data) }),
  uploadOptimizedMedia: (file: File, options?: { title_bn?: string; alt_text?: string; folder?: string }) => {
    const formData = new FormData();
    formData.append('file', file);
    if (options?.title_bn) formData.append('title_bn', options.title_bn);
    if (options?.alt_text) formData.append('alt_text', options.alt_text);
    if (options?.folder) formData.append('folder', options.folder);
    return request<any>('/admin/media/upload-optimized', { method: 'POST', body: formData });
  },
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
  getKnowledgeDocuments: (params?: { category?: string; include_historical?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.include_historical !== undefined) query.set('include_historical', String(params.include_historical));
    return request<any[]>(`/admin/knowledge/documents?${query.toString()}`);
  },
  createKnowledgeDocument: (data: any) =>
    request<any>('/admin/knowledge/documents', { method: 'POST', body: JSON.stringify(data) }),
  supersedeKnowledgeDocument: (oldDocId: number, newDocumentId: number) =>
    request<any>(`/admin/knowledge/documents/${oldDocId}/supersede`, {
      method: 'POST',
      body: JSON.stringify({ new_document_id: newDocumentId }),
    }),
  generateSmartFaqs: (documentId: number, maxFaqs = 5) =>
    request<any>('/admin/ai/generate-faqs', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId, max_faqs: maxFaqs }),
    }),
  getAdminFaqs: (status?: string) =>
    request<any[]>(`/admin/ai/faqs${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  updateAdminFaq: (faqId: number, data: any) =>
    request<any>(`/admin/ai/faqs/${faqId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  aiContentAssist: (data: any) =>
    request<any>('/admin/ai/content-assist', { method: 'POST', body: JSON.stringify(data) }),
  getAiUsageAnalytics: () => request<any>('/admin/ai/analytics'),
  getAdminIntelligence: () => request<any>('/admin/analytics/intelligence'),
};
