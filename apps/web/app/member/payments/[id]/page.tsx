'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
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
  ArrowLeft,
  ShieldCheck,
  Receipt,
  User,
  Calendar,
  Building,
  RotateCcw,
  QrCode,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';

export default function MemberPaymentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const paymentId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [payment, setPayment] = useState<any | null>(null);

  const isEn = lang === 'en';

  const loadPaymentDetail = async () => {
    if (!paymentId || isNaN(paymentId)) {
      setError(isEn ? 'Invalid payment transaction ID' : 'অকার্যকর পেমেন্ট ট্রানজেকশন আইডি');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getPaymentDetail(paymentId);
      setPayment(data);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load transaction details from authoritative registry'
            : 'পেমেন্ট ট্রানজেকশন বিবরণী লোড করা সম্ভব হয়নি')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPaymentDetail();
  }, [paymentId]);

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return isEn ? 'Not recorded yet' : 'রেকর্ড করা হয়নি';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const isPaid = payment?.status === 'PAID' || payment?.status === 'SUCCESS' || payment?.status === 'COMPLETED';
  const isPending = payment?.status === 'PENDING' || payment?.status === 'INITIATED' || payment?.status === 'PROCESSING';
  const isRefunded = payment?.status === 'REFUNDED' || payment?.status === 'PARTIALLY_REFUNDED';

  return (
    <MemberLayout
      title={isEn ? 'Transaction Details' : 'লেনদেনের বিস্তারিত তথ্য'}
      lang={lang}
      onLangChange={setLang}
      activeTab="payments"
    >
      <div className="space-y-6 max-w-4xl mx-auto pb-12">
        {/* Navigation Breadcrumbs & Back */}
        <div className="flex items-center justify-between">
          <Link
            href="/member/payments"
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-600 hover:text-primary-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Payment History' : 'পেমেন্ট ইতিহাসে ফিরে যান'}</span>
          </Link>
          <div className="flex items-center gap-2">
            <button
              onClick={loadPaymentDetail}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
              title={isEn ? 'Refresh' : 'রিফ্রেশ'}
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-primary-500' : ''}`} />
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-16 text-center shadow-sm">
            <RefreshCw className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">
              {isEn ? 'Loading transaction details...' : 'লেনদেনের তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-2xl flex items-start gap-4">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm">{isEn ? 'Unable to load transaction' : 'লেনদেন লোড করা যায়নি'}</h3>
              <p className="text-xs mt-1 text-rose-600">{error}</p>
              <Link
                href="/member/payments"
                className="inline-flex items-center gap-1.5 mt-3 text-xs font-semibold text-rose-800 underline"
              >
                <span>{isEn ? 'Return to payments' : 'পেমেন্ট তালিকায় ফিরুন'}</span>
              </Link>
            </div>
          </div>
        )}

        {/* Transaction Content */}
        {payment && !loading && (
          <div className="space-y-6">
            {/* Status Header Banner */}
            <div
              className={`p-6 rounded-2xl border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                isPaid
                  ? 'bg-emerald-50/70 border-emerald-200/80 text-emerald-900'
                  : isPending
                  ? 'bg-amber-50/70 border-amber-200/80 text-amber-900'
                  : isRefunded
                  ? 'bg-purple-50/70 border-purple-200/80 text-purple-900'
                  : 'bg-rose-50/70 border-rose-200/80 text-rose-900'
              }`}
            >
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-sm ${
                    isPaid
                      ? 'bg-emerald-600 text-white'
                      : isPending
                      ? 'bg-amber-600 text-white animate-pulse'
                      : isRefunded
                      ? 'bg-purple-600 text-white'
                      : 'bg-rose-600 text-white'
                  }`}
                >
                  {isPaid ? (
                    <CheckCircle2 className="w-6 h-6" />
                  ) : isPending ? (
                    <Clock className="w-6 h-6" />
                  ) : isRefunded ? (
                    <RotateCcw className="w-6 h-6" />
                  ) : (
                    <XCircle className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <div className="text-xs font-semibold tracking-wider uppercase opacity-80">
                    {isEn ? 'Transaction Status' : 'লেনদেনের অবস্থা'}
                  </div>
                  <h2 className="text-xl font-bold mt-0.5">
                    {isEn
                      ? payment.status_label_en || payment.status
                      : payment.status_label_bn || payment.status}
                  </h2>
                  <p className="text-xs opacity-75 mt-0.5">
                    {isPaid
                      ? isEn
                        ? 'Payment verified by payment gateway and officially recorded.'
                        : 'পেমেন্ট গেটওয়ে দ্বারা যাচাইকৃত এবং অফিশিয়াল রেজিস্ট্রিভুক্ত।'
                      : isPending
                      ? isEn
                        ? 'Payment has been initiated and is awaiting completion or bank reconciliation.'
                        : 'পেমেন্ট শুরু হয়েছে এবং সম্পন্ন হওয়া বা ব্যাংক যাচাইয়ের জন্য অপেক্ষমাণ।'
                      : isRefunded
                      ? isEn
                        ? 'Amount has been returned to the original payment method.'
                        : 'টাকা মূল পেমেন্ট মাধ্যমে ফেরত দেওয়া হয়েছে।'
                      : isEn
                      ? 'Payment attempt failed or was cancelled by user.'
                      : 'পেমেন্ট প্রচেষ্টা ব্যর্থ হয়েছে অথবা ব্যবহারকারী দ্বারা বাতিল করা হয়েছে।'}
                  </p>
                </div>
              </div>

              {/* Quick Action in banner */}
              <div className="flex items-center gap-2">
                {isPaid && (
                  <Link
                    href={`/member/payments/${payment.id}/receipt`}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-700 text-white hover:bg-emerald-800 shadow-sm transition whitespace-nowrap"
                  >
                    <Receipt className="w-4 h-4" />
                    <span>{isEn ? 'View Official Receipt' : 'অফিসিয়াল রসিদ দেখুন'}</span>
                  </Link>
                )}
                {isPending && (
                  <Link
                    href="/member/membership/renew"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-amber-700 text-white hover:bg-amber-800 shadow-sm transition whitespace-nowrap"
                  >
                    <CreditCard className="w-4 h-4" />
                    <span>{isEn ? 'Proceed with Payment' : 'পেমেন্ট সম্পন্ন করুন'}</span>
                  </Link>
                )}
              </div>
            </div>

            {/* Details Grid */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-sm space-y-6">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-3">
                {isEn ? 'Financial Metadata' : 'আর্থিক তথ্য বিবরণী'}
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                {/* Reference ID */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Transaction Reference' : 'লেনদেন রেফারেন্স নম্বর'}
                  </span>
                  <span className="font-mono text-sm font-semibold text-slate-800 mt-1 block">
                    {payment.transaction_ref || payment.reference}
                  </span>
                </div>

                {/* Receipt Number */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Official Receipt No' : 'অফিসিয়াল রসিদ নম্বর'}
                  </span>
                  {payment.receipt_no ? (
                    <span className="font-mono text-sm font-bold text-emerald-700 mt-1 block">
                      {payment.receipt_no}
                    </span>
                  ) : (
                    <span className="text-slate-400 italic mt-1 block">
                      {isEn ? 'Issued upon successful payment' : 'পেমেন্ট সফল হলে ইস্যু হবে'}
                    </span>
                  )}
                </div>

                {/* Purpose */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Purpose of Payment' : 'পেমেন্টের উদ্দেশ্য'}
                  </span>
                  <span className="font-semibold text-slate-900 mt-1 block text-sm">
                    {isEn ? payment.purpose_label_en || payment.purpose : payment.purpose_label_bn || payment.purpose}
                  </span>
                </div>

                {/* Amount */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Amount Paid' : 'পরিশোধিত টাকার পরিমাণ'}
                  </span>
                  <span className="font-extrabold text-slate-900 mt-1 block text-lg">
                    {payment.amount_formatted || `৳${payment.amount}`}
                  </span>
                </div>

                {/* Payment Gateway */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Payment Gateway / Channel' : 'পেমেন্ট চ্যানেল / গেটওয়ে'}
                  </span>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-800 font-semibold border border-slate-200">
                      {payment.provider || payment.gateway || 'ONLINE'}
                    </span>
                    {payment.provider_tran_id && (
                      <span className="font-mono text-slate-500 text-[11px]">
                        ID: {payment.provider_tran_id}
                      </span>
                    )}
                  </div>
                </div>

                {/* Creation Timestamp */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Initiated At' : 'শুরুর সময়'}
                  </span>
                  <span className="text-slate-700 font-medium mt-1 block">
                    {formatDate(payment.created_at)}
                  </span>
                </div>

                {/* Paid Timestamp */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Paid / Settled At' : 'পরিশোধের সময়'}
                  </span>
                  <span className="text-slate-700 font-medium mt-1 block">
                    {formatDate(payment.paid_at)}
                  </span>
                </div>

                {/* Membership Plan ID */}
                <div>
                  <span className="text-slate-400 block font-medium uppercase tracking-wider text-[10px]">
                    {isEn ? 'Associated Plan' : 'সদস্যপদ প্ল্যান'}
                  </span>
                  <span className="text-slate-700 font-medium mt-1 block">
                    {payment.membership_plan_id || 'GENERAL'}
                  </span>
                </div>
              </div>

              {/* Action Buttons row */}
              <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center gap-3">
                {isPaid && (
                  <>
                    <Link
                      href={`/member/payments/${payment.id}/receipt`}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm transition"
                    >
                      <Receipt className="w-4 h-4" />
                      <span>{isEn ? 'Open Digital Receipt' : 'ডিজিটাল রসিদ খুলুন'}</span>
                    </Link>

                    <a
                      href={`/api/v1/member/payments/${payment.id}/receipt.pdf`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                    >
                      <Download className="w-4 h-4" />
                      <span>{isEn ? 'Download PDF' : 'পিডিএফ ডাউনলোড'}</span>
                    </a>

                    <Link
                      href={`/verify/payment/${encodeURIComponent(payment.receipt_no || payment.transaction_ref)}`}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-100 text-slate-700 hover:bg-slate-200 transition"
                    >
                      <QrCode className="w-4 h-4" />
                      <span>{isEn ? 'Public Verification' : 'পাবলিক ভেরিফিকেশন'}</span>
                    </Link>
                  </>
                )}

                <Link
                  href="/member/payments"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium text-slate-500 hover:text-slate-700 transition ml-auto"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>{isEn ? 'Back to all payments' : 'সকল পেমেন্টে ফিরুন'}</span>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
