'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api, CircleItem } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';

export default function CirclesPage() {
  const { language, t, pick, formatNumber } = useLanguage();
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getCircles()
      .then((rows) => setCircles(Array.isArray(rows) ? rows : []))
      .catch(() => setCircles([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return circles;
    return circles.filter(
      (c) =>
        (c.name_bn || '').toLowerCase().includes(q) ||
        (c.name_en || '').toLowerCase().includes(q) ||
        (c.description_bn || '').toLowerCase().includes(q) ||
        (c.description_en || '').toLowerCase().includes(q)
    );
  }, [circles, query]);

  const totalActiveMembers = useMemo(
    () => circles.reduce((sum, c) => sum + (Number(c.active_members) || 0), 0),
    [circles]
  );

  return (
    <div className="bg-slate-50 min-h-screen py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-6 sm:p-10 text-white shadow-xl mb-8 relative overflow-hidden">
          <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div className="max-w-2xl">
              <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
                DIPROKOUS REGIONAL NETWORK • 2026–2028
              </span>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
                {t('শাখা কমিটি ও আঞ্চলিক গ্রিড সার্কেলসমূহ', 'Branch Committees & Regional Grid Circles')}
              </h1>
              <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
                {t(
                  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি (পিজিসিবি)-এর দেশব্যাপী আঞ্চলিক গ্রিড সার্কেল, জিএমডি ও দপ্তরভিত্তিক ডিপ্রকৌস শাখা কমিটি এবং নিবন্ধিত প্রকৌশলী ডিরেক্টরি।',
                  'Nationwide regional grid circles, GMD offices, and branch committees of the Power Grid Company of Bangladesh PLC (PGCB) along with the registered engineer directory.'
                )}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 shrink-0">
              <div className="bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 sm:p-5 text-center">
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                  {formatNumber(circles.length || 20)}
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mt-1">
                  {t('সক্রিয় শাখা / সার্কেল', 'Active Branches / Circles')}
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 sm:p-5 text-center">
                <div className="text-2xl sm:text-3xl font-extrabold text-amber-300">
                  {formatNumber(totalActiveMembers > 0 ? totalActiveMembers : 1457)}
                </div>
                <div className="text-xs font-bold uppercase tracking-wider text-slate-300 mt-1">
                  {t('তালিকাভুক্ত প্রকৌশলী', 'Registered Engineers')}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Search & Filter */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-sm mb-8 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t(
                'সার্কেল বা শাখা কমিটির নাম দিয়ে খুঁজুন (যেমন: ঢাকা, খুলনা, বগুড়া, এনএলডিসি)...',
                'Search by circle or branch committee name (e.g., Dhaka, Khulna, Bogura, NLDC)...'
              )}
              className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary focus:ring-2 focus:ring-primary/15 outline-none text-sm font-medium text-slate-900 transition-all"
            />
            <svg
              className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/members"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-primary text-white text-sm font-bold transition-colors"
            >
              {t('সম্পূর্ণ সদস্য ডিরেক্টরি দেখুন →', 'View Full Member Directory →')}
            </Link>
          </div>
        </div>

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <div key={n} className="h-56 rounded-2xl bg-white border border-slate-200 p-6 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
            <p className="text-lg font-bold text-slate-700 mb-2">
              {t('কোনো গ্রিড সার্কেল বা শাখা কমিটি পাওয়া যায়নি', 'No grid circle or branch committee found')}
            </p>
            <p className="text-sm text-slate-500">
              {t('অনুসন্ধান শব্দ পরিবর্তন করে পুনরায় চেষ্টা করুন।', 'Please try again with a different search term.')}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((circle) => {
              const slug = circle.slug || String(circle.id);
              const memberCount = Number(circle.active_members) || 0;
              const circleTitle = pick(circle, 'name', circle.name_bn);
              const circleDesc =
                language === 'en'
                  ? circle.description_en ||
                    `Integrated organizational unit of diploma engineers at PGCB ${circle.name_en || circle.name_bn} regional office and grid substations.`
                  : circle.description_bn ||
                    `পিজিসিবি ${circle.name_bn} আঞ্চলিক কার্যালয় ও আওতাধীন গ্রিড সাবস্টেশনের ডিপ্লোমা প্রকৌশলীদের সমন্বিত ইউনিট।`;

              return (
                <article
                  key={circle.id}
                  className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:shadow-xl hover:-translate-y-0.5 hover:border-primary/40 transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="flex items-center justify-between gap-3 mb-4">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {circle.name_en || `Circle #${circle.id}`}
                      </span>
                      <span className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-full">
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                        {language === 'en' ? `${formatNumber(memberCount)} Members` : `${formatNumber(memberCount)} জন সদস্য`}
                      </span>
                    </div>

                    <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 group-hover:text-primary transition-colors mb-2">
                      {circleTitle}
                    </h2>
                    <p className="text-sm text-slate-600 leading-relaxed mb-6">
                      {circleDesc}
                    </p>
                  </div>

                  <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                    <Link
                      href={`/circles/${encodeURIComponent(slug)}`}
                      className="inline-flex items-center gap-1.5 text-sm font-extrabold text-primary hover:text-emerald-800 transition-colors"
                    >
                      {t('সার্কেল প্রোফাইল ও সদস্যবৃন্দ', 'Circle Profile & Members')}
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                      </svg>
                    </Link>
                    <Link
                      href={`/members?circle_id=${circle.id}`}
                      className="text-xs font-bold text-slate-500 hover:text-slate-900 transition-colors"
                    >
                      {t('ডিরেক্টরি ফিল্টার', 'Filter Directory')}
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
