'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  Clock,
  Calendar,
  CheckCircle2,
  RefreshCw,
  CreditCard,
  Award,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  MapPin,
  Tag,
  History,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MembershipSummary, MembershipHistoryItem } from '@/lib/api/types';
import { MemberLayout } from '@/components/member/MemberLayout';

export default function MembershipCenterPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<MembershipSummary | null>(null);
  const [history, setHistory] = useState<MembershipHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('en');

  const isEn = lang === 'en';

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const sum = await api.getMembershipSummary();
      setSummary(sum);
      const histRes = await api.getMembershipHistory();
      setHistory(histRes.items || []);
    } catch (err: any) {
      if (err?.status === 401) {
        router.push('/login?redirect=/member/membership');
        return;
      }
      setError(err?.message || 'Failed to load membership details.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-500',
          label: isEn ? 'ACTIVE' : 'সক্রিয়',
          icon: CheckCircle2,
        };
      case 'EXPIRING_SOON':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          dot: 'bg-amber-500',
          label: isEn ? 'EXPIRING SOON' : 'শীঘ্রই মেয়াদোত্তীর্ণ',
          icon: Clock,
        };
      case 'EXPIRED':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          dot: 'bg-rose-500',
          label: isEn ? 'EXPIRED' : 'মেয়াদোত্তীর্ণ',
          icon: AlertCircle,
        };
      case 'SUSPENDED':
        return {
          bg: 'bg-red-500/20 text-red-400 border-red-500/40',
          dot: 'bg-red-500',
          label: isEn ? 'SUSPENDED' : 'স্থগিত',
          icon: AlertTriangle,
        };
      case 'PENDING':
      case 'UNDER_REVIEW':
      case 'DOCUMENTS_REQUIRED':
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          dot: 'bg-blue-500',
          label: isEn ? 'APPLICATION IN REVIEW' : 'আবেদন পর্যালোচনায়',
          icon: Clock,
        };
      default:
        return {
          bg: 'bg-slate-500/10 text-slate-300 border-slate-700',
          dot: 'bg-slate-400',
          label: status,
          icon: ShieldCheck,
        };
    }
  };

  const status = summary?.status || 'PENDING';
  const badge = getStatusBadge(status);
  const StatusIcon = badge.icon;
  const daysRemaining = summary?.days_remaining;

  return (
    <MemberLayout lang={lang} onLangChange={setLang}>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header Breadcrumbs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 mb-1">
              <Link href="/member/dashboard" className="hover:text-emerald-400 transition-colors">
                {isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}
              </Link>
              <ChevronRight size={14} />
              <span className="text-emerald-400">{isEn ? 'Membership' : 'সদস্যপদ'}</span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-black text-white tracking-tight">
              {isEn ? 'MY MEMBERSHIP' : 'আমার সদস্যপদ'}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={loadData}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
              title={isEn ? 'Refresh' : 'রিফ্রেশ'}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            </button>
            <Link
              href="/member/membership/history"
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-bold text-slate-200 border border-slate-700/60 transition-colors"
            >
              <History size={15} className="text-emerald-400" />
              <span>{isEn ? 'Full History' : 'সম্পূর্ণ হিস্ট্রি'}</span>
            </Link>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
            <AlertCircle size={20} className="shrink-0 text-rose-400" />
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
            <p className="text-slate-400 font-medium text-sm">
              {isEn ? 'Loading membership status...' : 'সদস্যপদের তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        ) : summary ? (
          <>
            {/* Status Alert Banner if Suspended or Expired or Expiring Soon */}
            {status === 'SUSPENDED' && (
              <div className="p-5 rounded-2xl bg-red-950/40 border border-red-500/40 text-red-200 flex items-start gap-4 shadow-lg shadow-red-950/20">
                <AlertTriangle size={24} className="shrink-0 text-red-400 mt-0.5" />
                <div>
                  <h3 className="font-bold text-base text-red-300">
                    {isEn ? 'Membership Suspended' : 'সদস্যপদ স্থগিত করা হয়েছে'}
                  </h3>
                  <p className="text-xs text-red-200/90 mt-1 leading-relaxed">
                    {summary.renewal_blocked_reason ||
                      (isEn
                        ? 'Your membership is currently suspended by administration. Renewal and certificates are temporarily locked.'
                        : 'আপনার সদস্যপদ বর্তমানে স্থগিত রাখা হয়েছে। বিস্তারিত তথ্যের জন্য কেন্দ্রীয় বা সার্কেল কমিটির সাথে যোগাযোগ করুন।')}
                  </p>
                </div>
              </div>
            )}

            {status === 'EXPIRING_SOON' && (
              <div className="p-5 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-amber-200 flex items-start justify-between gap-4 shadow-lg shadow-amber-950/20">
                <div className="flex items-start gap-3">
                  <Clock size={22} className="shrink-0 text-amber-400 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-sm text-amber-300">
                      {isEn ? 'Membership Expiring Soon' : 'সদস্যপদের মেয়াদ শীঘ্রই শেষ হচ্ছে'}
                    </h3>
                    <p className="text-xs text-amber-200/90 mt-1">
                      {isEn
                        ? `Your membership will expire in ${daysRemaining ?? 0} days. Renew now to avoid interruption of services.`
                        : `আপনার সদস্যপদের মেয়াদ আর মাত্র ${daysRemaining ?? 0} দিন বাকি রয়েছে। এখনই নবায়ন করুন।`}
                    </p>
                  </div>
                </div>
                <Link
                  href="/member/membership/renew"
                  className="shrink-0 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition-colors shadow-md shadow-amber-500/20"
                >
                  {isEn ? 'Renew Now' : 'এখনই নবায়ন করুন'}
                </Link>
              </div>
            )}

            {status === 'EXPIRED' && (
              <div className="p-5 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-200 flex items-start justify-between gap-4 shadow-lg shadow-rose-950/20">
                <div className="flex items-start gap-3">
                  <AlertCircle size={22} className="shrink-0 text-rose-400 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-sm text-rose-300">
                      {isEn ? 'Membership Expired' : 'সদস্যপদের মেয়াদ শেষ হয়েছে'}
                    </h3>
                    <p className="text-xs text-rose-200/90 mt-1">
                      {isEn
                        ? 'Your membership validity has expired. Please renew to regain access to member privileges and certificates.'
                        : 'আপনার সদস্যপদের মেয়াদ উত্তীর্ণ হয়েছে। সব সুযোগ-সুবিধা পুনরায় সক্রিয় করতে নবায়ন সম্পন্ন করুন।'}
                    </p>
                  </div>
                </div>
                <Link
                  href="/member/membership/renew"
                  className="shrink-0 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition-colors shadow-md shadow-rose-600/20"
                >
                  {isEn ? 'Renew Membership' : 'সদস্যপদ নবায়ন'}
                </Link>
              </div>
            )}

            {/* Main Membership Card */}
            <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 lg:p-8 backdrop-blur-md shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

              {/* Status Pill Header */}
              <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800/80">
                <div className="flex items-center gap-3">
                  <div className={`px-4 py-1.5 rounded-full border text-xs font-black tracking-wide flex items-center gap-2 ${badge.bg}`}>
                    <span className={`w-2.5 h-2.5 rounded-full ${badge.dot} animate-pulse`} />
                    <span>{badge.label}</span>
                  </div>
                  {summary.membership_type && (
                    <span className="text-xs font-bold text-slate-400 bg-slate-800/60 px-3 py-1 rounded-full border border-slate-700/60">
                      {isEn ? summary.membership_type_label_en || summary.membership_type : summary.membership_type_label_bn || summary.membership_type}
                    </span>
                  )}
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-slate-400 block">
                    {isEn ? 'MEMBERSHIP ID' : 'মেম্বারশিপ আইডি'}
                  </span>
                  <span className="text-lg font-black text-white font-mono tracking-wider">
                    {summary.membership_id || 'PENDING'}
                  </span>
                </div>
              </div>

              {/* Attributes Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 py-6 border-b border-slate-800/80">
                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">
                    {isEn ? 'Membership Type' : 'সদস্যপদের ধরন'}
                  </span>
                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-sm">
                    <Tag size={15} className="text-emerald-400" />
                    <span>{isEn ? summary.membership_type_label_en || summary.membership_type || 'Professional' : summary.membership_type_label_bn || 'প্রফেশনাল'}</span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">
                    {isEn ? 'Grid Circle' : 'গ্রিড সার্কেল'}
                  </span>
                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-sm">
                    <MapPin size={15} className="text-emerald-400" />
                    <span>{isEn ? summary.circle_en || summary.circle || 'Dhaka Circle' : summary.circle_bn || 'ঢাকা সার্কেল'}</span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">
                    {isEn ? 'Joined Date' : 'যোগদানের তারিখ'}
                  </span>
                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-sm">
                    <Calendar size={15} className="text-emerald-400" />
                    <span>{summary.joined_at || '—'}</span>
                  </div>
                </div>

                <div>
                  <span className="text-xs font-semibold text-slate-400 block mb-1">
                    {isEn ? 'Valid Until' : 'মেয়াদ উত্তীর্ণের তারিখ'}
                  </span>
                  <div className="flex items-center gap-1.5 font-bold text-slate-200 text-sm">
                    <Clock size={15} className="text-emerald-400" />
                    <span>{summary.valid_until || '—'}</span>
                  </div>
                </div>
              </div>

              {/* Validity Progress Section */}
              <div className="pt-6 pb-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300">
                    {isEn ? 'Membership Validity' : 'সদস্যপদের বৈধতা'}
                  </span>
                  <span className="text-xs font-black text-emerald-400 font-mono">
                    {daysRemaining !== null && daysRemaining !== undefined
                      ? daysRemaining >= 0
                        ? isEn
                          ? `${daysRemaining} days remaining`
                          : `${daysRemaining} দিন অবশিষ্ট`
                        : isEn
                        ? `Expired ${Math.abs(daysRemaining)} days ago`
                        : `${Math.abs(daysRemaining)} দিন পূর্বে মেয়াদোত্তীর্ণ`
                      : '—'}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-800 rounded-full h-3 p-0.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      status === 'EXPIRED'
                        ? 'bg-rose-500 w-full'
                        : status === 'EXPIRING_SOON'
                        ? 'bg-amber-500'
                        : 'bg-gradient-to-r from-emerald-600 to-teal-400'
                    }`}
                    style={{
                      width: `${Math.min(100, Math.max(5, summary.validity_progress_percentage || 0))}%`,
                    }}
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap items-center gap-3 pt-6 mt-4 border-t border-slate-800/60">
                  {summary.can_renew ? (
                    <Link
                      href="/member/membership/renew"
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm transition-colors shadow-lg shadow-emerald-600/20"
                    >
                      <RefreshCw size={16} />
                      <span>{isEn ? 'Renew Membership' : 'সদস্যপদ নবায়ন'}</span>
                    </Link>
                  ) : (
                    <button
                      type="button"
                      disabled
                      title={summary.renewal_blocked_reason || 'Renewal is currently unavailable'}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 text-slate-500 font-bold text-sm cursor-not-allowed border border-slate-700/40"
                    >
                      <RefreshCw size={16} />
                      <span>{isEn ? 'Renew Membership' : 'সদস্যপদ নবায়ন'}</span>
                    </button>
                  )}

                  <Link
                    href="/portal/id-card"
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors border border-slate-700/60"
                  >
                    <CreditCard size={16} className="text-emerald-400" />
                    <span>{isEn ? 'Digital ID' : 'ডিজিটাল আইডি'}</span>
                  </Link>

                  <Link
                    href="/portal?tab=certificates"
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors border border-slate-700/60"
                  >
                    <Award size={16} className="text-emerald-400" />
                    <span>{isEn ? 'Certificate' : 'সনদপত্র'}</span>
                  </Link>
                </div>
              </div>
            </div>

            {/* Recent Membership History Timeline */}
            <div className="rounded-3xl bg-slate-900/60 border border-slate-800 p-6 lg:p-8 backdrop-blur-md shadow-xl">
              <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <History size={20} className="text-emerald-400" />
                  <h2 className="text-lg font-bold text-white tracking-tight">
                    {isEn ? 'Membership History' : 'সদস্যপদ হিস্ট্রি ও ট্র্যাকিং'}
                  </h2>
                </div>

                <Link
                  href="/member/membership/history"
                  className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors"
                >
                  <span>{isEn ? 'View All' : 'সবগুলো দেখুন'}</span>
                  <ArrowRight size={14} />
                </Link>
              </div>

              {history.length === 0 ? (
                <p className="text-slate-500 text-sm text-center py-6">
                  {isEn ? 'No history records found.' : 'কোন হিস্ট্রি পাওয়া যায়নি।'}
                </p>
              ) : (
                <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {history.slice(0, 4).map((item, idx) => (
                    <div key={item.id || idx} className="relative group">
                      {/* Timeline Dot */}
                      <div className="absolute -left-[19px] top-1.5 w-3 h-3 rounded-full bg-emerald-500 ring-4 ring-slate-950" />

                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-black text-slate-400 font-mono">
                            {item.year || item.date}
                          </span>
                          <span className="text-slate-600">─────</span>
                          <span className="text-sm font-bold text-slate-100">
                            {isEn ? item.action_label_en : item.action_label_bn}
                          </span>
                        </div>

                        <div className="flex items-center gap-3">
                          {item.new_validity && item.new_validity !== '—' && (
                            <span className="text-xs text-slate-400">
                              {isEn ? `Valid till: ${item.new_validity}` : `মেয়াদ: ${item.new_validity}`}
                            </span>
                          )}
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-emerald-400 border border-slate-700/60">
                            {item.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </MemberLayout>
  );
}
