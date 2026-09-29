'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function CircleDetailPage({ params }: { params: { slug: string } }) {
  const slug = decodeURIComponent(params.slug);
  const [detail, setDetail] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .getCircleDetail(slug)
      .then((res) => setDetail(res))
      .catch((err) => setError(err?.message || 'গ্রিড সার্কেল খুঁজে পাওয়া যায়নি।'))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="bg-slate-50 min-h-screen py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="h-48 rounded-3xl bg-white border border-slate-200 animate-pulse" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="h-80 rounded-2xl bg-white border border-slate-200 animate-pulse lg:col-span-2" />
            <div className="h-80 rounded-2xl bg-white border border-slate-200 animate-pulse" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="bg-slate-50 min-h-screen py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-xl mx-auto bg-white rounded-3xl border border-slate-200 p-10 text-center shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-4 font-extrabold text-xl">
            !
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 mb-2">সার্কেল বা শাখা কমিটি পাওয়া যায়নি</h1>
          <p className="text-sm text-slate-600 mb-6">
            অনুরোধকৃত সার্কেল ({slug}) সিস্টেমে খুঁজে পাওয়া যায়নি অথবা বর্তমানে নিষ্ক্রিয় রয়েছে।
          </p>
          <Link
            href="/circles"
            className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-primary text-white text-sm font-bold hover:bg-emerald-800 transition-colors"
          >
            সকল সার্কেল তালিকায় ফিরে যান
          </Link>
        </div>
      </div>
    );
  }

  const members: any[] = Array.isArray(detail.members) ? detail.members : [];
  const committee: any[] = Array.isArray(detail.committee) ? detail.committee : [];
  const notices: any[] = Array.isArray(detail.notices) ? detail.notices : [];
  const stats = detail.statistics || {};

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <Link
            href="/circles"
            className="inline-flex items-center gap-2 text-sm font-bold text-slate-600 hover:text-primary transition-colors"
          >
            ← সকল গ্রিড সার্কেল ও শাখা কমিটি
          </Link>
        </div>

        {/* Hero */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-10">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
            <div>
              <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
                {detail.name_en || `Circle #${detail.id}`}
              </span>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
                {detail.name_bn}
              </h1>
              <p className="text-slate-300 text-base max-w-2xl leading-relaxed">
                {detail.description_bn ||
                  `পিজিসিবি ${detail.name_bn} আঞ্চলিক কার্যালয় এবং আওতাধীন জিএমডি ও গ্রিড সাবস্টেশনসমূহে কর্মরত ডিপ্লোমা প্রকৌশলীদের সাংগঠনিক ইউনিট।`}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-4 shrink-0">
              <div className="bg-white/10 border border-white/15 rounded-2xl p-4 text-center">
                <div className="text-2xl sm:text-3xl font-extrabold text-emerald-400">
                  {(stats.active_members ?? members.length).toLocaleString('bn-BD')}
                </div>
                <div className="text-xs font-bold text-slate-300 mt-1">সক্রিয় সদস্য</div>
              </div>
              <div className="bg-white/10 border border-white/15 rounded-2xl p-4 text-center">
                <div className="text-2xl sm:text-3xl font-extrabold text-amber-300">
                  {(stats.committee_size ?? committee.length).toLocaleString('bn-BD')}
                </div>
                <div className="text-xs font-bold text-slate-300 mt-1">কমিটি সদস্য</div>
              </div>
              <div className="bg-white/10 border border-white/15 rounded-2xl p-4 text-center">
                <div className="text-2xl sm:text-3xl font-extrabold text-sky-300">
                  {(stats.pending_members ?? 0).toLocaleString('bn-BD')}
                </div>
                <div className="text-xs font-bold text-slate-300 mt-1">প্রক্রিয়াধীন আবেদন</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left 2 Columns: Circle Members & Committee */}
          <div className="lg:col-span-2 space-y-8">
            {/* Circle Committee Section */}
            <section className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
              <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
                <div>
                  <h2 className="text-xl font-extrabold text-slate-900">শাখা কার্যনির্বাহী কমিটি</h2>
                  <p className="text-sm text-slate-500">সার্কেল/শাখা কমিটির অনুমোদিত দায়িত্বশীলদের তালিকা</p>
                </div>
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-slate-100 text-slate-700">
                  মেয়াদ ২০২৬–২০২৮
                </span>
              </div>

              {committee.length === 0 ? (
                <div className="p-6 rounded-xl bg-slate-50 border border-slate-200/60 text-sm text-slate-600">
                  এই শাখা কমিটির দায়িত্বশীলদের নামের তালিকা কেন্দ্রীয় অ্যাডমিন প্যানেল থেকে হালনাগাদ প্রক্রিয়াধীন রয়েছে। নিচে এই শাখার তালিকাভুক্ত প্রকৌশলীদের ডিরেক্টরি প্রদর্শিত হচ্ছে।
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {committee.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 flex items-center gap-4"
                    >
                      <div className="w-12 h-12 rounded-xl bg-primary/10 text-primary font-extrabold flex items-center justify-center shrink-0">
                        {(c.name_bn || 'প্র')[0]}
                      </div>
                      <div>
                        <div className="font-extrabold text-slate-900">{c.name_bn}</div>
                        <div className="text-xs font-bold text-primary">{c.designation_bn}</div>
                        {c.name_en && <div className="text-xs text-slate-500">{c.name_en}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Circle Active Members Preview */}
            <section className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
              <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
                <div>
                  <h2 className="text-xl font-extrabold text-slate-900">
                    তালিকাভুক্ত প্রকৌশলী সদস্যবৃন্দ ({(stats.active_members ?? members.length).toLocaleString('bn-BD')} জন)
                  </h2>
                  <p className="text-sm text-slate-500">
                    অফিসিয়াল ডিপ্রকৌস ভোটার ও সদস্য তালিকা (২০২৬–২০২৮) অনুযায়ী নিবন্ধিত প্রকৌশলী
                  </p>
                </div>
                <Link
                  href={`/members?circle_id=${detail.id}`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-50 text-primary text-xs font-extrabold hover:bg-emerald-100 transition-colors"
                >
                  সকল সদস্য দেখুন →
                </Link>
              </div>

              {members.length === 0 ? (
                <div className="p-8 rounded-xl bg-slate-50 text-center text-sm text-slate-500">
                  এই সার্কেলে এখনো কোনো সক্রিয় সদস্য তালিকাভুক্ত নেই।
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {members.map((m) => (
                    <div
                      key={m.membership_id}
                      className="p-4 rounded-xl border border-slate-200/80 hover:border-primary/40 transition-all flex items-start justify-between gap-3"
                    >
                      <div>
                        <div className="font-bold text-slate-900 text-sm">{m.name_bn}</div>
                        {m.name_en && <div className="text-xs text-slate-500">{m.name_en}</div>}
                        <div className="text-xs font-semibold text-slate-600 mt-1">
                          {m.designation_bn || 'উপ-সহকারী প্রকৌশলী'}
                          {m.office_name_bn ? ` • ${m.office_name_bn}` : ''}
                        </div>
                        <div className="mt-2 flex items-center gap-2 flex-wrap">
                          <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                            {m.membership_id}
                          </span>
                          {m.employee_id && (
                            <span className="text-[11px] font-mono text-slate-500">
                              EMP #{m.employee_id}
                            </span>
                          )}
                        </div>
                      </div>
                      <Link
                        href={`/verify/${encodeURIComponent(m.membership_id)}`}
                        className="text-xs font-bold text-primary hover:underline shrink-0"
                      >
                        যাচাই
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>

          {/* Right Sidebar: Office Info & Recent Notices */}
          <div className="space-y-6">
            <section className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
              <h3 className="text-lg font-extrabold text-slate-900 mb-4">আঞ্চলিক যোগাযোগ ও দপ্তর</h3>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">দপ্তর</dt>
                  <dd className="font-semibold text-slate-800 mt-0.5">
                    {detail.contact?.office_bn || `পিজিসিবি ${detail.name_bn} আঞ্চলিক কার্যালয়`}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">ইমেইল</dt>
                  <dd className="font-mono text-slate-700 mt-0.5">
                    {detail.contact?.email || 'info@pgcb.org.bd'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">ফোন</dt>
                  <dd className="font-mono text-slate-700 mt-0.5">
                    {detail.contact?.phone || '+880-2-55046731'}
                  </dd>
                </div>
              </dl>

              <div className="mt-6 pt-6 border-t border-slate-100 flex flex-col gap-2.5">
                <Link
                  href="/apply"
                  className="w-full py-2.5 px-4 rounded-xl bg-primary text-white text-center text-xs font-extrabold hover:bg-emerald-800 transition-colors"
                >
                  এই সার্কেলে সদস্যপদ আবেদন করুন
                </Link>
                <Link
                  href={`/members?circle_id=${detail.id}`}
                  className="w-full py-2.5 px-4 rounded-xl bg-slate-100 text-slate-800 text-center text-xs font-extrabold hover:bg-slate-200 transition-colors"
                >
                  সার্কেলের সকল সদস্য খুঁজুন
                </Link>
              </div>
            </section>

            <section className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm">
              <h3 className="text-lg font-extrabold text-slate-900 mb-4">সাম্প্রতিক নোটিশ</h3>
              {notices.length === 0 ? (
                <p className="text-sm text-slate-500">কোনো সাম্প্রতিক নোটিশ নেই।</p>
              ) : (
                <ul className="space-y-3">
                  {notices.map((n) => (
                    <li key={n.id} className="pb-3 border-b border-slate-100 last:border-none last:pb-0">
                      <Link
                        href={`/notices/${n.id}`}
                        className="text-sm font-bold text-slate-800 hover:text-primary transition-colors block"
                      >
                        {n.title_bn}
                      </Link>
                      {n.published_at && (
                        <span className="text-xs text-slate-400 mt-1 block">
                          {new Date(n.published_at).toLocaleDateString('bn-BD')}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
