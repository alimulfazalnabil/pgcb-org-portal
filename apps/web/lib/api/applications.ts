import { request } from './client';
import { ApplicationTrackResult } from './types';

export const applicationsApi = {
  submitApplication: (data: any) =>
    request<{ ok: boolean; application_no: string; message: string }>('/public/membership/apply', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  trackApplication: (applicationNo: string) =>
    request<ApplicationTrackResult>(`/public/membership/track/${encodeURIComponent(applicationNo)}`),
  getMemberApplication: () => request<any>('/member/application'),
  submitMemberApplication: () =>
    request<any>('/member/application', { method: 'POST' }),
};
