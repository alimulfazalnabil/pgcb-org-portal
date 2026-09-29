'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';

const CATEGORY_LABELS: Record<string, { bn: string; en: string }> = {
  TECHNICAL: { bn: 'কারিগরি গবেষণা প্রবন্ধ', en: 'Technical Research Paper' },
  REPORT: { bn: 'বিশেষ প্রতিবেদন ও গাইডলাইন', en: 'Special Report & Guideline' },
  SOUVENIR: { bn: 'স্মরণিকা ও বার্ষিক প্রকাশনা', en: 'Souvenir & Annual Publication' },
};

export default function JournalPage() {
  const { t, pick } = useLanguage();
  const [items, setItems] = useState<any[]>([]);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getJournals()
      .then((rows) => setItems(Array.isArray(rows) ? rows : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return items.filter((item) => {
      if (category !== 'ALL' && (item.category || '').toUpperCase() !== category) {
        return false;
      }
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return (
        (item.title_bn || '').toLowerCase().includes(q) ||
        (item.title_en || '').toLowerCase().includes(q) ||
        (item.abstract_bn || '').toLowerCase().includes(q) ||
        (item.abstract_en || '').toLowerCase().includes(q) ||
        (item.edition || '').toLowerCase().includes(q)
      );
    });
  }, [items, query, category]);

  return (
    <div className="bg-slate-50 min-h-screen py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-6 sm:p-10 text-white shadow-xl mb-10">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
            TECHNICAL JOURNAL & RESEARCH ARCHIVE
          </span>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
            {t('কারিগরি জার্নাল, গবেষণা ও স্মরণিকা', 'Technical Journal, Research & Souvenirs')}
          </h1>
          <p className="text-slate-300 text-sm sm:text-base max-w-3xl">
            {t(
              'উচ্চ ভোল্টেজ পাওয়ার গ্রিড ট্রান্সমিশন, সাবস্টেশন অটোমেশন, নিউমেরিক রিলে প্রোটেকশন এবং গ্রিড স্থিতিশীলতা বিষয়ে পিজিসিবির ডিপ্লোমা প্রকৌশলীদের গবেষণাপত্র ও বার্ষিক প্রকাশনা।',
              'Research papers and annual publications by PGCB diploma engineers on high-voltage power grid transmission, substation automation, numerical relay protection, and grid stability.'
            )}
          </p>
        </div>

        {/* Filter bar */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 sm:p-5 shadow-sm mb-8 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="relative flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('প্রবন্ধের শিরোনাম, বিষয় বা সংস্করণ দিয়ে খুঁজুন...', 'Search by paper title, topic, or edition...')}
              className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium text-slate-900"
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

          <div className="flex items-center gap-2 flex-wrap">
            {(['ALL', 'TECHNICAL', 'REPORT', 'SOUVENIR'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setCategory(cat)}
                className={`px-4 py-2 rounded-xl text-xs font-extrabold transition-all ${
                  category === cat
                    ? 'bg-primary text-white shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat === 'ALL'
                  ? t('সকল প্রকাশনা', 'All Publications')
                  : CATEGORY_LABELS[cat]
                  ? t(CATEGORY_LABELS[cat].bn, CATEGORY_LABELS[cat].en)
                  : cat}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-64 rounded-2xl bg-white border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
            <p className="text-lg font-bold text-slate-700 mb-1">
              {t('কোনো জার্নাল বা প্রকাশনা পাওয়া যায়নি', 'No journals or publications found')}
            </p>
            <p className="text-sm text-slate-500">
              {t('অনুসন্ধান ফিল্টার পরিবর্তন করে পুনরায় চেষ্টা করুন।', 'Please try again with a different search filter.')}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((item) => (
              <article
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm hover:shadow-xl hover:-translate-y-0.5 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-4">
                    <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {CATEGORY_LABELS[item.category]
                        ? t(CATEGORY_LABELS[item.category].bn, CATEGORY_LABELS[item.category].en)
                        : item.category || 'TECHNICAL'}
                    </span>
                    {item.edition && (
                      <span className="text-xs font-bold text-slate-500">{item.edition}</span>
                    )}
                  </div>

                  <h2 className="text-lg sm:text-xl font-extrabold text-slate-900 mb-3 leading-snug">
                    <Link href={`/journal/${item.id}`} className="hover:text-primary transition-colors">
                      {pick(item, 'title', item.title_bn)}
                    </Link>
                  </h2>

                  <p className="text-sm text-slate-600 leading-relaxed mb-6 line-clamp-3">
                    {pick(
                      item,
                      'abstract',
                      item.abstract_bn || t('পাওয়ার গ্রিড ট্রান্সমিশন ও সাবস্টেশন ইঞ্জিনিয়ারিং গবেষণা সারসংক্ষেপ।', 'Power grid transmission and substation engineering research abstract.')
                    )}
                  </p>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                  <Link
                    href={`/journal/${item.id}`}
                    className="inline-flex items-center gap-1.5 text-sm font-extrabold text-primary hover:text-emerald-800"
                  >
                    {t('সারসংক্ষেপ ও বিস্তারিত পড়ুন →', 'Read Abstract & Details →')}
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
