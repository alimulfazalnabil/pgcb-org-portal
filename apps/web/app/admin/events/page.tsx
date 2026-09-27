'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { api, EventItem } from '@/lib/api';
import {
  Calendar,
  Plus,
  Trash2,
  Users,
  MapPin,
  Clock,
  Ticket,
} from 'lucide-react';
import Link from 'next/link';

export default function AdminEventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [formData, setFormData] = useState({
    title_bn: '',
    title_en: '',
    description_bn: '',
    event_date: '',
    location_bn: '',
    registration_enabled: true,
    capacity: 200,
    fee_amount: 0,
    fee_currency: 'BDT',
    is_published: true,
  });

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents(false);
      setEvents(data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch('/backend/api/v1/admin/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('ইভেন্ট তৈরি করা সম্ভব হয়নি।');
      setMessage({ text: 'নতুন ইভেন্ট সফলভাবে প্রকাশিত হয়েছে।', type: 'success' });
      setCreateModal(false);
      fetchEvents();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="ইভেন্ট ও সম্মেলন পরিচালনা (Events & Conferences)"
        subtitle="বার্ষিক সম্মেলন, কাউন্সিল অধিবেশন এবং পেশাগত প্রশিক্ষণ ইভেন্ট ব্যবস্থাপনা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Status Toast */}
        {message && (
          <div
            className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between border ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-700'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">
              ✕
            </button>
          </div>
        )}

        {/* Toolbar */}
        <div className="flex justify-between items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <Calendar size={18} className="text-primary" />
            <span>নিবন্ধিত ইভেন্টের তালিকা ({events.length}টি)</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/admin/attendance"
              className="px-3.5 py-2 rounded-xl border border-border bg-card hover:bg-surface text-foreground text-xs font-bold transition-all flex items-center gap-1.5"
            >
              <Ticket size={14} /> কিউআর স্ক্যান ডেস্ক
            </Link>
            <button
              onClick={() => setCreateModal(true)}
              className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
            >
              <Plus size={14} /> নতুন ইভেন্ট তৈরি করুন
            </button>
          </div>
        </div>

        {/* Events Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading ? (
            <div className="col-span-2 p-8 text-center text-secondary text-xs">ইভেন্ট লোড হচ্ছে...</div>
          ) : events.length === 0 ? (
            <div className="col-span-2 p-8 text-center text-secondary text-xs">কোনো ইভেন্ট পাওয়া যায়নি।</div>
          ) : (
            events.map((ev) => (
              <div
                key={ev.id}
                className="bg-card border border-border p-5 rounded-2xl shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4"
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-bold text-foreground text-sm leading-snug">{ev.title_bn}</h3>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 ${
                        ev.registration_enabled
                          ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
                          : 'bg-surface text-secondary border border-border'
                      }`}
                    >
                      {ev.registration_enabled ? 'নিবন্ধন সক্রিয়' : 'নিবন্ধন বন্ধ'}
                    </span>
                  </div>
                  {ev.title_en && <p className="text-xs text-secondary mt-1">{ev.title_en}</p>}
                </div>

                <div className="space-y-1.5 text-xs text-secondary bg-surface/60 p-3 rounded-xl border border-border">
                  <div className="flex items-center gap-2">
                    <Clock size={13} className="text-primary shrink-0" />
                    <span>তারিখ: {ev.event_date ? new Date(ev.event_date).toLocaleDateString('bn-BD') : 'নির্ধারিত হয়নি'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={13} className="text-primary shrink-0" />
                    <span>স্থান: {ev.location_bn || 'পিজিসিবি অডিটোরিয়াম'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users size={13} className="text-primary shrink-0" />
                    <span>ধারণক্ষমতা: {ev.capacity ? `${ev.capacity} জন` : 'সীমাহীন'}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-border text-xs">
                  <span className="font-bold text-foreground">
                    ফি: {ev.fee_amount ? `৳${ev.fee_amount}` : 'বিনামূল্যে'}
                  </span>
                  <Link
                    href="/admin/attendance"
                    className="px-3 py-1.5 rounded-xl border border-border bg-surface hover:bg-card text-primary font-semibold text-xs inline-flex items-center gap-1"
                  >
                    উপস্থিতি পরিচালনা <Ticket size={13} />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Create Event Modal */}
      {createModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-border flex items-center justify-between bg-surface/50">
              <h3 className="text-sm font-bold text-foreground">নতুন প্রাতিষ্ঠানিক ইভেন্ট তৈরি</h3>
              <button onClick={() => setCreateModal(false)} className="text-secondary text-sm">✕</button>
            </div>

            <form onSubmit={handleCreate} className="p-6 space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">ইভেন্টের শিরোনাম (বাংলা) *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: ১৩তম বার্ষিক সাধারণ সম্মেলন ও প্রতিনিধি অধিবেশন ২০২৬..."
                  value={formData.title_bn}
                  onChange={(e) => setFormData({ ...formData, title_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">তারিখ ও সময় *</label>
                  <input
                    required
                    type="datetime-local"
                    value={formData.event_date}
                    onChange={(e) => setFormData({ ...formData, event_date: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">সর্বোচ্চ আসন সংখ্যা</label>
                  <input
                    type="number"
                    value={formData.capacity}
                    onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                    className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">অনুষ্ঠানস্থল (স্থান) *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: পিজিসিবি হেড অফিস অডিটোরিয়াম, আফতাবনগর, ঢাকা..."
                  value={formData.location_bn}
                  onChange={(e) => setFormData({ ...formData, location_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-foreground">
                  <input
                    type="checkbox"
                    checked={formData.registration_enabled}
                    onChange={(e) => setFormData({ ...formData, registration_enabled: e.target.checked })}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span>সদস্য অনলাইন নিবন্ধন উন্মুক্ত রাখুন</span>
                </label>
              </div>

              <div className="p-4 border-t border-border flex justify-end gap-2.5 bg-surface/50 -mx-6 -mb-6 mt-4">
                <button
                  type="button"
                  onClick={() => setCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
                >
                  বাতিল
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
                >
                  {busy ? 'তৈরি হচ্ছে...' : 'ইভেন্ট প্রকাশ করুন'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
