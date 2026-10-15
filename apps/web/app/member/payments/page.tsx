'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  CreditCard,
  CheckCircle2,
  Clock,
  XCircle,
  AlertCircle,
  RefreshCw,
  FileText,
  Download,
  ExternalLink,
  ArrowRight,
  ShieldCheck,
  Search,
  Filter,
  RotateCcw,
  Receipt,
  HelpCircle,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { PaymentSummary, PaymentTransactionItem } from '@/lib/api/types';

export default function MemberPaymentsPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<PaymentSummary | null>(null);
  const [activeTab, setActiveTab] = useState<'ALL' | 'PAID' | 'PENDING' | 'FAILED' | 'REFUNDED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const isEn = lang === 'en';

  const loadPaymentSummary = async (tab = activeTab) => {
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getPaymentSummary(tab);
      setSummary(data);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load payment history and financial records'
            : 'পেমেন্টের ইতিহাস ও আর্থিক বিবরণী লোড করা সম্ভব হয়নি')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPaymentSummary(activeTab);
  }, [activeTab]);

  const transactions = summary?.transactions || [];

  const filteredTransactions = transactions.filter((t) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      t.transaction_ref.toLowerCase().includes(q) ||
      (t.receipt_no && t.receipt_no.toLowerCase().includes(q)) ||
      (t.purpose_label_en && t.purpose_label_en.toLowerCase().includes(q)) ||
      (t.purpose_label_bn && t.purpose_label_bn.toLowerCase().includes(q)) ||
      (t.provider && t.provider.toLowerCase().includes(q))
    );
  });

  const getStatusBadge = (status: string, labelEn?: string, labelBn?: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'PAID' || s === 'SUCCESS' || s === 'COMPLETED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          {isEn ? labelEn || 'Paid' : labelBn || 'পরিশোধিত'}
        </span>
      );
    }
    if (s === 'PENDING' || s === 'INITIATED' || s === 'PROCESSING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <Clock className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
          {isEn ? labelEn || 'Pending' : labelBn || 'অপেক্ষমাণ'}
        </span>
      );
    }
    if (s === 'REFUNDED' || s === 'PARTIALLY_REFUNDED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200">
          <RotateCcw className="w-3.5 h-3.5 text-purple-600" />
          {isEn ? labelEn || 'Refunded' : labelBn || 'ফেরত প্রদান'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
        <XCircle className="w-3.5 h-3.5 text-rose-600" />
        {isEn ? labelEn || 'Failed' : labelBn || 'ব্যর্থ'}
      </span>
    );
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <MemberLayout
      title={isEn ? 'My Payments & Receipts' : 'আমার পেমেন্ট ও রসিদসমূহ'}
      lang={lang}
      onLangChange={setLang}
      activeTab="payments"
    >
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div>
            <div className="flex items-center gap-2 text-primary-700 text-xs font-semibold tracking-wider uppercase mb-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              {isEn ? 'PGCB Core Financial Registry' : 'পিজিসিবি কেন্দ্রীয় আর্থিক রেজিস্ট্রি'}
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {isEn ? 'My Payments & Receipts' : 'আমার পেমেন্ট ও রসিদসমূহ'}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              {isEn
                ? 'Official records of membership renewals, application fees, event registrations, and digital receipts.'
                : 'সদস্যপদ নবায়ন, আবেদন ফি, ইভেন্ট নিবন্ধন এবং অফিসিয়াল ডিজিটাল রসিদের বিস্তারিত বিবরণ।'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => loadPaymentSummary(activeTab)}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition"
              title={isEn ? 'Refresh' : 'রিফ্রেশ'}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-primary-600' : ''}`} />
              <span>{isEn ? 'Refresh' : 'হালনাগাদ'}</span>
            </button>
            <Link
              href="/member/membership/renew"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-xl shadow-sm transition"
            >
              <CreditCard className="w-4 h-4" />
              <span>{isEn ? 'Renew Membership' : 'সদস্যপদ নবায়ন করুন'}</span>
            </Link>
          </div>
        </div>

        {/* Financial Summary Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Total Paid */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
                {isEn ? 'TOTAL PAID' : 'মোট পরিশোধিত'}
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                ৳
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900 mt-2">
              {summary ? summary.total_paid_formatted : '৳0'}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isEn ? 'Verified successful transactions' : 'যাচাইকৃত সফল পেমেন্ট'}
            </p>
          </div>

          {/* Successful Count */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
                {isEn ? 'SUCCESSFUL' : 'সফল পেমেন্ট'}
              </span>
              <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900 mt-2">
              {summary ? summary.successful_count : 0}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isEn ? 'Receipts available' : 'রসিদ প্রাপ্তিযোগ্য'}
            </p>
          </div>

          {/* Pending Count */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
                {isEn ? 'PENDING' : 'অপেক্ষমাণ'}
              </span>
              <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <Clock className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900 mt-2">
              {summary ? summary.pending_count : 0}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isEn ? 'Awaiting gateway / review' : 'গেটওয়ে বা রিভিউ অপেক্ষমাণ'}
            </p>
          </div>

          {/* Failed Count */}
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-slate-500 uppercase">
                {isEn ? 'FAILED / CANCELLED' : 'ব্যর্থ / বাতিল'}
              </span>
              <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                <XCircle className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-extrabold text-slate-900 mt-2">
              {summary ? summary.failed_count : 0}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {isEn ? 'Uncompleted checkouts' : 'অসম্পূর্ণ চেকআউট'}
            </p>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 flex items-center gap-3 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Main Content Box: Filters & Transaction History Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          {/* Header & Filter Tabs */}
          <div className="p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Status Tabs */}
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: 'ALL', labelEn: 'All', labelBn: 'সকল' },
                { id: 'PAID', labelEn: 'Paid', labelBn: 'পরিশোধিত' },
                { id: 'PENDING', labelEn: 'Pending', labelBn: 'অপেক্ষমাণ' },
                { id: 'FAILED', labelEn: 'Failed', labelBn: 'ব্যর্থ' },
                { id: 'REFUNDED', labelEn: 'Refunded', labelBn: 'ফেরত' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
                    activeTab === tab.id
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {isEn ? tab.labelEn : tab.labelBn}
                </button>
              ))}
            </div>

            {/* Search Box */}
            <div className="relative min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={isEn ? 'Search by reference or receipt...' : 'রেফারেন্স বা রসিদ দিয়ে খুঁজুন...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 transition"
              />
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-primary-500 mb-3" />
              <p className="text-sm font-medium">{isEn ? 'Loading payment records...' : 'পেমেন্ট রেকর্ড লোড হচ্ছে...'}</p>
            </div>
          ) : filteredTransactions.length === 0 ? (
            <div className="py-16 text-center px-4">
              <div className="w-14 h-14 bg-slate-50 rounded-2xl flex items-center justify-center mx-auto mb-3 text-slate-400">
                <Receipt className="w-7 h-7" />
              </div>
              <h3 className="text-base font-semibold text-slate-800">
                {isEn ? 'No payment records found' : 'কোনো পেমেন্ট রেকর্ড পাওয়া যায়নি'}
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-5">
                {isEn
                  ? 'There are no transactions matching the current status filter. Initiate a membership renewal or pay application fees to see records here.'
                  : 'বর্তমান ফিল্টারের সাথে মিলে এমন কোনো লেনদেন নেই। সদস্যপদ নবায়ন বা ফি পরিশোধ করলে এখানে রেকর্ড দেখতে পাবেন।'}
              </p>
              <Link
                href="/member/membership/renew"
                className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-xl transition shadow-sm"
              >
                <CreditCard className="w-4 h-4" />
                <span>{isEn ? 'Renew Membership' : 'সদস্যপদ নবায়ন করুন'}</span>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                    <th className="py-3 px-4">{isEn ? 'Date' : 'তারিখ'}</th>
                    <th className="py-3 px-4">{isEn ? 'Description & Reference' : 'বিবরণ ও রেফারেন্স'}</th>
                    <th className="py-3 px-4">{isEn ? 'Amount' : 'পরিমাণ'}</th>
                    <th className="py-3 px-4">{isEn ? 'Gateway' : 'গেটওয়ে'}</th>
                    <th className="py-3 px-4">{isEn ? 'Status' : 'অবস্থা'}</th>
                    <th className="py-3 px-4 text-right">{isEn ? 'Actions' : 'পদক্ষেপ'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredTransactions.map((tx) => {
                    const isPaid = tx.status === 'PAID' || tx.status === 'SUCCESS' || tx.status === 'COMPLETED';
                    const isPending = tx.status === 'PENDING' || tx.status === 'INITIATED' || tx.status === 'PROCESSING';

                    return (
                      <tr key={tx.id} className="hover:bg-slate-50/70 transition">
                        {/* Date */}
                        <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                          {formatDate(tx.paid_at || tx.created_at)}
                        </td>

                        {/* Description & Reference */}
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-900">
                            {isEn ? tx.purpose_label_en : tx.purpose_label_bn}
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="font-mono text-[11px] text-slate-400">{tx.transaction_ref}</span>
                            {tx.receipt_no && (
                              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                                {tx.receipt_no}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Amount */}
                        <td className="py-3.5 px-4 font-bold text-slate-900 whitespace-nowrap">
                          {tx.amount_formatted}
                        </td>

                        {/* Gateway */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                            {tx.provider}
                          </span>
                        </td>

                        {/* Status */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          {getStatusBadge(tx.status, tx.status_label_en, tx.status_label_bn)}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <div className="inline-flex items-center gap-2">
                            {/* View Detail */}
                            <Link
                              href={`/member/payments/${tx.id}`}
                              className="px-2.5 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                            >
                              {isEn ? 'View' : 'বিবরণ'}
                            </Link>

                            {/* Official Digital Receipt if Paid */}
                            {isPaid && (
                              <>
                                <Link
                                  href={`/member/payments/${tx.id}/receipt`}
                                  className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 rounded-lg transition"
                                >
                                  <Receipt className="w-3.5 h-3.5" />
                                  <span>{isEn ? 'Receipt' : 'রসিদ'}</span>
                                </Link>

                                <a
                                  href={`/api/v1/member/payments/${tx.id}/receipt.pdf`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
                                  title={isEn ? 'Download PDF Receipt' : 'পিডিএফ রসিদ ডাউনলোড'}
                                >
                                  <Download className="w-3.5 h-3.5" />
                                </a>
                              </>
                            )}

                            {/* Pay Now if Pending */}
                            {isPending && (
                              <Link
                                href={`/member/payments/${tx.id}`}
                                className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg shadow-sm transition"
                              >
                                <span>{isEn ? 'Pay Now' : 'পরিশোধ করুন'}</span>
                                <ArrowRight className="w-3 h-3" />
                              </Link>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Security & Financial Notice */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-100/60 text-emerald-700 flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-semibold text-slate-700 block">
                {isEn ? 'Cryptographically Verified Digital Receipts' : 'ডিজিটালি যাচাইকৃত সরকারি রসিদ'}
              </span>
              <span>
                {isEn
                  ? 'All receipts issued by PGCB carry a unique QR verification code linked directly to the live registry.'
                  : 'পিজিসিবি কর্তৃক ইস্যুকৃত সকল রসিদে রয়েছে ইউনিক কিউআর যাচাইকরণ কোড যা সরাসরি ডাটাবেজের সাথে সংযুক্ত।'}
              </span>
            </div>
          </div>
          <Link
            href="/portal?tab=ai"
            className="inline-flex items-center gap-1.5 text-primary-600 hover:text-primary-700 font-semibold whitespace-nowrap"
          >
            <HelpCircle className="w-4 h-4" />
            <span>{isEn ? 'Ask AI about payments' : 'পেমেন্ট সংক্রান্ত এআই সহায়তা'}</span>
          </Link>
        </div>
      </div>
    </MemberLayout>
  );
}
