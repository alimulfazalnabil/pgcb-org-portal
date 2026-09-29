'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function JournalDetailPage({ params }: { params: { id: string } }) {
  const [item, setItem] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .getJournals()
      .then((rows) => {
        const list = Array.isArray(rows) ? rows : [];
        const match = list.find((x) => String(x.id) === String(params.id)) || list[0] || null;
        setItem(match);
      })
      .catch(() => setItem(null))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-screen py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto h-96 rounded-3xl bg-white border border-slate-200 animate-pulse" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="bg-slate-50 min-h-screen py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-xl mx-auto bg-white rounded-3xl border border-slate-200 p-10 text-center">
          <h1 className="text-2xl font-extrabold text-slate-900 mb-2">প্রকাশনা পাওয়া যায়নি</h1>
          <p className="text-sm text-slate-600 mb-6">অনুরোধকৃত কারিগরি জার্নালটি খুঁজে পাওয়া যায়নি।</p>
          <Link
            href="/journal"
            className="inline-flex items-center px-6 py-3 rounded-xl bg-primary text-white text-sm font-bold"
          >
            সকল জার্নাল দেখুন
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
            href="/journal"
            className="inline-flex items-center gap-2 text-sm font-bold text-slate-600 hover:text-primary transition-colors"
          >
            ← কারিগরি জার্নাল তালিকায় ফিরে যান
          </Link>
        </div>

        <article className="bg-white rounded-3xl border border-slate-200/80 shadow-lg overflow-hidden">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-8 sm:p-12 text-white">
            <div className="flex items-center gap-3 flex-wrap mb-4">
              <span className="px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                {item.category || 'TECHNICAL'}
              </span>
              {item.edition && (
                <span className="text-xs font-bold text-slate-300">সংস্করণ: {item.edition}</span>
              )}
              {item.publication_date && (
                <span className="text-xs font-bold text-slate-300">
                  • প্রকাশকাল: {new Date(item.publication_date).toLocaleDateString('bn-BD')}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight leading-snug">
              {item.title_bn}
            </h1>
            {item.title_en && (
              <p className="text-slate-300 text-base mt-2 font-medium">{item.title_en}</p>
            )}
          </div>

          <div className="p-8 sm:p-12 space-y-6 text-slate-700 leading-relaxed">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80">
              <h2 className="text-sm font-extrabold uppercase tracking-wider text-primary mb-2">
                গবেষণা সারসংক্ষেপ (Abstract)
              </h2>
              <p className="text-base text-slate-800 font-medium">{item.abstract_bn}</p>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-extrabold text-slate-900">প্রাসঙ্গিক কারিগরি প্রেক্ষাপট</h3>
              <p>
                বাংলাদেশের জাতীয় পাওয়ার গ্রিডে ৪০০ কেভি, ২৩০ কেভি এবং ১৩২ কেভি ট্রান্সমিশন নেটওয়ার্কের নির্ভরযোগ্যতা, ডিজিটাল সাবস্টেশন অটোমেশন (IEC 61850), নিউমেরিক রিলে প্রোটেকশন এবং ফ্রিকোয়েন্সি স্ট্যাবিলিটি নিশ্চিতকরণে পিজিসিবির ডিপ্লোমা প্রকৌশলীরা সরাসরি মাঠপর্যায়ে ও এনএলডিসিতে কাজ করছেন। এই প্রকাশনায় ব্যবহারিক অভিজ্ঞতা ও কারিগরি সুপারিশমালা তুলে ধরা হয়েছে।
              </p>
            </div>

            <div className="pt-6 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4">
              {item.document_url && item.document_url !== '#' ? (
                <a
                  href={item.document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-primary text-white text-sm font-extrabold hover:bg-emerald-800 transition-colors"
                >
                  পূর্ণাঙ্গ পিডিএফ ডাউনলোড করুন
                </a>
              ) : (
                <Link
                  href="/documents"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-900 text-white text-sm font-extrabold hover:bg-primary transition-colors"
                >
                  ডকুমেন্ট আর্কাইভ থেকে সংশ্লিষ্ট নথি দেখুন →
                </Link>
              )}

              <Link
                href="/journal"
                className="text-sm font-bold text-slate-500 hover:text-slate-900 transition-colors"
              >
                অন্যান্য গবেষণা প্রবন্ধ দেখুন
              </Link>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
