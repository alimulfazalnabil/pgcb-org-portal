'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';

export default function MediaPage() {
  const [items, setItems] = useState<any[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'PHOTO' | 'VIDEO'>('ALL');
  const [selected, setSelected] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getMedia()
      .then((rows) => setItems(Array.isArray(rows) ? rows : []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    if (filter === 'ALL') return items;
    return items.filter((item) => (item.media_type || 'PHOTO').toUpperCase() === filter);
  }, [items, filter]);

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-10">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div>
              <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
                MEDIA ARCHIVE • GALLERY
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
                মিডিয়া গ্যালারি ও ফটো আর্কাইভ
              </h1>
              <p className="text-slate-300 text-base max-w-2xl">
                ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর কেন্দ্রীয় সম্মেলন, কারিগরি কর্মশালা, গ্রিড পরিদর্শন এবং সাংগঠনিক কার্যক্রমের আলোকচিত্র ও ভিডিও সংগ্রহ।
              </p>
            </div>

            <div className="flex items-center gap-2 bg-white/10 p-1.5 rounded-2xl border border-white/15 self-start">
              {(
                [
                  { id: 'ALL', label: 'সকল মিডিয়া' },
                  { id: 'PHOTO', label: 'আলোকচিত্র' },
                  { id: 'VIDEO', label: 'ভিডিও' },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilter(tab.id)}
                  className={`px-4 py-2 rounded-xl text-xs font-extrabold transition-all ${
                    filter === tab.id
                      ? 'bg-emerald-500 text-white shadow-md'
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((n) => (
              <div key={n} className="h-72 rounded-2xl bg-white border border-slate-200 animate-pulse" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
            <p className="text-lg font-bold text-slate-700 mb-1">কোনো মিডিয়া আইটেম পাওয়া যায়নি</p>
            <p className="text-sm text-slate-500">নতুন আলোকচিত্র বা ভিডিও শীঘ্রই যুক্ত করা হবে।</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((item) => {
              const rawUrl = item.thumbnail_url || item.url;
              const hasValidImage = rawUrl && rawUrl !== '#' && !rawUrl.startsWith('javascript:');
              const imgSrc = hasValidImage ? rawUrl : '/brand/pgcb-logo.svg';

              return (
                <article
                  key={item.id}
                  onClick={() => setSelected(item)}
                  className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-0.5 transition-all cursor-pointer group flex flex-col"
                >
                  <div className="relative h-52 bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 flex items-center justify-center overflow-hidden">
                    <img
                      src={imgSrc}
                      alt={item.title_bn}
                      className={`${
                        imgSrc.endsWith('.svg')
                          ? 'w-24 h-24 object-contain opacity-90'
                          : 'w-full h-full object-cover'
                      } group-hover:scale-105 transition-transform duration-300`}
                    />
                    <span className="absolute top-3 left-3 px-3 py-1 rounded-full text-[11px] font-extrabold uppercase tracking-wider bg-slate-900/80 text-emerald-300 border border-emerald-400/30 backdrop-blur-sm">
                      {item.media_type === 'VIDEO' ? 'ভিডিও' : 'আলোকচিত্র'}
                    </span>
                  </div>

                  <div className="p-6 flex-1 flex flex-col justify-between">
                    <div>
                      <h2 className="text-lg font-extrabold text-slate-900 group-hover:text-primary transition-colors mb-2">
                        {item.title_bn}
                      </h2>
                      <p className="text-sm text-slate-600 line-clamp-2">
                        {item.description_bn ||
                          'ডিপ্রকৌস (পিজিসিবি)-এর অফিসিয়াল সাংগঠনিক কার্যক্রম ও কারিগরি অধিবেশনের দৃশ্যপট।'}
                      </p>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs font-bold text-primary">
                      <span>বিস্তারিত প্রিভিউ দেখুন</span>
                      <span>→</span>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {/* Lightbox Modal */}
        {selected && (
          <div
            className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setSelected(null)}
          >
            <div
              className="bg-white rounded-3xl max-w-3xl w-full overflow-hidden shadow-2xl border border-slate-200"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="relative h-72 sm:h-96 bg-slate-900 flex items-center justify-center">
                <img
                  src={
                    selected.url && selected.url !== '#'
                      ? selected.url
                      : '/brand/pgcb-logo.svg'
                  }
                  alt={selected.title_bn}
                  className={
                    selected.url && selected.url !== '#' && !selected.url.endsWith('.svg')
                      ? 'w-full h-full object-contain'
                      : 'w-36 h-36 object-contain'
                  }
                />
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="absolute top-4 right-4 w-10 h-10 rounded-full bg-slate-900/80 text-white font-bold hover:bg-red-600 transition-colors"
                  aria-label="বন্ধ করুন"
                >
                  ✕
                </button>
              </div>
              <div className="p-6 sm:p-8">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-emerald-50 text-emerald-800 mb-2">
                  {selected.media_type === 'VIDEO' ? 'ভিডিও আর্কাইভ' : 'ফটো আর্কাইভ'}
                </span>
                <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900 mb-2">
                  {selected.title_bn}
                </h3>
                <p className="text-sm sm:text-base text-slate-600">
                  {selected.description_bn ||
                    'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি (ডিপ্রকৌস)-এর কেন্দ্রীয় ও আঞ্চলিক কার্যক্রমের অফিসিয়াল মিডিয়া সংরক্ষণাগার।'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
