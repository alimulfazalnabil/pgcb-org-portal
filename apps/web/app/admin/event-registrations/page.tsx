'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import {
  Calendar,
  CheckCircle2,
  FileDown,
  Search,
  UserCheck,
  XCircle,
} from 'lucide-react';

export default function AdminEventRegistrationsPage() {
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedEventId) params.set('event_id', selectedEventId);
      if (statusFilter) params.set('status', statusFilter);

      const [regRes, evRes] = await Promise.all([
        fetch(`/backend/api/v1/admin/event-registrations?${params.toString()}`).then((r) =>
          r.ok ? r.json() : []
        ),
        fetch('/backend/api/v1/admin/events').then((r) => (r.ok ? r.json() : [])),
      ]);
      setRegistrations(Array.isArray(regRes) ? regRes : []);
      setEvents(Array.isArray(evRes) ? evRes : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedEventId, statusFilter]);

  const handleStatusChange = async (regId: number, status: string) => {
    try {
      const res = await fetch(`/backend/api/v1/admin/event-registrations/${regId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error('স্ট্যাটাস পরিবর্তন ব্যর্থ হয়েছে।');
      setMessage({ text: `রেজিস্ট্রেশন স্ট্যাটাস '${status}'-এ আপডেট করা হয়েছে।`, type: 'success' });
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    }
  };

  const handleCheckIn = async (regId: number) => {
    try {
      const res = await fetch(`/backend/api/v1/admin/event-registrations/${regId}/check-in`, {
        method: 'POST',
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'চেক-ইন সম্পন্ন করা যায়নি।');
      }
      setMessage({ text: 'উপস্থিতি (Check-in) সফলভাবে রেকর্ড করা হয়েছে।', type: 'success' });
      loadData();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    }
  };

  const filtered = registrations.filter((r) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (r.name || '').toLowerCase().includes(q) ||
      (r.email || '').toLowerCase().includes(q) ||
      (r.ticket_code || '').toLowerCase().includes(q) ||
      (r.phone || '').toLowerCase().includes(q)
    );
  });

  return (
    <>
      <AdminHeader
        title="ইভেন্ট নিবন্ধন ও অংশগ্রহণকারী ব্যবস্থাপনা (Event Registrations)"
        subtitle="সম্মেলন ও সেমিনারে নিবন্ধিত সদস্যদের তালিকা, টিকিট কোড যাচাই এবং উপস্থিতি অনুমোদন"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {message && (
          <div
            className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between border ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-700'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)}>✕</button>
          </div>
        )}

        {/* Filters */}
        <div className="bg-card border border-border rounded-2xl p-4 flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between shadow-sm">
          <div className="flex flex-wrap gap-3 flex-1">
            <div className="relative flex-1 min-w-[220px]">
              <Search size={15} className="absolute left-3 top-2.5 text-secondary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="নাম, ইমেইল বা টিকিট কোড দিয়ে খুঁজুন..."
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
              />
            </div>

            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              className="px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
            >
              <option value="">সকল ইভেন্ট (All Events)</option>
              {events.map((ev) => (
                <option key={ev.id} value={String(ev.id)}>
                  {ev.title_bn || ev.title_en}
                </option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
            >
              <option value="">সকল স্ট্যাটাস</option>
              <option value="REGISTERED">REGISTERED</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="WAITLISTED">WAITLISTED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <a
            href="/backend/api/v1/admin/exports/event-registrations.csv"
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0"
          >
            <FileDown size={14} /> CSV ডাউনলোড
          </a>
        </div>

        {/* Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">টিকিট কোড</th>
                  <th className="p-4">অংশগ্রহণকারী</th>
                  <th className="p-4">যোগাযোগ</th>
                  <th className="p-4">রেজিস্ট্রেশন</th>
                  <th className="p-4">উপস্থিতি</th>
                  <th className="p-4">পেমেন্ট</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-secondary">
                      ইভেন্ট নিবন্ধন তালিকা লোড হচ্ছে...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-secondary">
                      কোনো নিবন্ধন পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  filtered.map((reg) => (
                    <tr key={reg.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-mono font-bold text-primary">{reg.ticket_code}</td>
                      <td className="p-4">
                        <div className="font-bold text-foreground">{reg.name}</div>
                        <div className="text-[11px] text-secondary">{reg.organization || 'PGCB'}</div>
                      </td>
                      <td className="p-4 text-secondary">
                        <div>{reg.email}</div>
                        <div className="text-[11px]">{reg.phone || '—'}</div>
                      </td>
                      <td className="p-4">
                        <StatusBadge status={reg.registration_status} />
                      </td>
                      <td className="p-4">
                        <StatusBadge status={reg.attendance_status} />
                      </td>
                      <td className="p-4">
                        <StatusBadge status={reg.payment_status} />
                      </td>
                      <td className="p-4 text-right space-x-1.5">
                        {reg.attendance_status !== 'CHECKED_IN' &&
                          reg.registration_status !== 'CANCELLED' && (
                            <button
                              onClick={() => handleCheckIn(reg.id)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-bold text-[11px] inline-flex items-center gap-1"
                            >
                              <UserCheck size={12} /> চেক-ইন
                            </button>
                          )}
                        {reg.registration_status !== 'CONFIRMED' && (
                          <button
                            onClick={() => handleStatusChange(reg.id, 'CONFIRMED')}
                            className="px-2.5 py-1 rounded-lg border border-border bg-surface hover:bg-card text-foreground font-semibold text-[11px]"
                          >
                            নিশ্চিত করুন
                          </button>
                        )}
                        {reg.registration_status !== 'CANCELLED' && (
                          <button
                            onClick={() => handleStatusChange(reg.id, 'CANCELLED')}
                            className="px-2.5 py-1 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 font-semibold text-[11px]"
                          >
                            বাতিল
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
