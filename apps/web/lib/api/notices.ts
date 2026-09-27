import { request } from './client';
import { Notice } from './types';

export const noticesApi = {
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
};
