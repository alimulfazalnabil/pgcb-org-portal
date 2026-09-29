import { request, API_BASE_URL } from './client';
import { PublicMember, CircleItem, CommitteeItem } from './types';

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
  markAllNotificationsRead: () =>
    request<any>('/member/notifications/read-all', { method: 'POST' }),
  getNotificationPreferences: () => request<any>('/member/notification-preferences'),
  updateNotificationPreferences: (prefs: Record<string, any>) =>
    request<any>('/member/notification-preferences', { method: 'PUT', body: JSON.stringify(prefs) }),
  getMemberDashboard: () => request<any>('/member/dashboard'),
  getRenewalOptions: () => request<any>('/member/renewal-options'),
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
};
