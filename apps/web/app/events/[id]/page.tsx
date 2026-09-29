'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api, EventItem } from '@/lib/api';

export default function EventDetailPage() {
  const params = useParams<{ id: string }>();
  const eventId = String(params?.id || '');
  const [ev, setEv] = useState<EventItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getEvent(Number(eventId))
      .then((res) => setEv(res))
      .catch(() => setEv(null))
      .finally(() => setLoading(false));
  }, [eventId]);

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-screen py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto h-96 rounded-3xl bg-white border border-slate-200 animate-pulse" />
      </div>
    );
  }

  if (!ev) {
    return (
      <div className="bg-slate-50 min-h-screen py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-xl mx-auto bg-white rounded-3xl border border-slate-200 p-10 text-center">
          <h1 className="text-2xl font-extrabold text-slate-900 mb-2">ইভেন্ট খুঁজে পাওয়া যায়নি</h1>
          <p className="text-sm text-slate-600 mb-6">অনুরোধকৃত সম্মেলন বা কর্মশালার তথ্য পাওয়া যায়নি।</p>
          <Link
            href="/events"
            className="inline-flex items-center px-6 py-3 rounded-xl bg-primary text-white text-sm font-bold"
          >
            সকল ইভেন্ট দেখুন
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link
            href="/events"
            className="inline-flex items-center gap-2 text-sm font-bold text-slate-600 hover:text-primary transition-colors"
          >
            ← সকল সম্মেলন ও কর্মশালা
          </Link>
        </div>

        <article className="bg-white rounded-3xl border border-slate-200/80 shadow-lg overflow-hidden">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-8 sm:p-12 text-white">
            <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-4">
              OFFICIAL EVENT • #{ev.id}
            </span>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight mb-3">{ev.title_bn}</h1>
            {ev.title_en && <p className="text-slate-300 text-base">{ev.title_en}</p>}
          </div>

          <div className="p-8 sm:p-12 space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70">
                <div className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">তারিখ ও সময়</div>
                <div className="font-bold text-slate-900 text-sm">
                  {ev.event_date ? new Date(ev.event_date).toLocaleString('bn-BD') : 'তারিখ শীঘ্রই ঘোষিত হবে'}
                </div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70">
                <div className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">ভেন্যু / স্থান</div>
                <div className="font-bold text-slate-900 text-sm">
                  {ev.location_bn || 'পিজিসিবি হেড অফিস অডিটোরিয়াম, ঢাকা'}
                </div>
              </div>
              <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/70">
                <div className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">আসন সংখ্যা ও ফি</div>
                <div className="font-bold text-slate-900 text-sm">
                  {ev.capacity || 300} আসন •{' '}
                  {ev.fee_amount > 0 ? `৳${ev.fee_amount.toLocaleString('bn-BD')}` : 'বিনামূল্যে'}
                </div>
              </div>
            </div>

            <div className="space-y-4 text-slate-700 leading-relaxed">
              <h2 className="text-lg font-extrabold text-slate-900">কর্মসূচির বিবরণ</h2>
              <p>
                {ev.description_bn ||
                  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি (পিজিসিবি)-এর ডিপ্লোমা প্রকৌশলীদের অংশগ্রহণে কেন্দ্রীয় অধিবেশন, কারিগরি প্রেজেন্টেশন এবং প্যানেল আলোচনা অনুষ্ঠিত হবে।'}
              </p>
            </div>

            <div className="pt-6 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4">
              <Link
                href={`/events/${ev.id}/register`}
                className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-primary text-white text-sm font-extrabold hover:bg-emerald-800 shadow-md transition-all"
              >
                অংশগ্রহণের জন্য নিবন্ধন করুন →
              </Link>
              <Link
                href="/events"
                className="text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors"
              >
                সকল ইভেন্ট দেখুন
              </Link>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
