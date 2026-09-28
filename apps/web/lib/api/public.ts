import { request } from './client';
import { PublicStats, CircularItem } from './types';

export const publicApi = {
  getStats: () => request<PublicStats>('/public/stats'),
  getSettings: () => request<Record<string, string>>('/public/settings'),
  getCirculars: (params?: { q?: string; category?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.q) query.set('q', params.q);
    if (params?.category) query.set('category', params.category);
    if (params?.limit) query.set('limit', params.limit.toString());
    if (params?.offset) query.set('offset', params.offset.toString());
    return request<CircularItem[]>(`/public/circulars?${query.toString()}`);
  },
  getCircular: (id: number) => request<CircularItem>(`/public/circulars/${id}`),
  getJournals: (q?: string) => request<any[]>(`/public/journals${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  getMedia: (type?: string) => request<any[]>(`/public/media${type ? `?media_type=${type}` : ''}`),
  getNews: (params?: { q?: string; category?: string; tag?: string; featured?: boolean; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.q) query.set('q', params.q);
    if (params?.category) query.set('category', params.category);
    if (params?.tag) query.set('tag', params.tag);
    if (params?.featured !== undefined) query.set('featured', String(params.featured));
    if (params?.limit) query.set('limit', params.limit.toString());
    return request<any[]>(`/public/news?${query.toString()}`);
  },
  getNewsDetail: (slugOrId: string | number) => request<any>(`/public/news/${encodeURIComponent(String(slugOrId))}`),
  getNewsBySlug: (slug: string) => request<any>(`/public/news/${encodeURIComponent(slug)}`),
  getHomepageConfig: () => request<any>('/public/homepage-config'),
  search: (q: string) =>
    request<{ query: string; count: number; results: any[] }>(`/public/search?q=${encodeURIComponent(q)}`),
  submitContact: (data: { name: string; email: string; phone?: string; subject: string; message: string }) =>
    request<{ ok: boolean; message_id: number; ticket_no?: string; status?: string }>('/public/contact', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
