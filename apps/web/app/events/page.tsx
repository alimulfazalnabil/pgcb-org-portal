'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, EventItem } from '@/lib/api';

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [upcomingOnly, setUpcomingOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .getEvents(upcomingOnly)
      .then((rows) => setEvents(Array.isArray(rows) ? rows : []))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [upcomingOnly]);

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
              CONFERENCES, COUNCILS & WORKSHOPS
            </span>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
              কেন্দ্রীয় সম্মেলন, কাউন্সিল ও কারিগরি কর্মশালা
            </h1>
            <p className="text-slate-300 text-base max-w-2xl">
              ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর বার্ষিক সাধারণ সভা, আঞ্চলিক প্রতিনিধি সম্মেলন ও কারিগরি প্রশিক্ষণ কর্মসূচির ক্যালেন্ডার।
            </p>
          </div>

          <div className="flex items-center gap-2 bg-white/10 p-1.5 rounded-2xl border border-white/15 self-start">
            <button
              type="button"
              onClick={() => setUpcomingOnly(false)}
              className={`px-4 py-2 rounded-xl text-xs font-extrabold transition-all ${
                !upcomingOnly ? 'bg-emerald-500 text-white shadow-md' : 'text-slate-300 hover:text-white'
              }`}
            >
              সকল কর্মসূচি
            </button>
            <button
              type="button"
              onClick={() => setUpcomingOnly(true)}
              className={`px-4 py-2 rounded-xl text-xs font-extrabold transition-all ${
                upcomingOnly ? 'bg-emerald-500 text-white shadow-md' : 'text-slate-300 hover:text-white'
              }`}
            >
              আসন্ন কর্মসূচি
            </button>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-72 rounded-2xl bg-white border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : events.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
            <p className="text-lg font-bold text-slate-700 mb-1">কোনো নির্ধারিত ইভেন্ট বা সম্মেলন পাওয়া যায়নি</p>
            <p className="text-sm text-slate-500">পরবর্তী কর্মসূচির তারিখ ঘোষিত হলে এখানে প্রদর্শিত হবে।</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((ev) => (
              <article
                key={ev.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:shadow-xl hover:-translate-y-0.5 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-4">
                    <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {ev.event_date
                        ? new Date(ev.event_date).toLocaleDateString('bn-BD', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                          })
                        : 'তারিখ শীঘ্রই'}
                    </span>
                    <span className="text-xs font-bold text-slate-500">
                      {ev.fee_amount > 0 ? `৳${ev.fee_amount.toLocaleString('bn-BD')}` : 'বিনামূল্যে নিবন্ধন'}
                    </span>
                  </div>

                  <h2 className="text-xl font-extrabold text-slate-900 mb-2 leading-snug">
                    <Link href={`/events/${ev.id}`} className="hover:text-primary transition-colors">
                      {ev.title_bn}
                    </Link>
                  </h2>

                  <p className="text-xs font-bold text-slate-500 mb-3">
                    স্থান: {ev.location_bn || 'পিজিসিবি প্রধান কার্যালয় অডিটোরিয়াম, ঢাকা'}
                  </p>

                  <p className="text-sm text-slate-600 leading-relaxed mb-6 line-clamp-3">
                    {ev.description_bn || 'ডিপ্রকৌস (পিজিসিবি)-এর অফিসিয়াল প্রতিনিধি সম্মেলন ও কারিগরি অধিবেশন।'}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                  <Link
                    href={`/events/${ev.id}`}
                    className="text-sm font-extrabold text-slate-700 hover:text-primary transition-colors"
                  >
                    বিস্তারিত তথ্য
                  </Link>
                  <Link
                    href={`/events/${ev.id}/register`}
                    className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-extrabold hover:bg-emerald-800 transition-colors"
                  >
                    নিবন্ধন করুন →
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
