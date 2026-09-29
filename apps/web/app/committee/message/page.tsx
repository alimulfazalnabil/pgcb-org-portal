'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, CommitteeItem } from '@/lib/api';

export default function PresidentMessagePage() {
  const [leaders, setLeaders] = useState<CommitteeItem[]>([]);
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getCommittee().catch(() => []),
      api.getSettings().catch(() => ({})),
    ])
      .then(([committeeRows, siteSettings]) => {
        setLeaders(Array.isArray(committeeRows) ? committeeRows : []);
        setSettings(siteSettings || {});
      })
      .finally(() => setLoading(false));
  }, []);

  const president =
    leaders.find(
      (m) =>
        (m.designation_en || '').toLowerCase().includes('president') &&
        !(m.designation_en || '').toLowerCase().includes('vice')
    ) ||
    leaders.find((m) => (m.designation_bn || '').includes('সভাপতি') && !(m.designation_bn || '').includes('সহ')) ||
    leaders[0] ||
    null;

  const generalSecretary =
    leaders.find((m) => (m.designation_en || '').toLowerCase().includes('general secretary')) ||
    leaders.find((m) => (m.designation_bn || '').includes('সাধারণ সম্পাদক') && !(m.designation_bn || '').includes('যুগ্ম')) ||
    null;

  const orgNameBn =
    settings.org_name_bn || 'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)';

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
          <Link
            href="/leadership"
            className="inline-flex items-center gap-2 text-sm font-bold text-slate-600 hover:text-primary transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            কেন্দ্রীয় কার্যনির্বাহী পরিষদে ফিরে যান
          </Link>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-primary/10 text-primary border border-primary/20">
            সাংগঠনিক বার্তা • মেয়াদ ২০২৬–২০২৮
          </span>
        </div>

        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xl overflow-hidden">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-8 sm:p-12 text-white relative overflow-hidden">
            <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center gap-6">
              <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-emerald-500/20 border-2 border-emerald-400/40 flex items-center justify-center text-3xl font-extrabold text-emerald-300 shrink-0">
                {president?.photo_url ? (
                  <img
                    src={president.photo_url}
                    alt={president.name_bn}
                    className="w-full h-full object-cover rounded-2xl"
                  />
                ) : (
                  <span>{(president?.name_bn || 'ডি')[0]}</span>
                )}
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-widest text-emerald-300 block mb-1">
                  কেন্দ্রীয় কার্যনির্বাহী পরিষদ বিবৃতি
                </span>
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-2">
                  {president ? `${president.designation_bn}-এর বার্তা` : 'কেন্দ্রীয় কার্যনির্বাহী পরিষদের বার্তা'}
                </h1>
                <p className="text-slate-300 text-sm sm:text-base font-medium">
                  {president
                    ? `${president.name_bn}${president.name_en ? ` (${president.name_en})` : ''} — ${president.designation_bn}`
                    : orgNameBn}
                </p>
              </div>
            </div>
          </div>

          <div className="p-8 sm:p-12 space-y-6 text-slate-700 leading-relaxed text-base sm:text-lg">
            {loading ? (
              <div className="py-12 text-center text-slate-400 font-bold animate-pulse">
                সাংগঠনিক বার্তা লোড হচ্ছে...
              </div>
            ) : (
              <>
                <p className="font-semibold text-slate-900">
                  প্রিয় সহকর্মী ডিপ্লোমা প্রকৌশলীবৃন্দ,
                </p>

                {president?.message_bn ? (
                  <blockquote className="p-6 rounded-2xl bg-emerald-50/70 border-l-4 border-primary text-slate-800 font-medium">
                    “{president.message_bn}”
                  </blockquote>
                ) : null}

                <p>
                  পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি (পিজিসিবি)-তে কর্মরত ১,৪৫৭ জন ডিপ্লোমা প্রকৌশলীর পেশাগত মর্যাদা, ন্যায্য অধিকার, কারিগরি উৎকর্ষ এবং পারস্পরিক কল্যাণ নিশ্চিত করার লক্ষ্যে <strong>{orgNameBn}</strong> নিরলসভাবে কাজ করে যাচ্ছে। জাতীয় পাওয়ার গ্রিডের ৪০০ কেভি, ২৩০ কেভি ও ১৩২ কেভি সঞ্চালন লাইন এবং গ্রিড সাবস্টেশনসমূহ সার্বক্ষণিক সচল রাখতে আমাদের প্রকৌশলীরা দেশের প্রতিটি প্রান্তে নিষ্ঠার সাথে দায়িত্ব পালন করছেন।
                </p>

                <p>
                  সাংগঠনিক কার্যক্রমকে শতভাগ স্বচ্ছ, জবাবদিহিমূলক ও কাগজবিহীন করার অংশ হিসেবে এই সমন্বিত ডিজিটাল পোর্টাল চালু করা হয়েছে। এর মাধ্যমে ২০টি শাখা কমিটি ও গ্রিড সার্কেলের সদস্যদের ভেরিফিকেশনযোগ্য ডিজিটাল ডিরেক্টরি, কিউআর স্মার্ট আইডি কার্ড, অনলাইন সদস্যপদ আবেদন ও নবায়ন, অফিসিয়াল নোটিশ ও সার্কুলার আর্কাইভ এবং কারিগরি জার্নাল এক প্ল্যাটফর্মে যুক্ত হয়েছে।
                </p>

                <p>
                  আমরা বিশ্বাস করি—প্রযুক্তিগত দক্ষতা, ঐক্যবদ্ধ সাংগঠনিক শক্তি এবং পারস্পরিক সহযোগিতার মাধ্যমে পিজিসিবির ডিপ্লোমা প্রকৌশলীরা জাতীয় বিদ্যুৎ খাতে আরও গৌরবোজ্জ্বল ভূমিকা রাখবেন।
                </p>

                <div className="pt-8 mt-8 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/70">
                    <div className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                      {president?.designation_bn || 'সভাপতি'}
                    </div>
                    <div className="text-lg font-extrabold text-slate-900">
                      {president?.name_bn || 'কেন্দ্রীয় কার্যনির্বাহী পরিষদ'}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {orgNameBn} • মেয়াদ {president?.term_start || 2026}–{president?.term_end || 2028}
                    </div>
                  </div>

                  {generalSecretary && (
                    <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200/70">
                      <div className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                        {generalSecretary.designation_bn}
                      </div>
                      <div className="text-lg font-extrabold text-slate-900">
                        {generalSecretary.name_bn}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {orgNameBn} • মেয়াদ {generalSecretary.term_start || 2026}–{generalSecretary.term_end || 2028}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
