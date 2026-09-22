'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  FileText,
  Calendar,
  Users,
  MapPin,
  FileCheck,
  Download,
  Search,
  AlertTriangle,
  Award,
  ChevronRight
} from 'lucide-react';
import { api, PublicStats, Notice, CircularItem, CommitteeItem } from '../lib/api';
import { LoadingState } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';

function toBengaliNumber(num: number | string | undefined): string {
  if (num === undefined || num === null) return '০';
  return Number(num).toLocaleString('bn-BD');
}

export default function HomePage() {
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [circulars, setCirculars] = useState<CircularItem[]>([]);
  const [leader, setLeader] = useState<CommitteeItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    Promise.allSettled([
      api.getStats(),
      api.getNotices({ limit: 4 }),
      api.getCirculars({ limit: 4 }),
      api.getCommittee(),
    ]).then(([statsRes, noticesRes, circularsRes, committeeRes]) => {
      if (!isMounted) return;

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value);
      }
      if (noticesRes.status === 'fulfilled') {
        setNotices(noticesRes.value);
      }
      if (circularsRes.status === 'fulfilled') {
        setCirculars(circularsRes.value);
      }
      if (committeeRes.status === 'fulfilled' && committeeRes.value.length > 0) {
        // Pick leader with designation containing সভাপতি or the first member
        const president = committeeRes.value.find((m) => m.designation_bn.includes('সভাপতি')) || committeeRes.value[0];
        setLeader(president);
      }
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-primary text-white overflow-hidden py-16 md:py-24">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px]"></div>
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-accent opacity-20 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative max-w-7xl mx-auto px-6 flex flex-col items-start">
          <span className="inline-flex items-center gap-1.5 py-1 px-3.5 rounded-full bg-secondary/50 border border-secondary text-accent text-xs font-semibold tracking-wider mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            অফিসিয়াল ডিজিটাল পোর্টাল &middot; PGCB
          </span>
          <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold leading-tight mb-6 max-w-3xl">
            পাওয়ার গ্রিড প্রকৌশলী সমিতি, বাংলাদেশ
          </h1>
          <p className="text-base md:text-lg text-slate-200 mb-10 max-w-2xl leading-relaxed">
            জাতীয় বিদ্যুৎ গ্রিড সঞ্চালন খাতের প্রকৌশলীদের পেশাগত মানোন্নয়ন, সাংগঠনিক ঐক্য ও কল্যাণমূলক কর্মকাণ্ডের একমাত্র সার্বজনীন প্ল্যাটফর্ম।
          </p>

          <div className="flex flex-wrap gap-4">
            <Link
              href="/membership/apply"
              className="px-8 py-3.5 bg-success text-white font-medium rounded-lg hover:bg-emerald-600 transition-all shadow-lg shadow-success/20 flex items-center gap-2"
            >
              সদস্যপদের আবেদন <ArrowRight size={16} />
            </Link>
            <Link
              href="/verify"
              className="px-8 py-3.5 bg-white/10 border border-white/20 text-white font-medium rounded-lg hover:bg-white/20 transition-all"
            >
              সদস্য ভেরিফিকেশন
            </Link>
            <Link
              href="/membership/track"
              className="px-8 py-3.5 bg-transparent border border-white/30 text-slate-200 font-medium rounded-lg hover:bg-white/10 transition-all"
            >
              আবেদন ট্র্যাকিং
            </Link>
          </div>
        </div>
      </section>

      {/* Statistics Section (Dynamic Live Counters from Database) */}
      <section className="max-w-7xl mx-auto px-6 py-8 -mt-10 relative z-10 w-full">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-emerald-50 text-emerald-700">
              <Users size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? `${toBengaliNumber(stats.active_members)} জন` : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">নিবন্ধিত সক্রিয় সদস্য</p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-blue-50 text-blue-700">
              <MapPin size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? `${toBengaliNumber(stats.active_circles)} টি` : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">গ্রিড সার্কেল ইউনিট</p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-amber-50 text-amber-700">
              <FileText size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? `${toBengaliNumber(stats.publications || stats.documents_count || 0)} টি` : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">প্রকাশনা ও ডকুমেন্টস</p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-purple-50 text-purple-700">
              <Calendar size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? `${toBengaliNumber(stats.upcoming_events)} টি` : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">আসন্ন প্রাতিষ্ঠানিক ইভেন্ট</p>
            </div>
          </div>
        </div>
      </section>

      {/* Quick Services Strip */}
      <section className="max-w-7xl mx-auto px-6 py-6 w-full">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link
            href="/membership/apply"
            className="p-4 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm transition-all flex items-center gap-3 text-slate-800"
          >
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded">
              <FileCheck size={20} />
            </div>
            <div>
              <div className="text-sm font-semibold">সদস্য আবেদন</div>
              <div className="text-xs text-slate-500">অনলাইনে আবেদন জমা দিন</div>
            </div>
          </Link>

          <Link
            href="/documents"
            className="p-4 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm transition-all flex items-center gap-3 text-slate-800"
          >
            <div className="p-2 bg-blue-50 text-blue-600 rounded">
              <Download size={20} />
            </div>
            <div>
              <div className="text-sm font-semibold">ফরম ও প্রকাশনা</div>
              <div className="text-xs text-slate-500">ডাউনলোড করুন</div>
            </div>
          </Link>

          <Link
            href="/members"
            className="p-4 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm transition-all flex items-center gap-3 text-slate-800"
          >
            <div className="p-2 bg-amber-50 text-amber-600 rounded">
              <Search size={20} />
            </div>
            <div>
              <div className="text-sm font-semibold">সদস্য ডিরেক্টরি</div>
              <div className="text-xs text-slate-500">প্রকৌশলীদের তালিকা</div>
            </div>
          </Link>

          <Link
            href="/portal"
            className="p-4 rounded-lg border border-slate-200 bg-white hover:border-emerald-500 hover:shadow-sm transition-all flex items-center gap-3 text-slate-800"
          >
            <div className="p-2 bg-purple-50 text-purple-600 rounded">
              <Award size={20} />
            </div>
            <div>
              <div className="text-sm font-semibold">ডিজিটাল কার্ড</div>
              <div className="text-xs text-slate-500">প্রোফাইল ও কার্ড প্রিন্ট</div>
            </div>
          </Link>
        </div>
      </section>

      {/* Main Content Area: Notices + Sidebar */}
      <section className="bg-slate-50 py-12 flex-1">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recent Notices (Spans 2 columns) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center border-b-2 border-primary pb-3">
              <h2 className="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-2">
                <span>📌</span> সাম্প্রতিক নোটিশ ও সার্কুলার
              </h2>
              <div className="flex items-center gap-4">
                <Link href="/notices" className="text-xs md:text-sm font-medium text-emerald-700 hover:underline flex items-center gap-1">
                  সকল নোটিশ <ChevronRight size={14} />
                </Link>
                <Link href="/circulars" className="text-xs md:text-sm font-medium text-slate-600 hover:underline flex items-center gap-1">
                  সার্কুলার <ChevronRight size={14} />
                </Link>
              </div>
            </div>

            {loading ? (
              <LoadingState message="নোটিশ লোড হচ্ছে..." />
            ) : notices.length === 0 && circulars.length === 0 ? (
              <EmptyState
                icon="📄"
                title="কোনো নোটিশ পাওয়া যায়নি"
                description="বর্তমানে কোনো নতুন নোটিশ প্রকাশিত হয়নি।"
              />
            ) : (
              <div className="space-y-3">
                {notices.map((notice) => (
                  <div
                    key={notice.id}
                    className="bg-white p-4 rounded-lg border border-slate-200 hover:border-emerald-500 transition-all flex gap-4 items-start shadow-sm"
                  >
                    <div className="flex flex-col items-center justify-center min-w-[64px] bg-slate-100 rounded p-2 text-slate-700 border border-slate-200">
                      <span className="text-lg font-bold leading-none">
                        {notice.published_at ? new Date(notice.published_at).getDate() : '—'}
                      </span>
                      <span className="text-[11px] font-medium mt-1">
                        {notice.published_at
                          ? new Date(notice.published_at).toLocaleDateString('bn-BD', { month: 'short' })
                          : 'তারিখ'}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {notice.priority === 'URGENT' && (
                          <span className="bg-red-100 text-red-700 text-[11px] font-bold px-2 py-0.5 rounded">
                            জরুরী
                          </span>
                        )}
                        <span className="bg-emerald-50 text-emerald-700 text-[11px] font-medium px-2 py-0.5 rounded">
                          {notice.category}
                        </span>
                      </div>
                      <Link
                        href={`/notices/${notice.id}`}
                        className="text-slate-900 font-semibold hover:text-emerald-700 transition-colors line-clamp-2 text-sm md:text-base"
                      >
                        {notice.title_bn}
                      </Link>
                    </div>
                  </div>
                ))}

                {circulars.slice(0, 2).map((circ) => (
                  <div
                    key={`circ-${circ.id}`}
                    className="bg-white p-4 rounded-lg border border-slate-200 hover:border-blue-500 transition-all flex gap-4 items-start shadow-sm"
                  >
                    <div className="flex flex-col items-center justify-center min-w-[64px] bg-blue-50 rounded p-2 text-blue-700 border border-blue-100">
                      <span className="text-lg font-bold leading-none">
                        {circ.published_at ? new Date(circ.published_at).getDate() : '—'}
                      </span>
                      <span className="text-[11px] font-medium mt-1">
                        {circ.published_at
                          ? new Date(circ.published_at).toLocaleDateString('bn-BD', { month: 'short' })
                          : 'সার্কুলার'}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="bg-blue-100 text-blue-700 text-[11px] font-medium px-2 py-0.5 rounded">
                          অফিসিয়াল সার্কুলার
                        </span>
                        {circ.reference_no && (
                          <span className="text-xs text-slate-500">স্মারক: {circ.reference_no}</span>
                        )}
                      </div>
                      <Link
                        href={`/circulars/${circ.id}`}
                        className="text-slate-900 font-semibold hover:text-blue-700 transition-colors line-clamp-2 text-sm md:text-base"
                      >
                        {circ.title_bn}
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar / Leadership Message & Key Resources */}
          <div className="space-y-6">
            <div className="border-b-2 border-primary pb-3">
              <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>💬</span> সভাপতির বার্তা
              </h2>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-slate-100 rounded-full mb-4 overflow-hidden border-2 border-emerald-600 flex items-center justify-center text-3xl">
                {leader?.photo_url ? (
                  <img src={leader.photo_url} alt={leader.name_bn} className="w-full h-full object-cover" />
                ) : (
                  '👤'
                )}
              </div>
              <h3 className="font-bold text-base md:text-lg text-slate-900">
                {leader?.name_bn || 'প্রকৌশলী নেতৃত্ব'}
              </h3>
              <p className="text-xs font-medium text-emerald-700 mb-3">
                {leader?.designation_bn || 'পাওয়ার গ্রিড প্রকৌশলী সমিতি'}
              </p>
              <p className="text-xs md:text-sm text-slate-600 line-clamp-5 italic mb-4 leading-relaxed">
                {leader?.message_bn ||
                  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর সম্মানিত প্রকৌশলী ও সদস্যদের ঐক্যবদ্ধ প্রচেষ্টায় জাতীয় বিদ্যুৎ সঞ্চালন ব্যবস্থার নিরবচ্ছিন্ন উন্নয়ন নিশ্চিত করতে আমরা অঙ্গীকারবদ্ধ।'}
              </p>
              <Link
                href="/leadership"
                className="text-xs font-semibold text-emerald-700 hover:underline flex items-center gap-1"
              >
                সম্পূর্ণ কার্যনির্বাহী কমিটি দেখুন <ArrowRight size={12} />
              </Link>
            </div>

            {/* Helpline Box */}
            <div className="bg-emerald-800 text-white p-5 rounded-xl shadow-sm">
              <h4 className="font-bold text-base mb-1">প্রকৌশলী সহায়তা ও তথ্যকেন্দ্র</h4>
              <p className="text-xs text-emerald-100 mb-4">
                সদস্যপদ, পরিচয়পত্র বা যেকোনো তথ্যের জন্য সরাসরি যোগাযোগ করুন।
              </p>
              <div className="space-y-2 text-xs font-medium">
                <div>📞 হেল্পলাইন: +৮৮০ ২ ৯৫৫৩৬৬৩</div>
                <div>✉️ ইমেইল: info@pgcb.gov.bd</div>
                <div>📍 প্রধান কার্যালয়: পিজিসিবি ভবন, আফতাবনগর, ঢাকা</div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
