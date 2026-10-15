import { request, API_BASE_URL } from './client';
import {
  PublicMember,
  CircleItem,
  CommitteeItem,
  MembershipSummary,
  MembershipHistoryItem,
  MembershipRenewalOptions,
  MembershipRenewalRequest,
  MembershipRenewalResult,
  ApplicationCenterDetails,
  PaymentSummary,
  MemberEventItem,
  MemberEventsResponse,
  MemberEventPass,
  MemberNotificationItem,
  MemberNotificationsResponse,
  NotificationSettingsResponse,
  AdminEventAttendanceResponse,
  AdminCheckInResult,
} from './types';

export const membersApi = {
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
  getCircleDetail: (circleSlugOrId: string | number) =>
    request<any>(`/public/circles/${encodeURIComponent(String(circleSlugOrId))}`),
  getCommittee: () => request<CommitteeItem[]>('/public/committee'),
  getCircleCommittee: (circleId: string | number) =>
    request<CommitteeItem[]>(`/public/circles/${encodeURIComponent(String(circleId))}/committee`),
  verifyMember: (membershipId: string) => request<any>(`/public/verify/${encodeURIComponent(membershipId)}`),
  getProfile: () => request<any>('/member/profile'),
  updateProfile: (data: any) =>
    request<any>('/member/profile', { method: 'PATCH', body: JSON.stringify(data) }),
  uploadProfilePhoto: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<any>('/member/profile/photo', {
      method: 'POST',
      body: formData,
    });
  },
  getProfileChangeRequests: () => request<{ items: any[]; change_requests: any[]; count: number }>('/member/profile/change-requests'),
  getProfileChangeRequest: (id: number) => request<any>(`/member/profile/change-requests/${id}`),
  createProfileChangeRequest: (data: {
    field_name: string;
    requested_value: string;
    reason?: string;
    supporting_doc_url?: string;
    supporting_document_id?: number;
  }) =>
    request<any>('/member/profile/change-requests', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  cancelProfileChangeRequest: (id: number) =>
    request<any>(`/member/profile/change-requests/${id}`, {
      method: 'DELETE',
    }),
  getApplicationTimeline: () => request<any>('/member/application/timeline'),
  saveApplicationDraft: () =>
    request<any>('/member/application/draft', { method: 'POST' }),
  submitApplication: () =>
    request<any>('/member/application', { method: 'POST' }),
  cancelApplication: () =>
    request<any>('/member/application/cancel', { method: 'POST' }),
  getMemberDocuments: () => request<any[]>('/member/documents'),
  uploadMemberDocument: (documentType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<any>(`/member/documents?document_type=${encodeURIComponent(documentType)}`, {
      method: 'POST',
      body: formData,
    });
  },
  getNotificationPreferences: () => request<any>('/member/notification-preferences'),
  updateNotificationPreferences: (prefs: Record<string, any>) =>
    request<any>('/member/notification-preferences', { method: 'PUT', body: JSON.stringify(prefs) }),
  getMemberDashboard: () => request<any>('/member/dashboard'),
  getRenewalOptions: () => request<MembershipRenewalOptions>('/member/membership/renewal/options'),
  getMemberRenewals: () => request<any>('/member/renewals'),
  getRenewals: async () => {
    const res = await request<any>('/member/renewals');
    return Array.isArray(res) ? res : res?.renewals || res?.items || [];
  },
  initiateRenewal: (
    planOrData: string | { period?: string; plan_code?: string; provider?: string; idempotency_key?: string },
    provider = 'SSLCOMMERZ'
  ) => {
    const body =
      typeof planOrData === 'string'
        ? { plan_code: planOrData, provider }
        : planOrData;
    return request<any>('/member/renewal/initiate', { method: 'POST', body: JSON.stringify(body) });
  },
  getMemberCertificates: () => request<any[]>('/member/certificates'),
  getDigitalCardDetails: () => request<any>('/member/card/details'),
  getMemberAnnouncements: () => request<any[]>('/member/announcements'),
  getMemberUpdates: () => request<{ items: any[]; count: number }>('/member/updates'),
  toggleBookmarkUpdate: (contentType: string, contentId: number) =>
    request<any>('/member/updates/bookmark', {
      method: 'POST',
      body: JSON.stringify({ content_type: contentType, content_id: contentId }),
    }),
  markUpdateRead: (contentType: string, contentId: number) =>
    request<any>('/member/updates/read', {
      method: 'POST',
      body: JSON.stringify({ content_type: contentType, content_id: contentId }),
    }),
  getMemberSettings: () => request<any>('/member/settings'),
  updateMemberSettings: (settingsData: Record<string, any>) =>
    request<any>('/member/settings', { method: 'PUT', body: JSON.stringify(settingsData) }),
  getMemberLoginHistory: () => request<any>('/member/login-history'),
  getMemberPayments: () => request<any[]>('/member/payments'),
  getMyEventRegistrations: () => request<any[]>('/events/registrations/me'),
  getDigitalCardUrl: () => `${API_BASE_URL}/api/v1/member/card`,
  getDigitalCardBackUrl: () => `${API_BASE_URL}/api/v1/member/card/back`,
  getDigitalCardPdfUrl: () => `${API_BASE_URL}/api/v1/member/card/pdf`,
  getCertificatePngUrl: (certificateNo: string) =>
    `${API_BASE_URL}/api/v1/certificates/${encodeURIComponent(certificateNo)}.png`,
  getCertificatePdfUrl: (certificateNo: string) =>
    `${API_BASE_URL}/api/v1/certificates/${encodeURIComponent(certificateNo)}.pdf`,
  getPaymentReceiptPdfUrl: (transactionId: number) =>
    `${API_BASE_URL}/api/v1/payments/transactions/${transactionId}/receipt.pdf`,

  // Phase 3 — Membership Center
  getMembershipSummary: () => request<MembershipSummary>('/member/membership'),
  getMembershipHistory: () => request<{ items: MembershipHistoryItem[]; count: number }>('/member/membership/history'),
  submitRenewal: (data: MembershipRenewalRequest) =>
    request<MembershipRenewalResult>('/member/membership/renew', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getApplicationDetails: () => request<ApplicationCenterDetails>('/member/application'),
  uploadApplicationDocument: (file: File, documentType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    return request<any>('/member/application/documents', {
      method: 'POST',
      body: formData,
    });
  },

  // Phase 4 — Document Center & Digital ID
  getDocumentSummary: (filter?: string) => {
    const q = filter && filter.toUpperCase() !== 'ALL' ? `?filter=${encodeURIComponent(filter.toUpperCase())}` : '';
    return request<any>(`/member/documents${q}`);
  },
  getDocumentDetail: (id: number) => request<any>(`/member/documents/${id}`),
  uploadDocument: (file: File, documentType: string, title?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);
    if (title) formData.append('title', title);
    return request<any>('/member/documents', {
      method: 'POST',
      body: formData,
    });
  },
  replaceDocument: (id: number, file: File, replacementReason?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (replacementReason) formData.append('replacement_reason', replacementReason);
    return request<any>(`/member/documents/${id}/replace`, {
      method: 'POST',
      body: formData,
    });
  },
  getDigitalMemberId: () => request<any>('/member/digital-id'),
  getDigitalMemberIdPdfUrl: () => `${API_BASE_URL}/api/v1/member/digital-id/pdf`,
  getMemberCertificatesList: () => request<any[]>('/member/certificates'),
  getMemberCertificateDetail: (id: number) => request<any>(`/member/certificates/${id}`),
  verifyMemberPublic: (ref: string) => request<any>(`/public/verify/member/${encodeURIComponent(ref)}`),
  verifyCertificatePublic: (ref: string) => request<any>(`/public/verify/certificate/${encodeURIComponent(ref)}`),

  // Phase 5 — Payments & Receipts
  getPaymentSummary: (statusFilter?: string) => {
    const q = statusFilter && statusFilter.toUpperCase() !== 'ALL' ? `?status=${encodeURIComponent(statusFilter.toUpperCase())}` : '';
    return request<PaymentSummary>(`/member/payments/summary${q}`);
  },
  getPaymentDetail: (id: number) => request<any>(`/member/payments/${id}`),
  getPaymentReceipt: (id: number) => request<any>(`/member/payments/${id}/receipt`),
  initiatePaymentCheckout: (data: { purpose: string; plan_code?: string; provider?: string; idempotency_key?: string }) =>
    request<any>('/member/payments/initiate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  verifyPaymentPublic: (ref: string) => request<any>(`/public/verify/payment/${encodeURIComponent(ref)}`),

  // Phase 6 — Events & Notifications
  getMemberEvents: (params?: { tab?: string; category?: string; search?: string; location?: string }) => {
    const q = new URLSearchParams();
    if (params?.tab) q.set('tab', params.tab);
    if (params?.category) q.set('category', params.category);
    if (params?.search) q.set('search', params.search);
    if (params?.location) q.set('location', params.location);
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<MemberEventsResponse>(`/member/events${qs}`);
  },
  getMemberEventDetail: (id: number) => request<MemberEventItem>(`/member/events/${id}`),
  registerMemberEvent: (id: number, payload?: any) =>
    request<any>(`/member/events/${id}/register`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),
  cancelMemberEvent: (id: number, reason?: string) =>
    request<any>(`/member/events/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  getMemberEventPass: (id: number) => request<{ ok: boolean; pass: MemberEventPass }>(`/member/events/${id}/pass`),
  getMemberEventQrUrl: (id: number) => `${API_BASE_URL}/api/v1/member/events/${id}/qr`,

  getMemberNotifications: (params?: { status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.limit) q.set('limit', params.limit.toString());
    if (params?.offset) q.set('offset', params.offset.toString());
    const qs = q.toString() ? `?${q.toString()}` : '';
    return request<MemberNotificationsResponse>(`/member/notifications${qs}`);
  },
  markNotificationRead: (id: number) =>
    request<{ ok: boolean; id: number; read_at: string }>(`/member/notifications/${id}/read`, {
      method: 'POST',
    }),
  markAllNotificationsRead: () =>
    request<{ ok: boolean; updated: number }>('/member/notifications/read-all', {
      method: 'POST',
    }),
  getNotificationSettings: () => request<NotificationSettingsResponse>('/member/notification-settings'),
  updateNotificationSettings: (preferences: any) =>
    request<{ ok: boolean; message: string; preferences: any }>('/member/notification-settings', {
      method: 'PATCH',
      body: JSON.stringify({ preferences }),
    }),

  // Admin Event Check-in
  getAdminEventAttendance: (eventId: number) =>
    request<AdminEventAttendanceResponse>(`/admin/events/${eventId}/attendance`),
  adminEventCheckIn: (eventId: number, data: { qr_token?: string; ticket_code?: string; method?: string }) =>
    request<AdminCheckInResult>(`/admin/events/${eventId}/check-in`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getAdminEventRegistrations: (eventId: number, status?: string) => {
    const q = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<any>(`/admin/events/${eventId}/registrations${q}`);
  },
};

