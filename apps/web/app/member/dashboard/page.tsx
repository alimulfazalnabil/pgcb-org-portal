'use client';

import React, { useEffect, useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ShieldCheck,
  Calendar,
  FileText,
  CreditCard,
  Award,
  Bell,
  Sparkles,
  User,
  Settings,
  LogOut,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Clock,
  MapPin,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  Compass,
  ArrowRight,
  ExternalLink,
  MessageSquare,
  Globe,
  Menu,
  X,
  Home,
  Layers,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MemberDashboardData } from '@/lib/api/types';

export default function MemberDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<MemberDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<'bn' | 'en'>('en');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  async function fetchDashboard() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMemberDashboard();
      setData(res);
    } catch (err: any) {
      console.error('Failed to load member dashboard', err);
      setError(
        language === 'en'
          ? 'Unable to load your membership information. Please check your connection and retry.'
          : 'আপনার সদস্যপদের তথ্য লোড করা সম্ভব হয়নি। সংযোগ পরীক্ষা করে পুনরায় চেষ্টা করুন।'
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDashboard();
  }, []);

  async function handleLogout() {
    try {
      await api.logout();
    } catch {}
    router.push('/login');
  }

  // Time-of-day greeting
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    const isEn = language === 'en';
    const memberName = data?.member?.name_en || data?.user?.name_en || (isEn ? 'Member' : 'সদস্য');
    const prefix = isEn ? 'Engr.' : 'প্রকৌশলী';

    if (hour < 12) {
      return isEn ? `Good morning, ${prefix} ${memberName}` : `শুভ সকাল, ${prefix} ${data?.member?.name_bn || memberName}`;
    } else if (hour < 17) {
      return isEn ? `Good afternoon, ${prefix} ${memberName}` : `শুভ অপরাহ্ন, ${prefix} ${data?.member?.name_bn || memberName}`;
    } else {
      return isEn ? `Good evening, ${prefix} ${memberName}` : `শুভ সন্ধ্যা, ${prefix} ${data?.member?.name_bn || memberName}`;
    }
  }, [language, data]);

  // Normalized document stats
  const docStats = useMemo(() => {
    if (!data?.documents) {
      return { total: 0, verified: 0, pending: 0 };
    }
    if (Array.isArray(data.documents)) {
      const total = data.documents.length;
      const verified = data.documents.filter((d: any) => d.review_status === 'APPROVED').length;
      return { total, verified, pending: total - verified };
    }
    return {
      total: data.documents.total || 0,
      verified: data.documents.verified || 0,
      pending: data.documents.pending || 0,
    };
  }, [data?.documents]);

  const unreadCount = data?.unread_notifications_count ?? data?.quick_stats?.unread_notifications ?? 0;
  const isEn = language === 'en';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 font-black text-slate-950 text-lg">
              P
            </div>
            <div>
              <span className="font-extrabold tracking-tight text-white text-base lg:text-lg block leading-none">
                PGCB MEMBER PORTAL
              </span>
              <span className="text-[11px] font-semibold text-emerald-400 block leading-tight mt-0.5">
                {isEn ? 'Institution of Engineers Bangladesh Circle' : 'বাংলাদেশ পাওয়ার গ্রিড সদস্য পোর্টাল'}
              </span>
            </div>
          </div>
        </div>

        {/* Right Header Controls */}
        <div className="flex items-center gap-2.5 lg:gap-4">
          {/* Notifications Bell */}
          <Link
            href="/portal?tab=notifications"
            className="relative p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white transition-colors"
            title={isEn ? 'Notifications' : 'বিজ্ঞপ্তি'}
          >
            <Bell size={19} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 px-1.5 py-0.5 min-w-[18px] text-center text-[10px] font-black bg-rose-500 text-white rounded-full border-2 border-slate-900 animate-pulse">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>

          {/* Language Toggle */}
          <button
            type="button"
            onClick={() => setLanguage(language === 'en' ? 'bn' : 'en')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-bold text-slate-200 border border-slate-700/60 transition-colors"
          >
            <Globe size={14} className="text-emerald-400" />
            <span>{isEn ? 'বাংলা' : 'EN'}</span>
          </button>

          {/* User Profile Pill */}
          <Link
            href="/portal?tab=profile"
            className="flex items-center gap-2 py-1.5 px-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center font-black text-xs">
              {data?.member?.name_en ? data.member.name_en.charAt(0) : <User size={14} />}
            </div>
            <span className="hidden sm:inline text-xs font-bold text-emerald-300 max-w-[120px] truncate">
              {data?.member?.name_en || (isEn ? 'My Account' : 'প্রোফাইল')}
            </span>
          </Link>
        </div>
      </header>

      {/* Main Workspace Body */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex flex-col w-64 border-r border-slate-800/80 bg-slate-900/40 p-4 shrink-0">
          <div className="space-y-1">
            <Link
              href="/member/dashboard"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm bg-emerald-600 text-white shadow-md shadow-emerald-600/20"
            >
              <Home size={18} />
              <span>{isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}</span>
            </Link>

            <Link
              href="/member/profile"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <User size={18} />
              <span>{isEn ? 'My Profile' : 'আমার প্রোফাইল'}</span>
            </Link>

            <Link
              href="/member/membership"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <ShieldCheck size={18} />
              <span>{isEn ? 'Membership' : 'সদস্যপদ'}</span>
            </Link>

            <Link
              href="/member/application"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <FileText size={18} />
              <span>{isEn ? 'Application' : 'আবেদন ট্র্যাকিং'}</span>
            </Link>

            <Link
              href="/portal?tab=documents"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <FileCheck size={18} />
              <span>{isEn ? 'Documents' : 'ডকুমেন্টস'}</span>
            </Link>

            <Link
              href="/portal/id-card"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <CreditCard size={18} />
              <span>{isEn ? 'Digital ID' : 'ডিজিটাল আইডি'}</span>
            </Link>

            <Link
              href="/portal?tab=certificates"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Award size={18} />
              <span>{isEn ? 'Certificates' : 'সনদপত্র ওয়ালেট'}</span>
            </Link>

            <Link
              href="/portal?tab=payments"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <CreditCard size={18} />
              <span>{isEn ? 'Payments' : 'পেমেন্ট ও রসিদ'}</span>
            </Link>

            <Link
              href="/events"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Calendar size={18} />
              <span>{isEn ? 'Events' : 'ইভেন্টসমূহ'}</span>
            </Link>

            <Link
              href="/portal?tab=notifications"
              className="flex items-center justify-between px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Bell size={18} />
                <span>{isEn ? 'Notifications' : 'বিজ্ঞপ্তি'}</span>
              </div>
              {unreadCount > 0 && (
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  {unreadCount}
                </span>
              )}
            </Link>

            <Link
              href="/portal?tab=ai-assistant"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-amber-300 hover:bg-amber-500/10 transition-colors"
            >
              <Sparkles size={18} className="text-amber-400" />
              <span>{isEn ? 'AI Assistant' : 'এআই সহায়িকা'}</span>
            </Link>

            <Link
              href="/portal?tab=settings"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Settings size={18} />
              <span>{isEn ? 'Settings' : 'সেটিংস'}</span>
            </Link>
          </div>

          <div className="mt-auto pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut size={18} />
              <span>{isEn ? 'Logout' : 'লগআউট'}</span>
            </button>
          </div>
        </aside>

        {/* Mobile Flyout Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 md:hidden bg-slate-950/90 backdrop-blur-md p-6 flex flex-col justify-between overflow-y-auto">
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="font-black text-white text-lg">PGCB PORTAL MENU</div>
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-xl bg-slate-800 text-slate-300"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 mt-4">
                <Link
                  href="/member/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-emerald-600 text-white font-bold text-xs flex items-center gap-2"
                >
                  <Home size={16} />
                  <span>{isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}</span>
                </Link>
                <Link
                  href="/member/profile"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <User size={16} />
                  <span>{isEn ? 'My Profile' : 'প্রোফাইল'}</span>
                </Link>
                <Link
                  href="/member/membership"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <ShieldCheck size={16} />
                  <span>{isEn ? 'Membership' : 'সদস্যপদ'}</span>
                </Link>
                <Link
                  href="/portal?tab=documents"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <FileCheck size={16} />
                  <span>{isEn ? 'Documents' : 'ডকুমেন্ট'}</span>
                </Link>
                <Link
                  href="/portal/id-card"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <CreditCard size={16} />
                  <span>{isEn ? 'Digital ID' : 'আইডি কার্ড'}</span>
                </Link>
                <Link
                  href="/portal?tab=certificates"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <Award size={16} />
                  <span>{isEn ? 'Certificates' : 'সনদপত্র'}</span>
                </Link>
                <Link
                  href="/portal?tab=payments"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <CreditCard size={16} />
                  <span>{isEn ? 'Payments' : 'পেমেন্ট'}</span>
                </Link>
                <Link
                  href="/events"
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-3 rounded-xl bg-slate-900 text-slate-200 font-bold text-xs flex items-center gap-2 border border-slate-800"
                >
                  <Calendar size={16} />
                  <span>{isEn ? 'Events' : 'ইভেন্ট'}</span>
                </Link>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                handleLogout();
              }}
              className="mt-6 w-full py-3 rounded-xl bg-rose-500/20 text-rose-300 font-bold text-sm border border-rose-500/40"
            >
              {isEn ? 'Logout' : 'লগআউট'}
            </button>
          </div>
        )}

        {/* Main Content Area */}
        <main className="flex-1 p-4 lg:p-8 space-y-6 lg:space-y-8 overflow-y-auto pb-24 md:pb-8">
          {/* Loading State with Skeleton */}
          {loading && (
            <div className="space-y-6 animate-pulse">
              <div className="h-9 w-64 bg-slate-800/80 rounded-xl" />
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-28 bg-slate-900 border border-slate-800/80 rounded-2xl" />
                ))}
              </div>
              <div className="h-32 bg-slate-900 border border-slate-800/80 rounded-2xl" />
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 h-72 bg-slate-900 border border-slate-800/80 rounded-2xl" />
                <div className="h-72 bg-slate-900 border border-slate-800/80 rounded-2xl" />
              </div>
            </div>
          )}

          {/* API Failure State */}
          {!loading && error && (
            <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-center space-y-4 max-w-lg mx-auto my-12">
              <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto">
                <AlertCircle size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">
                  {isEn ? 'Unable to load member dashboard' : 'ড্যাশবোর্ড তথ্য লোড করা যায়নি'}
                </h3>
                <p className="text-sm text-rose-300/80 mt-1">{error}</p>
              </div>
              <button
                type="button"
                onClick={fetchDashboard}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors shadow-lg shadow-rose-600/30"
              >
                <RefreshCw size={14} />
                <span>{isEn ? 'Retry' : 'পুনরায় চেষ্টা করুন'}</span>
              </button>
            </div>
          )}

          {/* Fully Loaded Dashboard Content */}
          {!loading && !error && data && (
            <>
              {/* Welcome Greeting Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/80">
                <div>
                  <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                    {greeting}
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                    {isEn
                      ? 'PGCB Member ID: '
                      : 'পিজিসিবি সদস্য নম্বর: '}
                    <span className="font-mono font-bold text-emerald-400">
                      {data.member?.membership_id || data.membership?.membership_id || 'PENDING'}
                    </span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Link
                    href="/portal/id-card"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors border border-slate-700/60"
                  >
                    <CreditCard size={14} className="text-emerald-400" />
                    <span>{isEn ? 'Digital Card' : 'ডিজিটাল কার্ড'}</span>
                  </Link>

                  <Link
                    href="/portal?tab=profile"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors shadow-md shadow-emerald-600/20"
                  >
                    <User size={14} />
                    <span>{isEn ? 'Edit Profile' : 'প্রোফাইল'}</span>
                  </Link>
                </div>
              </div>

              {/* Step 3: Six Primary Dashboard Cards */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 lg:gap-4">
                {/* 1. Membership Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      <span>{isEn ? 'Membership' : 'সদস্যপদ'}</span>
                      <span className="flex items-center gap-1 text-emerald-400">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        {data.membership?.status || 'ACTIVE'}
                      </span>
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight font-mono">
                      {data.member?.membership_id || data.membership?.membership_id || 'PGCB-001245'}
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-2 block">
                    {data.membership?.type || 'Professional'}
                  </span>
                </div>

                {/* 2. Validity Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {isEn ? 'Valid Until' : 'মেয়াদ উত্তীর্ণ'}
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight">
                      {data.membership?.valid_until_formatted ||
                        data.membership?.valid_until ||
                        '31 Dec 2027'}
                    </div>
                  </div>
                  <span className="text-[11px] text-emerald-400 mt-2 block font-medium">
                    {isEn ? 'Current Status: Active' : 'সক্রিয় সদস্য'}
                  </span>
                </div>

                {/* 3. Grid Circle Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {isEn ? 'Grid Circle' : 'গ্রিড সার্কেল'}
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight">
                      {data.member?.circle || data.membership?.circle || 'Dhaka'}
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-2 block">
                    {data.member?.circle_bn || 'ঢাকা সার্কেল'}
                  </span>
                </div>

                {/* 4. Application Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {isEn ? 'Application' : 'আবেদন'}
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight flex items-center gap-1.5">
                      <CheckCircle2 size={15} className="text-emerald-400 shrink-0" />
                      <span>{data.application?.status || 'Approved'}</span>
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-2 block truncate">
                    {data.application?.reference || data.application?.application_no || 'PGCB-APP-2026-00123'}
                  </span>
                </div>

                {/* 5. Documents Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {isEn ? 'Documents' : 'ডকুমেন্ট'}
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight">
                      {docStats.verified} / {docStats.total} {isEn ? 'verified' : 'যাচাইকৃত'}
                    </div>
                  </div>
                  <span className="text-[11px] text-amber-400 mt-2 block">
                    {docStats.pending > 0
                      ? `${docStats.pending} ${isEn ? 'pending' : 'অপেক্ষমাণ'}`
                      : isEn
                      ? 'All verified ✓'
                      : 'সকল নথি যাচাইকৃত ✓'}
                  </span>
                </div>

                {/* 6. Profile Completion Card */}
                <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-900/60 border border-slate-800/80 hover:border-emerald-500/40 transition-colors flex flex-col justify-between">
                  <div>
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                      {isEn ? 'Profile' : 'প্রোফাইল'}
                    </div>
                    <div className="font-black text-sm lg:text-base text-white tracking-tight">
                      {data.profile_completion ?? 90}% {isEn ? 'complete' : 'সম্পূর্ণ'}
                    </div>
                  </div>
                  <Link
                    href="/portal?tab=profile"
                    className="text-[11px] text-emerald-400 hover:text-emerald-300 font-bold mt-2 inline-flex items-center gap-1 group"
                  >
                    <span>{isEn ? 'Complete' : 'সম্পন্ন করুন'}</span>
                    <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>

              {/* Step 7: Profile Completion Progress Bar & Breakdown */}
              <div className="p-5 lg:p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/30 border border-slate-800/80 shadow-xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                      <User size={18} className="text-emerald-400" />
                      <span>{isEn ? 'Profile Completion' : 'প্রোফাইল সম্পূর্ণতা'}</span>
                    </h2>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {isEn
                        ? 'Institutional verification and data integrity criteria'
                        : 'প্রাতিষ্ঠানিক যাচাইকরণ ও তথ্য নির্ভরযোগ্যতার মাপকাঠি'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-black text-emerald-400">
                      {data.profile_completion ?? 90}%
                    </span>
                    <Link
                      href="/portal?tab=profile"
                      className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors shadow-md shadow-emerald-600/20"
                    >
                      {isEn ? 'Complete your profile' : 'প্রোফাইল সম্পন্ন করুন'}
                    </Link>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden p-0.5">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700 shadow-sm"
                    style={{ width: `${Math.min(100, Math.max(8, data.profile_completion ?? 90))}%` }}
                  />
                </div>

                {/* Breakdown items */}
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2 text-xs">
                  {data.profile_completion_details?.items ? (
                    data.profile_completion_details.items.map((it: any) => (
                      <div
                        key={it.key}
                        className={`flex items-center gap-2 p-2 rounded-xl border ${
                          it.completed
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 font-semibold'
                            : 'bg-slate-800/40 border-slate-700/50 text-slate-400'
                        }`}
                      >
                        <span className="text-sm font-bold">
                          {it.completed ? '✓' : '✗'}
                        </span>
                        <span className="truncate">
                          {isEn ? it.label_en : it.label_bn}
                        </span>
                      </div>
                    ))
                  ) : (
                    <>
                      <div className="flex items-center gap-2 p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
                        <span>✓</span>
                        <span>{isEn ? 'Basic information' : 'প্রাথমিক তথ্য'}</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
                        <span>✓</span>
                        <span>{isEn ? 'Contact information' : 'যোগাযোগের তথ্য'}</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
                        <span>✓</span>
                        <span>{isEn ? 'Professional information' : 'পেশাগত তথ্য'}</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-semibold">
                        <span>✓</span>
                        <span>{isEn ? 'Profile photo' : 'প্রোফাইল ছবি'}</span>
                      </div>
                      <div className="flex items-center gap-2 p-2 rounded-xl bg-slate-800/40 border border-slate-700/50 text-slate-400">
                        <span>✗</span>
                        <span>{isEn ? 'Emergency contact' : 'জরুরি যোগাযোগ'}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Main Two-Column Section: Left (Activity & Events), Right (Notifications & AI Assistant) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
                {/* Left 2 Cols: Activity Feed & Upcoming Events */}
                <div className="lg:col-span-2 space-y-6 lg:space-y-8">
                  {/* Step 4: Recent Activity */}
                  <div className="p-5 lg:p-6 rounded-2xl bg-slate-900 border border-slate-800/80 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-2.5">
                        <Clock size={18} className="text-emerald-400" />
                        <h2 className="text-base font-extrabold text-white">
                          {isEn ? 'Recent Activity' : 'সাম্প্রতিক কর্মকাণ্ড'}
                        </h2>
                      </div>
                      <span className="text-xs text-slate-400 font-medium">
                        {isEn ? 'Verified History' : 'যাচাইকৃত ইতিহাস'}
                      </span>
                    </div>

                    {data.recent_activity && data.recent_activity.length > 0 ? (
                      <div className="space-y-3">
                        {data.recent_activity.slice(0, 6).map((act: any, idx: number) => {
                          const iconColor =
                            act.type === 'PAYMENT'
                              ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                              : act.type === 'CERTIFICATE'
                              ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                              : act.type === 'APPLICATION'
                              ? 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
                              : 'text-purple-400 bg-purple-500/10 border-purple-500/30';

                          return (
                            <Link
                              key={act.id || idx}
                              href={act.href || '/portal'}
                              className="group flex items-start justify-between p-3.5 rounded-xl bg-slate-800/40 hover:bg-slate-800/80 border border-slate-800/60 hover:border-slate-700 transition-colors"
                            >
                              <div className="flex items-start gap-3">
                                <div
                                  className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border mt-0.5 ${iconColor}`}
                                >
                                  {act.type === 'PAYMENT' && <CheckCircle2 size={16} />}
                                  {act.type === 'CERTIFICATE' && <Award size={16} />}
                                  {act.type === 'APPLICATION' && <FileText size={16} />}
                                  {act.type === 'MEMBERSHIP' && <ShieldCheck size={16} />}
                                  {act.type === 'PROFILE' && <User size={16} />}
                                  {act.type === 'DOCUMENT' && <FileCheck size={16} />}
                                  {act.type === 'EVENT' && <Calendar size={16} />}
                                  {!['PAYMENT', 'CERTIFICATE', 'APPLICATION', 'MEMBERSHIP', 'PROFILE', 'DOCUMENT', 'EVENT'].includes(
                                    act.type || ''
                                  ) && <CheckCircle2 size={16} />}
                                </div>
                                <div>
                                  <div className="font-bold text-sm text-slate-100 group-hover:text-emerald-400 transition-colors">
                                    {isEn ? act.title || act.title_en : act.title_bn || act.title}
                                  </div>
                                  <div className="text-xs text-slate-400 mt-0.5">
                                    {isEn ? act.description : act.subtitle_bn || act.description}
                                  </div>
                                </div>
                              </div>
                              <span className="text-[11px] font-semibold text-slate-400 shrink-0 mt-0.5 ml-2">
                                {isEn
                                  ? act.relative_time_en || act.relative_time || 'Recent'
                                  : act.relative_time_bn || act.relative_time || 'সম্প্রতি'}
                              </span>
                            </Link>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-8 text-center text-sm text-slate-400">
                        {isEn ? 'No recent activity recorded.' : 'কোন সাম্প্রতিক কার্যকলাপ নেই।'}
                      </div>
                    )}
                  </div>

                  {/* Step 5: Upcoming Events */}
                  <div className="p-5 lg:p-6 rounded-2xl bg-slate-900 border border-slate-800/80 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-2.5">
                        <Calendar size={18} className="text-emerald-400" />
                        <h2 className="text-base font-extrabold text-white">
                          {isEn ? 'Upcoming Events' : 'আসন্ন ইভেন্টসমূহ'}
                        </h2>
                      </div>
                      <Link
                        href="/events"
                        className="text-xs font-bold text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1"
                      >
                        <span>{isEn ? 'Browse Events' : 'সকল ইভেন্ট'}</span>
                        <ChevronRight size={14} />
                      </Link>
                    </div>

                    {data.upcoming_events && data.upcoming_events.length > 0 ? (
                      <div className="space-y-3">
                        {data.upcoming_events.slice(0, 3).map((ev: any) => (
                          <div
                            key={ev.id}
                            className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-slate-800/40 border border-slate-800/60 gap-3"
                          >
                            <div className="flex items-center gap-3">
                              {/* Date Badge */}
                              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col items-center justify-center shrink-0">
                                <span className="text-base font-black text-emerald-400 leading-none">
                                  {ev.day || '15'}
                                </span>
                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider mt-0.5">
                                  {ev.month || 'OCT'}
                                </span>
                              </div>

                              <div>
                                <h3 className="font-bold text-sm text-white">
                                  {isEn ? ev.title || ev.title_en : ev.title_bn || ev.title}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
                                  <span className="flex items-center gap-1">
                                    <MapPin size={12} className="text-slate-400" />
                                    {isEn ? ev.location || ev.location_en : ev.location_bn || ev.location}
                                  </span>
                                  <span>·</span>
                                  <span>{ev.time || '10:00 AM'}</span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2.5 self-end sm:self-auto">
                              {ev.is_registered ? (
                                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-xs font-bold">
                                  <CheckCircle2 size={13} />
                                  <span>{isEn ? 'Registered' : 'নিবন্ধিত'}</span>
                                </span>
                              ) : null}

                              <Link
                                href={`/events/${ev.slug || ev.id}`}
                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                                  ev.is_registered
                                    ? 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20'
                                }`}
                              >
                                {ev.is_registered
                                  ? isEn
                                    ? 'View Event'
                                    : 'বিস্তারিত'
                                  : isEn
                                  ? 'Register'
                                  : 'নিবন্ধন করুন'}
                              </Link>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-8 text-center space-y-3 bg-slate-900/50 rounded-xl border border-dashed border-slate-800">
                        <Calendar size={28} className="mx-auto text-slate-400" />
                        <p className="text-sm text-slate-400">
                          {isEn ? 'No upcoming events.' : 'কোন আসন্ন ইভেন্ট পাওয়া যায়নি।'}
                        </p>
                        <Link
                          href="/events"
                          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 transition-colors"
                        >
                          <span>{isEn ? 'Browse Events' : 'ইভেন্টসমূহ দেখুন'}</span>
                          <ArrowRight size={13} />
                        </Link>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Column: Step 6 Notifications & Step 9 AI Integration */}
                <div className="space-y-6 lg:space-y-8">
                  {/* Step 9: Prominent AI Assistant Integration Banner */}
                  <div className="p-5 lg:p-6 rounded-2xl bg-gradient-to-br from-amber-500/20 via-slate-900 to-slate-900 border border-amber-500/40 shadow-xl space-y-3.5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 -mr-4 -mt-4 w-28 h-28 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />

                    <div className="flex items-center gap-2 text-amber-400 font-extrabold text-sm">
                      <Sparkles size={18} />
                      <span>{isEn ? 'Need help? Ask PGCB AI Assistant' : 'সহায়তা প্রয়োজন? এআইকে প্রশ্ন করুন'}</span>
                    </div>

                    <p className="text-xs text-slate-300 italic bg-slate-950/50 p-2.5 rounded-xl border border-slate-800">
                      &ldquo;আমার membership কখন expire হবে?&rdquo;
                    </p>

                    <Link
                      href="/portal?tab=ai-assistant"
                      className="w-full inline-flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black text-xs transition-all shadow-lg shadow-amber-500/20"
                    >
                      <MessageSquare size={14} />
                      <span>{isEn ? 'Ask AI Assistant →' : 'এআই সহায়িকা খুলুন →'}</span>
                    </Link>
                  </div>

                  {/* Step 6: Notification Preview */}
                  <div className="p-5 lg:p-6 rounded-2xl bg-slate-900 border border-slate-800/80 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                        <Bell size={18} className="text-emerald-400" />
                        <h2 className="text-base font-extrabold text-white">
                          {isEn ? 'Notifications' : 'বিজ্ঞপ্তি'}
                        </h2>
                      </div>
                      <Link
                        href="/portal?tab=notifications"
                        className="text-xs font-bold text-emerald-400 hover:text-emerald-300"
                      >
                        {isEn ? 'View all →' : 'সকল দেখুন →'}
                      </Link>
                    </div>

                    {data.notifications && data.notifications.length > 0 ? (
                      <div className="space-y-3">
                        {data.notifications.slice(0, 5).map((n: any) => {
                          const dotClass =
                            n.dot_color === 'blue'
                              ? 'bg-blue-400'
                              : n.dot_color === 'green'
                              ? 'bg-emerald-400'
                              : n.dot_color === 'amber'
                              ? 'bg-amber-400'
                              : 'bg-purple-400';

                          return (
                            <Link
                              key={n.id}
                              href="/portal?tab=notifications"
                              className="group block p-3 rounded-xl bg-slate-800/40 hover:bg-slate-800/70 border border-slate-800/50 transition-colors"
                            >
                              <div className="flex items-start gap-2.5">
                                <span
                                  className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${dotClass}`}
                                />
                                <div>
                                  <div className="text-xs font-bold text-slate-200 group-hover:text-white transition-colors leading-snug">
                                    {isEn ? n.title || n.title_bn : n.title_bn || n.title}
                                  </div>
                                  <div className="text-[11px] text-slate-400 mt-1">
                                    {isEn
                                      ? n.relative_time_en || n.relative_time || 'Recently'
                                      : n.relative_time_bn || n.relative_time || 'সম্প্রতি'}
                                  </div>
                                </div>
                              </div>
                            </Link>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-6 text-center text-xs text-slate-400">
                        {isEn ? 'No notifications to display.' : 'কোন বিজ্ঞপ্তি নেই।'}
                      </div>
                    )}
                  </div>

                  {/* Payment Summary Box */}
                  {data.payment_summary && (
                    <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800/80 space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-slate-400 uppercase tracking-wider">
                        <span>{isEn ? 'Payment Status' : 'পেমেন্ট সারসংক্ষেপ'}</span>
                        <Link href="/portal?tab=payments" className="text-emerald-400 hover:underline">
                          {isEn ? 'Receipts' : 'রসিদ'}
                        </Link>
                      </div>
                      <div className="flex items-baseline justify-between pt-1">
                        <span className="text-sm font-semibold text-slate-300">
                          {isEn ? 'Total Verified Payments' : 'মোট পরিশোধিত ফি'}
                        </span>
                        <span className="text-base font-black text-emerald-400 font-mono">
                          {data.payment_summary.total_paid_formatted || `৳${Number(data.payment_summary.total_paid || 0).toLocaleString()}`}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                        <span>
                          {isEn ? 'Successful: ' : 'সফল: '}
                          <strong className="text-emerald-400">{data.payment_summary.successful ?? 0}</strong>
                        </span>
                        <span>
                          {isEn ? 'Pending: ' : 'অপেক্ষমাণ: '}
                          <strong className="text-amber-400">{data.payment_summary.pending ?? 0}</strong>
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </main>
      </div>

      {/* Step 8: Mobile Bottom Navigation */}
      <nav
        aria-label="Mobile Member Navigation"
        className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 shadow-2xl px-2 py-2"
      >
        <div className="grid grid-cols-5 text-center">
          <Link
            href="/member/dashboard"
            className="flex flex-col items-center gap-1 text-[11px] font-bold text-emerald-400"
          >
            <Home size={18} />
            <span>{isEn ? 'Home' : 'হোম'}</span>
          </Link>

          <Link
            href="/portal?tab=membership"
            className="flex flex-col items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
          >
            <CreditCard size={18} />
            <span>{isEn ? 'Membership' : 'সদস্যপদ'}</span>
          </Link>

          <Link
            href="/portal?tab=documents"
            className="flex flex-col items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
          >
            <FileText size={18} />
            <span>{isEn ? 'Documents' : 'ডকুমেন্ট'}</span>
          </Link>

          <Link
            href="/portal?tab=notifications"
            className="relative flex flex-col items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
          >
            <Bell size={18} />
            {unreadCount > 0 && (
              <span className="absolute top-0 right-4 w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            )}
            <span>{isEn ? 'Alerts' : 'বিজ্ঞপ্তি'}</span>
          </Link>

          <Link
            href="/portal"
            className="flex flex-col items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-white"
          >
            <Layers size={18} />
            <span>{isEn ? 'More' : 'আরও'}</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}
