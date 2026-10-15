'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Calendar,
  Lock,
  Receipt,
  CreditCard,
  Building2,
  ArrowRight,
} from 'lucide-react';
import { membersApi } from '@/lib/api/members';

export default function PublicPaymentReceiptVerifyPage() {
  const params = useParams();
  const reference = String(params?.reference || '');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('bn');

  const isEn = lang === 'en';

  useEffect(() => {
    async function verify() {
      if (!reference) return;
      try {
        setLoading(true);
        setError(null);
        const res = await membersApi.verifyPaymentPublic(reference);
        setData(res);
      } catch (err: any) {
        setError(
          err?.message ||
            (isEn
              ? 'Payment receipt verification record not found in the authoritative registry.'
              : 'কেন্দ্রীয় রেজিস্ট্রিতে এই পেমেন্ট রসিদের কোনো যাচাইকরণ রেকর্ড পাওয়া যায়নি।')
        );
      } finally {
        setLoading(false);
      }
    }
    verify();
  }, [reference]);

  const isValid = data?.is_valid === true && (data?.status === 'VALID' || data?.status === 'PAID');

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
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

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between p-4 sm:p-6 font-sans">
      <div className="max-w-xl w-full mx-auto my-auto space-y-6">
        {/* Language switch */}
        <div className="flex justify-end">
          <button
            onClick={() => setLang(lang === 'en' ? 'bn' : 'en')}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 shadow-sm transition"
          >
            {isEn ? 'বাংলা সংস্করণ' : 'English Version'}
          </button>
        </div>

        {/* Institution Brand */}
        <div className="text-center space-y-1">
          <div className="inline-flex p-3 bg-primary-700 text-white rounded-2xl shadow-md mb-2">
            <Receipt className="w-8 h-8" />
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            {isEn ? 'Power Grid Company of Bangladesh PLC' : 'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি'}
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            {isEn
              ? 'Institutional Financial Registry & Official Receipt Verification'
              : 'প্রাতিষ্ঠানিক কেন্দ্রীয় আর্থিক রেজিস্ট্রি ও পেমেন্ট রসিদ সত্যতা যাচাই'}
          </p>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
            <RefreshCw className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-600">
              {isEn ? 'Verifying payment authenticity against authoritative registry...' : 'রেজিস্ট্রি থেকে পেমেন্টের সত্যতা যাচাই করা হচ্ছে...'}
            </p>
          </div>
        ) : error || !data || !isValid ? (
          <div className="bg-white rounded-2xl border border-rose-200 p-8 text-center shadow-sm space-y-3">
            <div className="w-14 h-14 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto">
              <XCircle className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-rose-900">
              {isEn ? 'Invalid / Unverified Payment Receipt' : 'অযাচাইকৃত বা অকার্যকর পেমেন্ট রসিদ'}
            </h2>
            <p className="text-xs text-slate-600 max-w-sm mx-auto">
              {error ||
                (isEn
                  ? 'The provided receipt number or transaction reference does not correspond to a verified financial transaction in our registry.'
                  : 'প্রদত্ত রসিদ নম্বর বা ট্রানজেকশন রেফারেন্সের অনুকূলে আমাদের রেজিস্ট্রিতে কোনো যাচাইকৃত পেমেন্ট রেকর্ড পাওয়া যায়নি।')}
            </p>
            <div className="pt-2 text-[11px] text-slate-400 font-mono">
              Ref: {reference}
            </div>
            <div className="pt-3">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-700 hover:text-primary-800"
              >
                <span>{isEn ? 'Go to Member Portal' : 'সদস্য পোর্টালে যান'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
            {/* Status Header Banner */}
            <div className="bg-emerald-600 p-6 text-white text-center space-y-1">
              <div className="w-12 h-12 bg-white/20 backdrop-blur rounded-full flex items-center justify-center mx-auto mb-1">
                <CheckCircle2 className="w-7 h-7 text-white" />
              </div>
              <h2 className="text-lg font-bold tracking-tight">
                {isEn ? 'Officially Verified & Authentic Receipt' : 'অফিসিয়ালি যাচাইকৃত ও বৈধ রসিদ'}
              </h2>
              <p className="text-xs text-emerald-100">
                {isEn
                  ? 'Confirmed live against the PGCB Core Financial Registry'
                  : 'পিজিসিবি কেন্দ্রীয় আর্থিক রেজিস্ট্রি থেকে সরাসরি নিশ্চিতকৃত'}
              </p>
            </div>

            {/* Receipt Summary Grid */}
            <div className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4 pb-4 border-b border-slate-100">
                <div>
                  <span className="text-slate-400 block font-medium uppercase text-[10px] tracking-wider">
                    {isEn ? 'Receipt Number' : 'রসিদ নম্বর'}
                  </span>
                  <span className="font-mono font-bold text-slate-900 text-sm mt-0.5 block">
                    {data.receipt_no}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block font-medium uppercase text-[10px] tracking-wider">
                    {isEn ? 'Amount Paid' : 'পরিশোধিত টাকার পরিমাণ'}
                  </span>
                  <span className="font-mono font-extrabold text-emerald-700 text-base mt-0.5 block">
                    {data.amount_formatted || `৳${data.amount}`}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">{isEn ? 'Payment Purpose' : 'পেমেন্টের উদ্দেশ্য'}</span>
                  <span className="font-semibold text-slate-800 text-right">
                    {isEn ? data.purpose_title_en || data.purpose : data.purpose_title_bn || data.purpose}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">{isEn ? 'Billed Member' : 'সদস্যের নাম'}</span>
                  <span className="font-semibold text-slate-800 text-right">
                    {isEn ? data.member_name : data.member_name_bn || data.member_name}
                  </span>
                </div>

                {data.membership_id && (
                  <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                    <span className="text-slate-500">{isEn ? 'Membership ID' : 'সদস্য আইডি'}</span>
                    <span className="font-mono font-semibold text-slate-800">
                      {data.membership_id}
                    </span>
                  </div>
                )}

                <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">{isEn ? 'Payment Date' : 'পরিশোধের তারিখ ও সময়'}</span>
                  <span className="text-slate-700">
                    {formatDate(data.paid_at || data.payment_date)}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">{isEn ? 'Transaction Reference' : 'ট্রানজেকশন রেফারেন্স'}</span>
                  <span className="font-mono text-slate-700">
                    {data.transaction_ref}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">{isEn ? 'Payment Channel' : 'পেমেন্ট চ্যানেল'}</span>
                  <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 font-semibold text-[11px]">
                    {data.provider || 'ONLINE'}
                  </span>
                </div>

                <div className="flex justify-between items-center py-1.5">
                  <span className="text-slate-500">{isEn ? 'Registry Verified At' : 'যাচাইয়ের সময়'}</span>
                  <span className="text-slate-400 font-mono text-[11px]">
                    {formatDate(data.verified_at || new Date().toISOString())}
                  </span>
                </div>
              </div>
            </div>

            {/* Verification Guarantee Footer */}
            <div className="bg-slate-50 p-4 border-t border-slate-100 text-center text-[11px] text-slate-500 flex items-center justify-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                {isEn
                  ? 'Guaranteed authentic by Power Grid Company of Bangladesh PLC.'
                  : 'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি কর্তৃক সত্যতা নিশ্চিতকৃত।'}
              </span>
            </div>
          </div>
        )}

        {/* Global Portal Links */}
        <div className="text-center text-xs text-slate-400 space-x-3">
          <Link href="/" className="hover:text-slate-600 underline">
            {isEn ? 'Portal Home' : 'পোর্টাল হোম'}
          </Link>
          <span>•</span>
          <Link href="/member/payments" className="hover:text-slate-600 underline">
            {isEn ? 'Member Payments' : 'সদস্য পেমেন্ট'}
          </Link>
          <span>•</span>
          <Link href="/contact" className="hover:text-slate-600 underline">
            {isEn ? 'Support / Helpdesk' : 'হেল্পডেস্ক'}
          </Link>
        </div>
      </div>
    </div>
  );
}
