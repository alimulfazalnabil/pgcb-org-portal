'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  User,
  ShieldCheck,
  CreditCard,
  FileText,
  FileCheck,
  Award,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  Languages,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  HeartPulse,
  Lock,
  Edit3,
  FileEdit,
  Sparkles,
  Info,
  Calendar,
  Layers,
  HelpCircle,
  Building,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MemberProfile, VerificationBadge } from '@/lib/api/types';

export default function MemberProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'bn' | 'en'>('en');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedBadge, setSelectedBadge] = useState<VerificationBadge | null>(null);

  const isEn = lang === 'en';

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data = await api.getProfile();
        setProfile(data);
        if (data.preferred_language === 'bn') {
          setLang('bn');
        }
      } catch (err: any) {
        if (err?.status === 401) {
          router.push('/login?redirect=/member/profile');
          return;
        }
        setError(err?.message || 'Failed to load profile details');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [router]);

  const toggleLanguage = () => {
    setLang((prev) => (prev === 'en' ? 'bn' : 'en'));
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      router.push('/login');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-slate-400 font-medium text-sm">
            {isEn ? 'Loading member profile...' : 'সদস্য প্রোফাইল লোড হচ্ছে...'}
          </p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto" />
          <h2 className="text-lg font-bold text-white">
            {isEn ? 'Unable to load profile' : 'প্রোফাইল লোড করা সম্ভব হয়নি'}
          </h2>
          <p className="text-sm text-slate-400">{error || 'Session expired or profile unavailable'}</p>
          <div className="flex justify-center gap-3 pt-2">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors"
            >
              {isEn ? 'Retry' : 'পুনরায় চেষ্টা করুন'}
            </button>
            <Link
              href="/member/dashboard"
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold transition-colors"
            >
              {isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const pInfo = profile.personal_information || {};
  const profInfo = profile.professional_information || {};
  const cInfo = profile.contact_information || {};
  const eContact = profile.emergency_contact || {};
  const badges = profile.verification_badges || {};
  const comp = profile.profile_completion_details;
  const pct = profile.profile_completion ?? 80;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link href="/member/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-emerald-600/30">
              P
            </div>
            <div className="hidden sm:block">
              <span className="font-extrabold tracking-tight text-white text-sm">PGCB</span>
              <span className="text-emerald-400 font-bold text-xs ml-1.5 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/50">
                MEMBER PORTAL
              </span>
            </div>
          </Link>
        </div>

        {/* Global Controls & Member Chip */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 hover:border-slate-600 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            title="Switch Language"
          >
            <Languages size={15} />
            <span className="uppercase">{lang}</span>
          </button>

          <Link
            href="/portal?tab=notifications"
            className="p-2 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-750 transition-colors relative"
            title={isEn ? 'Notifications' : 'বিজ্ঞপ্তি'}
          >
            <Bell size={17} />
          </Link>

          <Link
            href="/member/profile"
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 transition-colors"
          >
            <div className="w-6 h-6 rounded-full bg-emerald-700 text-white flex items-center justify-center font-bold text-[11px] overflow-hidden">
              {profile.photo_url ? (
                <img src={profile.photo_url} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                profile.name_en?.[0] || 'M'
              )}
            </div>
            <span className="text-xs font-semibold max-w-[120px] truncate hidden md:inline">
              {profile.name_en || profile.name_bn || 'Member'}
            </span>
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar Navigation */}
        <aside
          className={`lg:w-64 bg-slate-900/60 lg:bg-slate-900/30 border-r border-slate-800/80 p-4 lg:p-6 shrink-0 transition-all duration-300 ${
            mobileMenuOpen ? 'block' : 'hidden lg:block'
          }`}
        >
          <div className="space-y-1">
            <Link
              href="/member/dashboard"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Layers size={18} />
              <span>{isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}</span>
            </Link>

            <Link
              href="/member/profile"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm bg-emerald-600/15 border border-emerald-500/30 text-emerald-300 transition-colors"
            >
              <User size={18} className="text-emerald-400" />
              <span>{isEn ? 'My Profile' : 'আমার প্রোফাইল'}</span>
            </Link>

            <Link
              href="/member/profile/edit"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors pl-8 text-xs"
            >
              <Edit3 size={15} />
              <span>{isEn ? 'Edit Profile' : 'তথ্য পরিবর্তন'}</span>
            </Link>

            <Link
              href="/member/profile/change-requests"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors pl-8 text-xs"
            >
              <FileEdit size={15} />
              <span>{isEn ? 'Change Requests' : 'ভেরিফিকেশন আবেদন'}</span>
            </Link>

            <Link
              href="/portal?tab=membership"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <ShieldCheck size={18} />
              <span>{isEn ? 'Membership' : 'সদস্যপদ'}</span>
            </Link>

            <Link
              href="/portal?tab=application"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <FileText size={18} />
              <span>{isEn ? 'Application' : 'আবেদন ট্র্যাকিং'}</span>
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
              href="/member/dashboard#assistant"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Sparkles size={18} className="text-amber-400" />
              <span>{isEn ? 'AI Assistant' : 'এআই সহকারী'}</span>
            </Link>

            <div className="pt-4 mt-4 border-t border-slate-800/80 space-y-1">
              <Link
                href="/portal?tab=settings"
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <Settings size={18} />
                <span>{isEn ? 'Settings' : 'সেটিংস'}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:bg-rose-500/10 transition-colors text-left"
              >
                <LogOut size={18} />
                <span>{isEn ? 'Sign Out' : 'লগ আউট'}</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Profile Content Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6 lg:space-y-8">
          {/* Breadcrumbs */}
          <nav className="flex items-center gap-2 text-xs text-slate-400 font-medium">
            <Link href="/member/dashboard" className="hover:text-slate-200 transition-colors">
              {isEn ? 'Portal' : 'পোর্টাল'}
            </Link>
            <ChevronRight size={13} />
            <span className="text-emerald-400 font-bold">{isEn ? 'My Profile' : 'আমার প্রোফাইল'}</span>
          </nav>

          {/* Section 1: Hero Member Identity Card */}
          <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/40 border border-slate-800/80 shadow-2xl p-6 sm:p-8">
            <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
              <div className="flex flex-col sm:flex-row items-center sm:items-start md:items-center gap-5 text-center sm:text-left">
                {/* Member Photo */}
                <div className="relative group">
                  <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-2xl bg-slate-800 border-2 border-emerald-500/40 overflow-hidden flex items-center justify-center shadow-xl shadow-slate-950/60 shrink-0">
                    {profile.photo_url ? (
                      <img
                        src={profile.photo_url}
                        alt={profile.name_en || 'Profile Photo'}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-400">
                        <User size={38} className="text-slate-500" />
                        <span className="text-[10px] font-bold uppercase mt-1 text-slate-400">
                          {isEn ? 'No Photo' : 'ছবি নেই'}
                        </span>
                      </div>
                    )}
                  </div>
                  <Link
                    href="/member/profile/edit"
                    className="absolute -bottom-2 -right-2 p-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-colors"
                    title={isEn ? 'Change Photo' : 'ছবি পরিবর্তন'}
                  >
                    <Edit3 size={14} />
                  </Link>
                </div>

                {/* Name, ID, Badges */}
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-extrabold text-xs flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                      {profile.status === 'ACTIVE'
                        ? isEn
                          ? 'Active Member'
                          : 'সক্রিয় সদস্য'
                        : profile.status || 'Active Member'}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 font-semibold text-xs">
                      {profile.membership_type || 'General'}
                    </span>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                    {profile.name_en || 'Engr. Member Name'}
                  </h1>
                  {profile.name_bn && (
                    <div className="text-base font-semibold text-slate-300 font-bengali">
                      {profile.name_bn}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 pt-1 text-xs text-slate-400">
                    <span className="font-mono font-bold text-emerald-400 bg-slate-900/80 px-2.5 py-1 rounded-lg border border-slate-800">
                      ID: {profile.membership_id || 'PGD-2026-1001'}
                    </span>
                    <span className="flex items-center gap-1">
                      <MapPin size={13} className="text-slate-500" />
                      {profile.circle_en || profile.circle_bn || 'Dhaka Grid Circle'}
                    </span>
                    {profile.validity_date && (
                      <span className="flex items-center gap-1 text-slate-400">
                        <Clock size={13} className="text-slate-500" />
                        {isEn ? 'Valid to:' : 'মেয়াদ:'} {profile.validity_date}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 w-full md:w-auto shrink-0">
                <Link
                  href="/member/profile/edit"
                  className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/25 transition-all"
                >
                  <Edit3 size={15} />
                  <span>{isEn ? 'Edit Profile' : 'তথ্য পরিবর্তন'}</span>
                </Link>

                <Link
                  href="/portal/id-card"
                  className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-bold text-xs transition-colors"
                >
                  <CreditCard size={15} className="text-emerald-400" />
                  <span>{isEn ? 'Digital ID' : 'ডিজিটাল আইডি'}</span>
                </Link>

                <Link
                  href="/member/profile/change-requests"
                  className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-slate-300 font-bold text-xs transition-colors"
                >
                  <FileEdit size={15} className="text-amber-400" />
                  <span>{isEn ? 'Change Requests' : 'পরিবর্তন আবেদন'}</span>
                </Link>
              </div>
            </div>

            {/* Verification Badges Row */}
            <div className="mt-6 pt-6 border-t border-slate-800/80">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck size={14} className="text-emerald-400" />
                  {isEn ? 'Verification Badges' : 'যাচাইকরণ ব্যাজ'}
                </span>
                <span className="text-[11px] text-slate-400">
                  {isEn ? 'Click badge for verification details' : 'বিস্তারিত দেখতে ব্যাজে ক্লিক করুন'}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2.5">
                {Object.entries(badges).map(([key, badge]: [string, any]) => {
                  const isVerified = badge.is_verified || badge.status === 'VERIFIED';
                  return (
                    <button
                      key={key}
                      onClick={() => setSelectedBadge(badge)}
                      className={`flex items-center justify-between p-2.5 rounded-xl border text-left transition-all ${
                        isVerified
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20'
                          : 'bg-slate-800/40 border-slate-700/60 text-slate-400 hover:bg-slate-800/80'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        {isVerified ? (
                          <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                        ) : (
                          <Clock size={16} className="text-amber-400 shrink-0" />
                        )}
                        <span className="text-xs font-bold capitalize truncate">
                          {key === 'nid' ? 'Smart NID' : key}
                        </span>
                      </div>
                      <Info size={13} className="text-slate-500 shrink-0 ml-1" />
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          {/* Section 2: Dynamic Profile Completion Progress */}
          <section className="p-5 lg:p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-emerald-950/30 border border-slate-800/80 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                  <User size={18} className="text-emerald-400" />
                  <span>{isEn ? 'Profile Completion' : 'প্রোফাইল সম্পূর্ণতা'}</span>
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {isEn
                    ? 'Complete all 5 core sections to maximize your portal verification status'
                    : 'পোর্টাল সুবিধার পূর্ণ ব্যবহারের জন্য ৫টি বিভাগ সম্পন্ন করুন'}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-emerald-400">{pct}%</span>
                {pct < 100 && (
                  <Link
                    href="/member/profile/edit"
                    className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors shadow-md shadow-emerald-600/20"
                  >
                    {isEn ? 'Complete Profile' : 'তথ্য পূরণ করুন'}
                  </Link>
                )}
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700 shadow-sm"
                style={{ width: `${Math.min(100, Math.max(10, pct))}%` }}
              />
            </div>

            {/* Incomplete Checklist if any */}
            {comp?.missing && comp.missing.length > 0 && (
              <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex flex-wrap items-center gap-3 text-xs">
                <span className="font-bold text-slate-400 flex items-center gap-1.5">
                  <AlertCircle size={14} className="text-amber-400" />
                  {isEn ? 'Missing information:' : 'অসম্পূর্ণ তথ্যসমূহ:'}
                </span>
                {comp.missing.map((m: any, idx: number) => (
                  <Link
                    key={idx}
                    href={m.route || '/member/profile/edit'}
                    className="px-2.5 py-1 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-amber-300 font-semibold flex items-center gap-1 transition-colors"
                  >
                    <span>{isEn ? m.label : m.label_bn || m.label}</span>
                    <ArrowRight size={11} />
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* Section 3: Protected Information Notice Banner */}
          <div className="p-4 rounded-2xl bg-sky-950/30 border border-sky-800/40 flex items-start gap-3.5">
            <Lock size={19} className="text-sky-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-sky-200">
                {isEn ? 'Institutional Identity Protection' : 'প্রাতিষ্ঠানিক পরিচয় সুরক্ষা'}
              </h4>
              <p className="text-xs text-sky-300/80 leading-relaxed">
                {isEn
                  ? 'Key fields such as Full Legal Name, Date of Birth, NID, Membership ID, and Grid Circle are protected to preserve institutional records. Any change to these fields requires admin review.'
                  : 'পূর্ণ নাম, জন্ম তারিখ, জাতীয় পরিচয়পত্র, সদস্য আইডি এবং গ্রিড সার্কেল প্রাতিষ্ঠানিক নিরাপত্তার জন্য সুরক্ষিত। এসব তথ্যে পরিবর্তন আনতে প্রশাসনিক যাচাইয়ের জন্য রিকোয়েস্ট জমা দিন।'}
              </p>
              <Link
                href="/member/profile/change-requests"
                className="inline-flex items-center gap-1 text-xs font-bold text-sky-400 hover:text-sky-300 pt-1"
              >
                <span>{isEn ? 'Submit Profile Change Request' : 'পরিবর্তন আবেদন জমা দিন'}</span>
                <ArrowRight size={13} />
              </Link>
            </div>
          </div>

          {/* Section 4: 4 Detailed Information Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1: Personal Information */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="font-extrabold text-base text-white flex items-center gap-2">
                  <User size={18} className="text-emerald-400" />
                  <span>{isEn ? 'Personal Information' : 'ব্যক্তিগত তথ্য'}</span>
                </h3>
                <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1">
                  <Lock size={12} className="text-slate-400" />
                  {isEn ? 'Partially Protected' : 'আংশিক সুরক্ষিত'}
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Full Name (English)' : 'পূর্ণ নাম (ইংরেজি)'}</span>
                  <span className="font-bold text-white text-right">{pInfo.name_en || profile.name_en || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Full Name (Bangla)' : 'পূর্ণ নাম (বাংলা)'}</span>
                  <span className="font-bold text-white font-bengali text-right">
                    {pInfo.name_bn || profile.name_bn || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? "Father's Name" : 'পিতার নাম'}</span>
                  <span className="font-medium text-slate-200 text-right">{pInfo.father_name || profile.father_name || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? "Mother's Name" : 'মাতার নাম'}</span>
                  <span className="font-medium text-slate-200 text-right">{pInfo.mother_name || profile.mother_name || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Date of Birth' : 'জন্ম তারিখ'}</span>
                  <span className="font-mono text-slate-200 text-right">{pInfo.date_of_birth || profile.date_of_birth || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Gender' : 'লিঙ্গ'}</span>
                  <span className="font-medium text-slate-200 text-right">{pInfo.gender || profile.gender || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Blood Group' : 'রক্তের গ্রুপ'}</span>
                  <span className="font-bold text-rose-400 text-right">{pInfo.blood_group || profile.blood_group || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">{isEn ? 'NID / Passport' : 'জাতীয় পরিচয়পত্র'}</span>
                  <span className="font-mono font-bold text-emerald-400 text-right">
                    {pInfo.nid_number || profile.nid_number || '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* Card 2: Professional Information */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="font-extrabold text-base text-white flex items-center gap-2">
                  <Briefcase size={18} className="text-emerald-400" />
                  <span>{isEn ? 'Professional Information' : 'পেশাগত তথ্য'}</span>
                </h3>
                <Link
                  href="/member/profile/edit"
                  className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                >
                  <Edit3 size={13} />
                  <span>{isEn ? 'Edit' : 'সম্পাদনা'}</span>
                </Link>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Designation (English)' : 'পদবি (ইংরেজি)'}</span>
                  <span className="font-bold text-white text-right">
                    {profInfo.designation_en || profile.designation_en || 'Sub-Assistant Engineer'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Designation (Bangla)' : 'পদবি (বাংলা)'}</span>
                  <span className="font-bold text-white font-bengali text-right">
                    {profInfo.designation_bn || profile.designation_bn || 'উপ-সহকারী প্রকৌশলী'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Organization' : 'প্রতিষ্ঠান'}</span>
                  <span className="font-medium text-slate-200 text-right">
                    {profInfo.organization || profile.organization || 'Power Grid Company of Bangladesh PLC (PGCB)'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Department' : 'দপ্তর / শাখা'}</span>
                  <span className="font-medium text-slate-200 text-right">
                    {profInfo.department || profile.department || 'Grid Operations'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Diploma Institution' : 'ডিপ্লোমা প্রতিষ্ঠান'}</span>
                  <span className="font-medium text-slate-200 text-right">
                    {profInfo.diploma_institution || profile.diploma_institution || 'Dhaka Polytechnic Institute'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Passing Year' : 'পাসের সন'}</span>
                  <span className="font-mono text-slate-200 text-right">
                    {profInfo.graduation_year || profile.graduation_year || '2016'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">{isEn ? 'Experience' : 'অভিজ্ঞতা'}</span>
                  <span className="font-semibold text-emerald-400 text-right">
                    {profInfo.years_of_experience || profile.years_of_experience || '8'}{' '}
                    {isEn ? 'Years' : 'বছর'}
                  </span>
                </div>
              </div>
            </div>

            {/* Card 3: Contact Information */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="font-extrabold text-base text-white flex items-center gap-2">
                  <Phone size={18} className="text-emerald-400" />
                  <span>{isEn ? 'Contact Information' : 'যোগাযোগের তথ্য'}</span>
                </h3>
                <Link
                  href="/member/profile/edit"
                  className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                >
                  <Edit3 size={13} />
                  <span>{isEn ? 'Edit' : 'সম্পাদনা'}</span>
                </Link>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Official Email' : 'অফিসিয়াল ইমেইল'}</span>
                  <span className="font-mono text-white text-right">{cInfo.email || profile.email || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Mobile Number' : 'মোবাইল নম্বর'}</span>
                  <span className="font-mono font-semibold text-white text-right">{cInfo.phone || profile.phone || '—'}</span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Alternate Phone' : 'বিকল্প ফোন নম্বর'}</span>
                  <span className="font-mono text-slate-300 text-right">
                    {cInfo.alternate_phone || profile.alternate_phone || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Present Address' : 'বর্তমান ঠিকানা'}</span>
                  <span className="font-medium text-slate-200 text-right max-w-[200px] truncate">
                    {cInfo.current_address || profile.current_address || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Permanent Address' : 'স্থায়ী ঠিকানা'}</span>
                  <span className="font-medium text-slate-200 text-right max-w-[200px] truncate">
                    {cInfo.permanent_address || profile.permanent_address || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">{isEn ? 'Grid Circle' : 'গ্রিড সার্কেল'}</span>
                  <span className="font-bold text-emerald-400 text-right">
                    {cInfo.circle_en || profile.circle_en || 'Dhaka Grid Circle'}
                  </span>
                </div>
              </div>
            </div>

            {/* Card 4: Emergency Contact */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4 hover:border-slate-700 transition-colors">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="font-extrabold text-base text-white flex items-center gap-2">
                  <HeartPulse size={18} className="text-rose-400" />
                  <span>{isEn ? 'Emergency Contact' : 'জরুরি যোগাযোগ'}</span>
                </h3>
                <Link
                  href="/member/profile/edit"
                  className="text-xs font-bold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                >
                  <Edit3 size={13} />
                  <span>{isEn ? 'Edit' : 'সম্পাদনা'}</span>
                </Link>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Contact Person Name' : 'যোগাযোগকারীর নাম'}</span>
                  <span className="font-bold text-white text-right">
                    {eContact.name || profile.emergency_contact_name || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Relationship' : 'সম্পর্ক'}</span>
                  <span className="font-medium text-slate-200 text-right">
                    {eContact.relationship || profile.emergency_contact_relationship || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/50">
                  <span className="text-slate-400">{isEn ? 'Emergency Phone Number' : 'জরুরি ফোন নম্বর'}</span>
                  <span className="font-mono font-bold text-rose-300 text-right">
                    {eContact.phone || profile.emergency_contact_phone || '—'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">{isEn ? 'Contact Address' : 'ঠিকানা'}</span>
                  <span className="font-medium text-slate-200 text-right max-w-[200px] truncate">
                    {eContact.address || profile.emergency_contact_address || '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Verification Badge Modal */}
      {selectedBadge && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck size={20} className="text-emerald-400" />
                <h3 className="font-bold text-base text-white capitalize">
                  {selectedBadge.field} {isEn ? 'Verification' : 'যাচাইকরণ'}
                </h3>
              </div>
              <button
                onClick={() => setSelectedBadge(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{isEn ? 'Current Status' : 'বর্তমান স্থিতি'}</span>
                <span
                  className={`px-2.5 py-0.5 rounded-full font-bold ${
                    selectedBadge.status === 'VERIFIED'
                      ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300'
                      : 'bg-amber-500/15 border border-amber-500/30 text-amber-300'
                  }`}
                >
                  {isEn ? selectedBadge.label : selectedBadge.label_bn || selectedBadge.label}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-300 leading-relaxed">
                {isEn ? selectedBadge.description : selectedBadge.description_bn || selectedBadge.description}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedBadge(null)}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-colors"
              >
                {isEn ? 'Close' : 'বন্ধ করুন'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
