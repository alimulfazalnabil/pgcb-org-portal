/**
 * Centralized Institutional API Client for PGCB Organization Portal.
 * Handles baseURL resolution, credentials, auth cookies, error normalization, and typed endpoints.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'https://pgcb-org-portal.onrender.com';

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

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}/api/v1${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Ensures HTTP-only auth cookies are sent
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

// ---------------- Public Endpoints ----------------

export interface PublicStats {
  active_members: number;
  active_circles: number;
  publications: number;
  upcoming_events: number;
  notices_count?: number;
  documents_count?: number;
}

export interface Notice {
  id: number;
  title_bn: string;
  title_en?: string;
  content_bn: string;
  content_en?: string;
  priority: 'NORMAL' | 'HIGH' | 'URGENT';
  category: string;
  attachment_url?: string;
  is_pinned: boolean;
  is_published: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: number;
  title_bn: string;
  title_en?: string;
  category: string;
  description_bn?: string;
  file_path: string;
  file_size?: number;
  content_type?: string;
  version: string;
  download_count: number;
  created_at: string;
}

export interface PublicMember {
  membership_id: string;
  name_bn: string;
  name_en?: string;
  designation_bn?: string;
  designation_en?: string;
  circle_name_bn?: string;
  circle_name_en?: string;
  status: string;
}

export interface CircleItem {
  id: number;
  name_bn: string;
  name_en: string;
  description_bn?: string;
}

export interface CommitteeItem {
  id: number;
  name_bn: string;
  name_en?: string;
  designation_bn: string;
  designation_en?: string;
  message_bn?: string;
  photo_url?: string;
  term_start?: number;
  term_end?: number;
}

export interface CircularItem {
  id: number;
  category: string;
  reference_no?: string;
  title_bn: string;
  title_en?: string;
  summary_bn?: string;
  document_url?: string;
  published_at?: string;
  priority: number;
}

export interface EventItem {
  id: number;
  title_bn: string;
  title_en?: string;
  description_bn?: string;
  event_date?: string;
  location_bn?: string;
  cover_image_url?: string;
  registration_enabled: boolean;
  capacity?: number;
  fee_amount: number;
  fee_currency: string;
}

export const api = {
  // Public
  getStats: () => request<PublicStats>('/public/stats'),
  getSettings: () => request<Record<string, string>>('/public/settings'),
  getMembers: (params?: { q?: string; circle_id?: number; page?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.q) query.set('q', params.q);
    if (params?.circle_id) query.set('circle_id', params.circle_id.toString());
    if (params?.page) query.set('page', params.page.toString());
    if (params?.limit) query.set('limit', params.limit.toString());
    return request<{ total: number; page: number; limit: number; items: PublicMember[] }>(
      `/public/members?${query.toString()}`
    );
  },
  getCircles: () => request<CircleItem[]>('/public/circles'),
  getCommittee: () => request<CommitteeItem[]>('/public/committee'),
  getCircleCommittee: (circleId: number) => request<CommitteeItem[]>(`/public/circles/${circleId}/committee`),
  getCirculars: (params?: { q?: string; category?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.q) query.set('q', params.q);
    if (params?.category) query.set('category', params.category);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    return request<CircularItem[]>(`/public/circulars?${query.toString()}`);
  },
  getCircular: (id: number) => request<CircularItem>(`/public/circulars/${id}`),
  getEvents: (upcoming = false) => request<EventItem[]>(`/public/events?upcoming=${upcoming}`),
  getJournals: (q?: string) => request<any[]>(`/public/journals${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  getMedia: (type?: string) => request<any[]>(`/public/media${type ? `?media_type=${type}` : ''}`),
  search: (q: string) => request<{ query: string; count: number; results: any[] }>(`/public/search?q=${encodeURIComponent(q)}`),
  submitContact: (data: { name: string; email: string; phone?: string; subject: string; message: string }) =>
    request<{ ok: boolean; message_id: number }>('/public/contact', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  verifyMember: (membershipId: string) => request<any>(`/public/verify/${encodeURIComponent(membershipId)}`),

  // Notices
  getNotices: (params?: { category?: string; priority?: string; page?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.priority) query.set('priority', params.priority);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.limit) query.set('limit', params.limit.toString());
    return request<Notice[]>(`/notices?${query.toString()}`);
  },
  getUrgentNotice: () => request<Notice | null>('/notices/urgent'),
  getNotice: (id: number) => request<Notice>(`/notices/${id}`),
  createNotice: (data: Partial<Notice>) =>
    request<Notice>('/notices', { method: 'POST', body: JSON.stringify(data) }),
  updateNotice: (id: number, data: Partial<Notice>) =>
    request<Notice>(`/notices/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteNotice: (id: number) => request<void>(`/notices/${id}`, { method: 'DELETE' }),

  // Documents
  getDocuments: (params?: { category?: string; page?: number; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set('category', params.category);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.limit) query.set('limit', params.limit.toString());
    return request<DocumentItem[]>(`/documents?${query.toString()}`);
  },
  getDocument: (id: number) => request<DocumentItem>(`/documents/${id}`),
  getDocumentDownloadUrl: (id: number) => `${API_BASE_URL}/api/v1/documents/${id}/download`,
  uploadDocumentFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<{ file_path: string; file_size: number; content_type: string; original_filename: string }>(
      '/documents/upload',
      { method: 'POST', body: formData }
    );
  },
  createDocument: (data: Partial<DocumentItem>) =>
    request<DocumentItem>('/documents', { method: 'POST', body: JSON.stringify(data) }),
  updateDocument: (id: number, data: Partial<DocumentItem>) =>
    request<DocumentItem>(`/documents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteDocument: (id: number) => request<void>(`/documents/${id}`, { method: 'DELETE' }),

  // Auth
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

  // Membership & Profile
  getProfile: () => request<any>('/member/profile'),
  updateProfile: (data: any) =>
    request<any>('/member/profile', { method: 'PATCH', body: JSON.stringify(data) }),
  getMemberApplication: () => request<any>('/member/application'),
  submitMemberApplication: () =>
    request<any>('/member/application', { method: 'POST' }),
  getMemberDocuments: () => request<any[]>('/member/documents'),
  uploadMemberDocument: (documentType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<any>(`/member/documents?document_type=${encodeURIComponent(documentType)}`, {
      method: 'POST',
      body: formData,
    });
  },
  getMemberNotifications: () => request<any[]>('/member/notifications'),
  markNotificationRead: (id: number) =>
    request<any>(`/member/notifications/${id}/read`, { method: 'POST' }),
  getMemberPayments: () => request<any[]>('/member/payments'),
  getMyEventRegistrations: () => request<any[]>('/events/registrations/me'),
  getDigitalCardUrl: () => `${API_BASE_URL}/api/v1/member/card`,
  getDigitalCardPdfUrl: () => `${API_BASE_URL}/api/v1/member/card/pdf`,

  // Public Membership application & track
  submitApplication: (data: any) =>
    request<{ ok: boolean; application_no: string; message: string }>('/public/membership/apply', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  trackApplication: (applicationNo: string) =>
    request<any>(`/public/membership/track/${encodeURIComponent(applicationNo)}`),

  // Sessions & Security
  getSessions: () => request<any[]>('/auth/sessions'),
  revokeSession: (id: number) => request<any>(`/auth/sessions/${id}/revoke`, { method: 'POST' }),
  logoutAll: () => request<any>('/auth/logout-all', { method: 'POST' }),

  // Admin
  getAdminStats: () => request<any>('/admin/stats'),
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
};
