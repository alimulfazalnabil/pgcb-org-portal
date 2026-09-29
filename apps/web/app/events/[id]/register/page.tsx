'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api, EventItem } from '@/lib/api';

export default function EventRegisterPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const eventId = Number(params.id);
  const [ev, setEv] = useState<EventItem | null>(null);
  const [ticketCount, setTicketCount] = useState(1);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getEvent(eventId)
      .then((res) => setEv(res))
      .catch(() => setEv(null));
  }, [eventId]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await api.registerForEvent(eventId, {
        ticket_count: ticketCount,
        notes: notes.trim() || undefined,
      });
      const code = res?.ticket_code || `EVT-${eventId}-${Date.now().toString().slice(-5)}`;
      router.push(`/events/ticket/${encodeURIComponent(code)}`);
    } catch (err: any) {
      if (err?.status === 401 || err?.status === 403) {
        setError('ইভেন্ট নিবন্ধনের জন্য অনুগ্রহ করে প্রথমে আপনার সদস্য অ্যাকাউন্টে লগইন করুন।');
      } else {
        setError(err?.message || 'নিবন্ধন সম্পন্ন করা যায়নি। অনুগ্রহ করে পুনরায় চেষ্টা করুন।');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <Link
            href={`/events/${params.id}`}
            className="inline-flex items-center gap-2 text-sm font-bold text-slate-600 hover:text-primary transition-colors"
          >
            ← ইভেন্ট বিবরণীতে ফিরে যান
          </Link>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-3xl border border-slate-200/80 shadow-lg overflow-hidden"
        >
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-8 text-white">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
              DELEGATE REGISTRATION
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-1">
              {ev?.title_bn || `ইভেন্ট #${params.id} নিবন্ধন ফর্ম`}
            </h1>
            <p className="text-slate-300 text-sm">
              নিবন্ধন সফল হলে তাৎক্ষণিক কিউআর ই-টিকেট ও ডেলিগেট পাস ইস্যু করা হবে।
            </p>
          </div>

          <div className="p-8 space-y-6">
            {error && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-sm font-semibold flex flex-col gap-2">
                <span>{error}</span>
                <div>
                  <Link
                    href="/login"
                    className="inline-flex items-center px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-extrabold hover:bg-primary transition-colors"
                  >
                    সদস্য লগইন পেজে যান →
                  </Link>
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                ডেলিগেট টিকেট সংখ্যা
              </label>
              <select
                value={ticketCount}
                onChange={(e) => setTicketCount(Number(e.target.value))}
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-bold text-slate-900"
              >
                <option value={1}>১ জন (সদস্য নিজে)</option>
                <option value={2}>২ জন (সদস্য + ১ জন অতিথি)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                বিশেষ মন্তব্য / সার্কেল বা দপ্তরের নাম (ঐচ্ছিক)
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="আপনার গ্রিড সার্কেল, জিএমডি অথবা বিশেষ কোনো তথ্য থাকলে উল্লেখ করুন..."
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
              />
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="px-8 py-3.5 rounded-xl bg-primary hover:bg-emerald-800 disabled:opacity-60 text-white text-sm font-extrabold shadow-md transition-all"
              >
                {submitting ? 'নিবন্ধন প্রক্রিয়াকরণ হচ্ছে...' : 'নিবন্ধন নিশ্চিত করুন ও ই-টিকেট নিন'}
              </button>
              <Link
                href={`/events/${params.id}`}
                className="text-sm font-bold text-slate-500 hover:text-slate-900"
              >
                বাতিল করুন
              </Link>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
