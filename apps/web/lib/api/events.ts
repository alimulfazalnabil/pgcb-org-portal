import { request } from './client';
import { EventItem } from './types';

export const eventsApi = {
  getEvents: (upcoming = false) => request<EventItem[]>(`/public/events?upcoming=${upcoming}`),
  getEvent: (id: number) => request<EventItem>(`/public/events/${id}`),
  registerForEvent: (eventId: number, data: { ticket_count?: number; notes?: string }) =>
    request<any>(`/events/${eventId}/register`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  checkInTicket: (ticketCode: string) =>
    request<any>('/admin/events/checkin', {
      method: 'POST',
      body: JSON.stringify({ ticket_code: ticketCode }),
    }),
};
