'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  History,
  ChevronRight,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  CreditCard,
  Award,
  ExternalLink,
  ShieldCheck,
  Calendar,
  User,
  ArrowUpDown,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MembershipHistoryItem } from '@/lib/api/types';
import { MemberLayout } from '@/components/member/MemberLayout';

export default function MembershipHistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<MembershipHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [search, setSearch] = useState('');
  const [filterAction, setFilterAction] = useState<string>('ALL');

  const isEn = lang === 'en';

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getMembershipHistory();
      setHistory(res.items || []);
    } catch (err: any) {
      if (err?.status === 401) {
        router.push('/login?redirect=/member/membership/history');
        return;
      }
      setError(err?.message || 'Failed to load membership history.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const filteredHistory = history.filter((item) => {
    const matchesSearch =
      !search ||
      (item.reference || '').toLowerCase().includes(search.toLowerCase()) ||
      (item.action || '').toLowerCase().includes(search.toLowerCase()) ||
      (item.date || '').toLowerCase().includes(search.toLowerCase()) ||
      (item.performed_by || '').toLowerCase().includes(search.toLowerCase());

    const matchesFilter =
      filterAction === 'ALL' || item.action.toUpperCase() === filterAction.toUpperCase();

    return matchesSearch && matchesFilter;
  });

  const getActionBadge = (action: string) => {
    switch (action.toUpperCase()) {
      case 'RENEWAL':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: RefreshCw,
          label: isEn ? 'Renewal' : 'নবায়ন',
        };
      case 'CREATED':
      case 'ACTIVATED':
        return {
          bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
          icon: CheckCircle2,
          label: isEn ? 'Joined / Activated' : 'নিবন্ধন / সক্রিয়করণ',
        };
      case 'SUSPENDED':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          icon: AlertCircle,
          label: isEn ? 'Suspended' : 'স্থগিতকরণ',
        };
      default:
        return {
          bg: 'bg-slate-500/10 text-slate-300 border-slate-700',
          icon: History,
          label: action,
        };
    }
  };

  return (
    <MemberLayout lang={lang} onLangChange={setLang}>
      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Header Breadcrumbs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 mb-1">
              <Link href="/member/dashboard" className="hover:text-emerald-400 transition-colors">
                {isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}
              </Link>
              <ChevronRight size={14} />
              <Link href="/member/membership" className="hover:text-emerald-400 transition-colors">
                {isEn ? 'Membership' : 'সদস্যপদ'}
              </Link>
              <ChevronRight size={14} />
              <span className="text-emerald-400">{isEn ? 'History' : 'ইতিহাস'}</span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-black text-white tracking-tight">
              {isEn ? 'MEMBERSHIP LIFECYCLE AUDIT' : 'সদস্যপদ ইতিহাস ও অডিট'}
            </h1>
          </div>

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="self-start sm:self-auto p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
            title={isEn ? 'Refresh' : 'রিফ্রেশ'}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
            <AlertCircle size={20} className="shrink-0 text-rose-400" />
            <p>{error}</p>
          </div>
        )}

        {/* Filter and Search Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={17} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={isEn ? 'Search by reference, action, or date...' : 'রেফারেন্স, অ্যাকশন বা তারিখ দিয়ে খুঁজুন...'}
              className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter size={16} className="text-slate-400 shrink-0 hidden sm:block" />
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="bg-slate-900/80 border border-slate-800 rounded-xl px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500 transition-colors"
            >
              <option value="ALL">{isEn ? 'All Actions' : 'সকল কার্যক্রম'}</option>
              <option value="RENEWAL">{isEn ? 'Renewals' : 'নবায়ন'}</option>
              <option value="CREATED">{isEn ? 'Joined / Created' : 'সদস্যপদ সংযোজন'}</option>
              <option value="ACTIVATED">{isEn ? 'Activated' : 'সক্রিয়করণ'}</option>
              <option value="SUSPENDED">{isEn ? 'Suspended' : 'স্থগিতকরণ'}</option>
            </select>
          </div>
        </div>

        {/* Main Records Container */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
            <p className="text-slate-400 font-medium text-sm">
              {isEn ? 'Loading audit records...' : 'অডিট হিস্ট্রি লোড হচ্ছে...'}
            </p>
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="rounded-2xl bg-slate-900/50 border border-slate-800 p-12 text-center text-slate-400 text-sm">
            {isEn ? 'No membership history records match your search.' : 'কোন তথ্য পাওয়া যায়নি।'}
          </div>
        ) : (
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-xl">
            {/* Desktop Table View */}
            <div className="hidden lg:block overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 text-slate-400 font-bold uppercase tracking-wider text-[11px] border-b border-slate-700/60">
                  <tr>
                    <th className="px-5 py-3.5">{isEn ? 'Reference' : 'রেফারেন্স'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Date' : 'তারিখ'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Action' : 'কার্যক্রম'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Validity Period' : 'মেয়াদ পরিসীমা'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Status' : 'স্থিতি'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Linked Records' : 'যুক্ত রসিদ/সনদ'}</th>
                    <th className="px-4 py-3.5">{isEn ? 'Actor' : 'কর্তৃপক্ষ'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {filteredHistory.map((item) => {
                    const badge = getActionBadge(item.action);
                    const Icon = badge.icon;
                    return (
                      <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-4 font-mono font-bold text-white text-[13px]">
                          {item.reference || `PGCB-HIST-${item.id}`}
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap text-slate-300">
                          {item.date}
                        </td>
                        <td className="px-4 py-4">
                          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-bold ${badge.bg}`}>
                            <Icon size={13} />
                            <span>{isEn ? item.action_label_en : item.action_label_bn}</span>
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-1.5 text-slate-200">
                            <span className="text-slate-400">{item.old_validity || '—'}</span>
                            <span className="text-emerald-400">→</span>
                            <span className="font-bold text-white">{item.new_validity || '—'}</span>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-800 text-emerald-300 border border-slate-700/60">
                            {item.status}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex flex-col gap-1">
                            {item.payment_reference && (
                              <Link
                                href={`/portal?tab=payments`}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
                              >
                                <CreditCard size={12} />
                                <span>{item.payment_reference}</span>
                              </Link>
                            )}
                            {item.certificate_no && (
                              <Link
                                href={`/portal?tab=certificates`}
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-teal-400 hover:text-teal-300 transition-colors"
                              >
                                <Award size={12} />
                                <span>{item.certificate_no}</span>
                              </Link>
                            )}
                            {!item.payment_reference && !item.certificate_no && (
                              <span className="text-slate-600">—</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-slate-400 text-[11px]">
                          {item.performed_by || 'System'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Mobile Card View */}
            <div className="lg:hidden divide-y divide-slate-800">
              {filteredHistory.map((item) => {
                const badge = getActionBadge(item.action);
                const Icon = badge.icon;
                return (
                  <div key={item.id} className="p-4 space-y-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-mono font-bold text-white text-xs">
                        {item.reference || `PGCB-HIST-${item.id}`}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold ${badge.bg}`}>
                        <Icon size={12} />
                        <span>{isEn ? item.action_label_en : item.action_label_bn}</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block font-semibold">
                          {isEn ? 'Date' : 'তারিখ'}
                        </span>
                        <span className="text-slate-300">{item.date}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase block font-semibold">
                          {isEn ? 'New Validity' : 'নতুন মেয়াদ'}
                        </span>
                        <span className="text-slate-200 font-bold">{item.new_validity || '—'}</span>
                      </div>
                    </div>

                    {(item.payment_reference || item.certificate_no) && (
                      <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-3 text-xs">
                        {item.payment_reference && (
                          <Link
                            href="/portal?tab=payments"
                            className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300"
                          >
                            <CreditCard size={13} />
                            <span>{item.payment_reference}</span>
                          </Link>
                        )}
                        {item.certificate_no && (
                          <Link
                            href="/portal?tab=certificates"
                            className="inline-flex items-center gap-1 text-teal-400 hover:text-teal-300"
                          >
                            <Award size={13} />
                            <span>{item.certificate_no}</span>
                          </Link>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
