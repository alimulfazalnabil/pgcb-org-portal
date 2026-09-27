import { request, API_BASE_URL } from './client';
import { DocumentItem } from './types';

export const documentsApi = {
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
};
