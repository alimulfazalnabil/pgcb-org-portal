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
  Award,
  ChevronRight,
  BookOpen,
  Image as ImageIcon,
  PlayCircle
} from 'lucide-react';
import { api, PublicStats, Notice, CircularItem, CommitteeItem } from '../lib/api';
import { LoadingState } from '../components/ui/LoadingState';
import { EmptyState } from '../components/ui/EmptyState';
import { useLanguage } from '../lib/i18n';

export default function HomePage() {
  const { language, t, pick, formatNumber, formatDate } = useLanguage();
  const [stats, setStats] = useState<PublicStats | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [circulars, setCirculars] = useState<CircularItem[]>([]);
  const [leader, setLeader] = useState<CommitteeItem | null>(null);
  const [circles, setCircles] = useState<any[]>([]);
  const [publications, setPublications] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [media, setMedia] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    Promise.allSettled([
      api.getStats(),
      api.getNotices({ limit: 4 }),
      api.getCirculars({ limit: 4 }),
      api.getCommittee(),
      api.getCircles(),
      api.getJournals(),
      api.getEvents(true),
      api.getMedia(),
    ]).then(([statsRes, noticesRes, circularsRes, committeeRes, circlesRes, publicationsRes, eventsRes, mediaRes]) => {
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
        const president = committeeRes.value.find((m) => m.designation_bn?.includes('সভাপতি')) || committeeRes.value[0];
        setLeader(president);
      }
      if (circlesRes.status === 'fulfilled') setCircles(Array.isArray(circlesRes.value) ? circlesRes.value.slice(0, 3) : []);
      if (publicationsRes.status === 'fulfilled') setPublications(Array.isArray(publicationsRes.value) ? publicationsRes.value.slice(0, 3) : []);
      if (eventsRes.status === 'fulfilled') setEvents(Array.isArray(eventsRes.value) ? eventsRes.value.slice(0, 3) : []);
      if (mediaRes.status === 'fulfilled') setMedia(Array.isArray(mediaRes.value) ? mediaRes.value.slice(0, 4) : []);
      setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-primary text-white overflow-hidden py-12 md:py-16">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:16px_16px]"></div>
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-accent opacity-20 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-8 lg:gap-12 items-center">\n          <div className="flex flex-col items-start">
          <span className="inline-flex items-center gap-1.5 py-1 px-3.5 rounded-full bg-secondary/50 border border-secondary text-accent text-xs font-semibold tracking-wider mb-5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            {t('অফিসিয়াল ডিজিটাল পোর্টাল · PGCB', 'Official Digital Portal · PGCB')}
          </span>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold leading-snug mb-4 max-w-3xl">
            {t('পাওয়ার গ্রিড প্রকৌশলী সমিতি, বাংলাদেশ', 'Power Grid Engineers Association, Bangladesh')}
          </h1>
          <p className="text-sm sm:text-base md:text-lg text-slate-200 mb-8 max-w-2xl leading-relaxed">
            {t(
              'জাতীয় বিদ্যুৎ গ্রিড সঞ্চালন খাতের প্রকৌশলীদের পেশাগত মানোন্নয়ন, সাংগঠনিক ঐক্য ও কল্যাণমূলক কর্মকাণ্ডের একমাত্র সার্বজনীন প্ল্যাটফর্ম।',
              'The official institutional platform for professional excellence, organizational unity, and welfare of engineers across the national power grid of Bangladesh.'
            )}
          </p>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/membership/apply"
              className="px-6 py-3 bg-success text-white text-sm font-medium rounded-lg hover:bg-emerald-600 transition-all shadow-lg shadow-success/20 flex items-center gap-2"
            >
              {t('সদস্যপদের আবেদন', 'Apply for Membership')} <ArrowRight size={16} />
            </Link>
            <Link
              href="/verify"
              className="px-6 py-3 bg-white/10 border border-white/20 text-white text-sm font-medium rounded-lg hover:bg-white/20 transition-all"
            >
              {t('সদস্য ভেরিফিকেশন', 'Member Verification')}
            </Link>
            <Link
              href="/membership/track"
              className="px-6 py-3 bg-transparent border border-white/30 text-slate-200 text-sm font-medium rounded-lg hover:bg-white/10 transition-all"
            >
              {t('আবেদন ট্র্যাকিং', 'Track Application')}
            </Link>
          </div>
          <aside aria-label={t('সাম্প্রতিক নোটিশ', 'Latest notices')} className="w-full rounded-2xl border border-white/15 bg-slate-950/35 p-5 sm:p-6 shadow-2xl backdrop-blur-sm">
            <div className="flex items-center justify-between gap-3 border-b border-white/15 pb-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-emerald-300">{t('আপডেট', 'Stay informed')}</p>
                <h2 className="mt-1 text-lg font-extrabold text-white">{t('সাম্প্রতিক নোটিশ', 'Latest notices')}</h2>
              </div>
              <Link href="/notices" className="inline-flex items-center gap-1 text-xs font-bold text-emerald-200 hover:text-white">{t('সব দেখুন', 'View all')} <ArrowRight size={14}/></Link>
            </div>
            <div className="mt-3 divide-y divide-white/10">
              {loading ? <p className="py-5 text-sm text-slate-300">{t('নোটিশ লোড হচ্ছে…', 'Loading notices…')}</p> :
                notices.length ? notices.slice(0, 3).map((notice) => <Link key={notice.id} href={`/notices/${notice.id}`} className="block rounded-lg px-2 py-3 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300">
                  <div className="mb-1 flex items-center gap-2">
                    {notice.priority === 'URGENT' && <span className="rounded bg-red-500/20 px-2 py-0.5 text-[10px] font-extrabold text-red-200">{t('জরুরি', 'URGENT')}</span>}
                    <span className="text-[10px] font-semibold uppercase tracking-wide text-emerald-200">{notice.category}</span>
                  </div>
                  <p className="line-clamp-2 text-sm font-semibold leading-relaxed text-white">{pick(notice, 'title', notice.title_bn)}</p>
                  <p className="mt-1 text-[11px] text-slate-400">{notice.published_at ? formatDate(notice.published_at) : t('তারিখ নেই', 'Date unavailable')}</p>
                </Link>) :
                <p className="py-5 text-sm text-slate-300">{t('বর্তমানে কোনো প্রকাশিত নোটিশ নেই।', 'No published notices are available right now.')}</p>}
            </div>
            <Link href="/circulars" className="mt-3 inline-flex items-center gap-2 text-xs font-bold text-emerald-200 hover:text-white">{t('সার্কুলার দেখুন', 'Browse circulars')} <ArrowRight size={14}/></Link>
          </aside>
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
                {stats ? (language === 'en' ? `${formatNumber(stats.active_members)}` : `${formatNumber(stats.active_members)} জন`) : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">
                {t('নিবন্ধিত সক্রিয় সদস্য', 'Active Registered Members')}
              </p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-blue-50 text-blue-700">
              <MapPin size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? (language === 'en' ? `${formatNumber(stats.active_circles)}` : `${formatNumber(stats.active_circles)} টি`) : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">
                {t('গ্রিড সার্কেল ইউনিট', 'Grid Circle Units')}
              </p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-amber-50 text-amber-700">
              <FileText size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? (language === 'en' ? `${formatNumber(stats.publications || stats.documents_count || 0)}` : `${formatNumber(stats.publications || stats.documents_count || 0)} টি`) : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">
                {t('প্রকাশনা ও ডকুমেন্টস', 'Publications & Documents')}
              </p>
            </div>
          </div>

          <div className="glass-panel p-5 rounded-xl flex items-center gap-4 bg-white shadow-md border border-slate-100">
            <div className="p-3.5 rounded-lg bg-purple-50 text-purple-700">
              <Calendar size={24} />
            </div>
            <div>
              <p className="text-2xl md:text-3xl font-bold text-slate-800">
                {stats ? (language === 'en' ? `${formatNumber(stats.upcoming_events)}` : `${formatNumber(stats.upcoming_events)} টি`) : '—'}
              </p>
              <p className="text-xs md:text-sm font-medium text-slate-500">
                {t('আসন্ন প্রাতিষ্ঠানিক ইভেন্ট', 'Upcoming Institutional Events')}
              </p>
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
              <div className="text-sm font-semibold">{t('সদস্য আবেদন', 'Apply for Membership')}</div>
              <div className="text-xs text-slate-500">{t('অনলাইনে আবেদন জমা দিন', 'Submit online application')}</div>
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
              <div className="text-sm font-semibold">{t('ফরম ও প্রকাশনা', 'Forms & Publications')}</div>
              <div className="text-xs text-slate-500">{t('ডাউনলোড করুন', 'Download forms & reports')}</div>
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
              <div className="text-sm font-semibold">{t('সদস্য ডিরেক্টরি', 'Member Directory')}</div>
              <div className="text-xs text-slate-500">{t('প্রকৌশলীদের তালিকা', 'Directory of engineers')}</div>
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
              <div className="text-sm font-semibold">{t('ডিজিটাল কার্ড', 'Digital ID Card')}</div>
              <div className="text-xs text-slate-500">{t('প্রোফাইল ও কার্ড প্রিন্ট', 'Profile & smart ID print')}</div>
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
                <span>📌</span> {t('সাম্প্রতিক নোটিশ ও সার্কুলার', 'Recent Notices & Circulars')}
              </h2>
              <div className="flex items-center gap-4">
                <Link href="/notices" className="text-xs md:text-sm font-medium text-emerald-700 hover:underline flex items-center gap-1">
                  {t('সকল নোটিশ', 'All Notices')} <ChevronRight size={14} />
                </Link>
                <Link href="/circulars" className="text-xs md:text-sm font-medium text-slate-600 hover:underline flex items-center gap-1">
                  {t('সার্কুলার', 'Circulars')} <ChevronRight size={14} />
                </Link>
              </div>
            </div>

            {loading ? (
              <LoadingState message={t('নোটিশ লোড হচ্ছে...', 'Loading notices...')} />
            ) : notices.length === 0 && circulars.length === 0 ? (
              <EmptyState
                icon="📄"
                title={t('কোনো নোটিশ পাওয়া যায়নি', 'No notices found')}
                description={t('বর্তমানে কোনো নতুন নোটিশ প্রকাশিত হয়নি।', 'No new notices have been published at this time.')}
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
                          ? formatDate(notice.published_at, { month: 'short' })
                          : t('তারিখ', 'Date')}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {notice.priority === 'URGENT' && (
                          <span className="bg-red-100 text-red-700 text-[11px] font-bold px-2 py-0.5 rounded">
                            {t('জরুরী', 'URGENT')}
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
                        {pick(notice, 'title', notice.title_bn)}
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
                          ? formatDate(circ.published_at, { month: 'short' })
                          : t('সার্কুলার', 'Circular')}
                      </span>
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="bg-blue-100 text-blue-700 text-[11px] font-medium px-2 py-0.5 rounded">
                          {t('অফিসিয়াল সার্কুলার', 'Official Circular')}
                        </span>
                        {circ.reference_no && (
                          <span className="text-xs text-slate-500">
                            {t('স্মারক:', 'Ref:')} {circ.reference_no}
                          </span>
                        )}
                      </div>
                      <Link
                        href={`/circulars/${circ.id}`}
                        className="text-slate-900 font-semibold hover:text-blue-700 transition-colors line-clamp-2 text-sm md:text-base"
                      >
                        {pick(circ, 'title', circ.title_bn)}
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
                <span>💬</span> {t('সভাপতির বার্তা', "President's Message")}
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
                {pick(leader, 'name', t('প্রকৌশলী নেতৃত্ব', 'Engineering Leadership'))}
              </h3>
              <p className="text-xs font-medium text-emerald-700 mb-3">
                {pick(leader, 'designation', t('পাওয়ার গ্রিড প্রকৌশলী সমিতি', 'Power Grid Engineers Association'))}
              </p>
              <p className="text-xs md:text-sm text-slate-600 line-clamp-5 italic mb-4 leading-relaxed">
                {pick(
                  leader,
                  'message',
                  t(
                    'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর সম্মানিত প্রকৌশলী ও সদস্যদের ঐক্যবদ্ধ প্রচেষ্টায় জাতীয় বিদ্যুৎ সঞ্চালন ব্যবস্থার নিরবচ্ছিন্ন উন্নয়ন নিশ্চিত করতে আমরা অঙ্গীকারবদ্ধ।',
                    'We are committed to ensuring the continuous modernization and reliability of the national power transmission grid through the united leadership of PGCB engineers.'
                  )
                )}
              </p>
              <Link
                href="/leadership"
                className="text-xs font-semibold text-emerald-700 hover:underline flex items-center gap-1"
              >
                {t('সম্পূর্ণ কার্যনির্বাহী কমিটি দেখুন', 'View Full Executive Committee')} <ArrowRight size={12} />
              </Link>
            </div>

            {/* Helpline Box */}
            <div className="bg-emerald-800 text-white p-5 rounded-xl shadow-sm">
              <h4 className="font-bold text-base mb-1">
                {t('প্রকৌশলী সহায়তা ও তথ্যকেন্দ্র', 'Engineer Helpdesk & Information Center')}
              </h4>
              <p className="text-xs text-emerald-100 mb-4">
                {t(
                  'সদস্যপদ, পরিচয়পত্র বা যেকোনো তথ্যের জন্য সরাসরি যোগাযোগ করুন।',
                  'Contact our secretariat directly for membership, digital ID cards, or official inquiries.'
                )}
              </p>
              <div className="space-y-2 text-xs font-medium">
                <div>{t('📞 হেল্পলাইন: +৮৮০ ২ ৯৫৫৩৬৬৩', '📞 Helpline: +880 2 9553663')}</div>
                <div>{t('✉️ ইমেইল: info@powergriddiprocoush.org', '✉️ Email: info@powergriddiprocoush.org')}</div>
                <div>{t('📍 প্রধান কার্যালয়: পিজিসিবি ভবন, আফতাবনগর, ঢাকা', '📍 Head Office: PGCB Bhaban, Aftabnagar, Dhaka')}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Featured public content: Grid Circles, publications, events and media */}
      <section className="bg-white py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-6 space-y-14">
          <section aria-labelledby="home-circles-heading">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700 mb-2">{t('আঞ্চলিক নেটওয়ার্ক', 'Regional network')}</p>
                <h2 id="home-circles-heading" className="text-2xl md:text-3xl font-extrabold text-slate-900">{t('গ্রিড সার্কেলসমূহ', 'Grid Circles')}</h2>
                <p className="text-sm text-slate-600 mt-2 max-w-2xl">{t('সারা দেশের শাখা ও আঞ্চলিক প্রকৌশলী ইউনিটগুলো দেখুন।', 'Explore the regional engineering units and branch circles across the country.')}</p>
              </div>
              <Link href="/circles" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700 hover:text-emerald-900">{t('সব সার্কেল দেখুন', 'View all circles')} <ArrowRight size={16} /></Link>
            </div>
            {loading ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[1,2,3].map(n => <div key={n} className="h-40 rounded-2xl bg-slate-100 animate-pulse" />)}</div> :
              circles.length ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{circles.map((circle) => <article key={circle.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-6 hover:border-emerald-300 hover:shadow-md transition-all"><div className="w-11 h-11 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center mb-4"><MapPin size={21}/></div><h3 className="font-extrabold text-slate-900 text-lg">{pick(circle, 'name', circle.name_bn || circle.name_en || t('গ্রিড সার্কেল', 'Grid Circle'))}</h3><p className="text-sm text-slate-600 mt-2 line-clamp-2">{pick(circle, 'description', circle.description_bn || circle.description_en || '')}</p><p className="text-xs font-semibold text-slate-500 mt-4">{formatNumber(Number(circle.active_members) || 0)} {t('সদস্য', 'members')}</p><Link href={`/circles/${encodeURIComponent(circle.slug || String(circle.id))}`} className="mt-4 inline-flex items-center gap-1 text-sm font-bold text-emerald-700">{t('বিস্তারিত', 'Explore circle')} <ArrowRight size={14}/></Link></article>)}</div> :
              <EmptyState icon="📍" title={t('সার্কেল তথ্য পাওয়া যায়নি', 'No circle data available')} description={t('তথ্য যুক্ত হলে এখানে দেখানো হবে।', 'Circle information will appear here when available.')} />}
          </section>

          <section aria-labelledby="home-publications-heading">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-6"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700 mb-2">{t('জ্ঞান ও গবেষণা', 'Knowledge and research')}</p><h2 id="home-publications-heading" className="text-2xl md:text-3xl font-extrabold text-slate-900">{t('প্রকাশনা ও জার্নাল', 'Publications & Journals')}</h2></div><Link href="/journal" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700">{t('সব প্রকাশনা', 'All publications')} <ArrowRight size={16}/></Link></div>
            {loading ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[1,2,3].map(n=><div key={n} className="h-44 rounded-2xl bg-slate-100 animate-pulse"/>)}</div> :
              publications.length ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{publications.map((item:any)=><article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"><div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-4"><BookOpen size={20}/></div><p className="text-xs font-bold uppercase tracking-wider text-amber-700 mb-2">{item.category || item.edition || t('প্রকাশনা', 'Publication')}</p><h3 className="font-extrabold text-slate-900 leading-snug">{pick(item, 'title', item.title_bn || item.title_en || t('শিরোনাম পাওয়া যায়নি', 'Untitled publication'))}</h3><p className="text-sm text-slate-600 mt-2 line-clamp-3">{pick(item, 'summary', item.abstract_bn || item.summary_bn || item.description_bn || '')}</p><Link href={`/journal/${item.id}`} className="mt-4 inline-flex items-center gap-1 text-sm font-bold text-emerald-700">{t('পড়ুন', 'Read publication')} <ArrowRight size={14}/></Link></article>)}</div> :
              <EmptyState icon="📚" title={t('কোনো প্রকাশনা পাওয়া যায়নি', 'No publications available')} description={t('নতুন জার্নাল প্রকাশিত হলে এখানে দেখানো হবে।', 'New publications will appear here when published.')} />}
          </section>

          <section aria-labelledby="home-events-heading">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-6"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700 mb-2">{t('সাম্প্রতিক কার্যক্রম', 'What’s happening')}</p><h2 id="home-events-heading" className="text-2xl md:text-3xl font-extrabold text-slate-900">{t('ইভেন্ট ও কার্যক্রম', 'Events & Activities')}</h2></div><Link href="/events" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700">{t('সব ইভেন্ট', 'All events')} <ArrowRight size={16}/></Link></div>
            {loading ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{[1,2,3].map(n=><div key={n} className="h-44 rounded-2xl bg-slate-100 animate-pulse"/>)}</div> :
              events.length ? <div className="grid grid-cols-1 md:grid-cols-3 gap-4">{events.map((ev:any)=><article key={ev.id} className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"><div className="h-36 bg-slate-100 overflow-hidden">{ev.cover_image_url ? <img src={ev.cover_image_url} alt="" className="w-full h-full object-cover" loading="lazy"/> : <div className="h-full flex items-center justify-center text-emerald-800"><Calendar size={32}/></div>}</div><div className="p-5"><p className="text-xs font-bold text-emerald-700 mb-2">{ev.event_date ? formatDate(ev.event_date) : t('তারিখ শীঘ্রই জানানো হবে', 'Date to be announced')}</p><h3 className="font-extrabold text-slate-900">{pick(ev, 'title', ev.title_bn || ev.title_en || t('ইভেন্ট', 'Event'))}</h3><p className="text-sm text-slate-600 mt-2 line-clamp-2">{pick(ev, 'description', ev.description_bn || ev.description_en || '')}</p><p className="text-xs text-slate-500 mt-3">{pick(ev, 'location', ev.location_bn || ev.location_en || '')}</p></div></article>)}</div> :
              <EmptyState icon="📅" title={t('কোনো আসন্ন ইভেন্ট নেই', 'No upcoming events')} description={t('নতুন ইভেন্ট ঘোষণা করা হলে এখানে দেখানো হবে।', 'Upcoming activities will appear here when announced.')} />}
          </section>

          <section aria-labelledby="home-media-heading">
            <div className="flex flex-wrap items-end justify-between gap-4 mb-6"><div><p className="text-xs font-bold uppercase tracking-[0.18em] text-emerald-700 mb-2">{t('ছবি ও ভিডিও', 'Photos and video')}</p><h2 id="home-media-heading" className="text-2xl md:text-3xl font-extrabold text-slate-900">{t('ইভেন্ট গ্যালারি', 'Event Gallery')}</h2></div><Link href="/media" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700">{t('মিডিয়া গ্যালারি', 'View media gallery')} <ArrowRight size={16}/></Link></div>
            {loading ? <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[1,2,3,4].map(n=><div key={n} className="h-36 rounded-2xl bg-slate-100 animate-pulse"/>)}</div> :
              media.length ? <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{media.map((item:any)=><Link key={item.id} href="/media" className="group relative overflow-hidden rounded-2xl bg-slate-900 min-h-36 aspect-[4/3]">{item.cover_image_url || item.thumbnail_url || item.file_url ? <img src={item.cover_image_url || item.thumbnail_url || item.file_url} alt={pick(item, 'title', item.title_bn || item.title_en || '')} className="absolute inset-0 w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" loading="lazy"/> : <div className="absolute inset-0 flex items-center justify-center text-white/80"><ImageIcon size={28}/></div>}<div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/90 to-transparent p-3 pt-8 text-white text-sm font-bold">{pick(item, 'title', item.title_bn || item.title_en || t('কার্যক্রমের ছবি', 'Activity photo'))}{String(item.media_type || item.type || '').toLowerCase().includes('video') && <PlayCircle className="inline ml-2" size={15}/>}</div></Link>)}</div> :
              <EmptyState icon="🖼️" title={t('মিডিয়া পাওয়া যায়নি', 'No media available')} description={t('ছবি ও ভিডিও যুক্ত হলে এখানে দেখানো হবে।', 'Published photos and videos will appear here.')} />}
          </section>
        </div>
      </section>
    </div>
  );
}
