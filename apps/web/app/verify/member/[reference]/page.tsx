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
  Building,
  User,
  Calendar,
  Lock,
  ExternalLink,
} from 'lucide-react';
import { membersApi } from '@/lib/api/members';
import { PublicMemberVerificationResult } from '@/lib/api/types';

export default function PublicMemberVerifyPage() {
  const params = useParams();
  const reference = String(params?.reference || '');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PublicMemberVerificationResult | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('bn');

  const isEn = lang === 'en';

  useEffect(() => {
    async function verify() {
      if (!reference) return;
      try {
        setLoading(true);
        setError(null);
        const res = await membersApi.verifyMemberPublic(reference);
        setData(res);
      } catch (err: any) {
        setError(err?.message || (isEn ? 'Member verification record not found or inactive.' : 'সদস্যপদ যাচাইকরণ তথ্য পাওয়া যায়নি অথবা স্থিতি অকার্যকর।'));
      } finally {
        setLoading(false);
      }
    }
    verify();
  }, [reference]);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between p-4 sm:p-6 font-sans">
      <div className="max-w-xl w-full mx-auto my-auto space-y-6">
        {/* Language switch */}
        <div className="flex justify-end">
          <button
            onClick={() => setLang(lang === 'en' ? 'bn' : 'en')}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-100 text-slate-700"
          >
            {isEn ? 'বাংলা সংস্করণ' : 'English Version'}
          </button>
        </div>

        {/* Institution Brand */}
        <div className="text-center space-y-1">
          <div className="inline-flex p-3 bg-emerald-800 text-white rounded-2xl shadow-md mb-2">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            {isEn ? 'Power Grid Bangladesh' : 'পাওয়ার গ্রিড বাংলাদেশ'}
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            {isEn
              ? 'Diploma Engineers Association • Official Credentials Verification'
              : 'ডিপ্লোমা প্রকৌশলী সমিতি • প্রাতিষ্ঠানিক সনদ ও পরিচয় যাচাইকরণ'}
          </p>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-600">
              {isEn ? 'Authenticating credential with database...' : 'ডাটাবেজে সত্যতা যাচাই করা হচ্ছে...'}
            </p>
          </div>
        ) : error || !data ? (
          <div className="bg-white rounded-2xl border border-red-200 p-8 text-center shadow-sm space-y-3">
            <div className="w-14 h-14 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
              <XCircle className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-red-900">
              {isEn ? 'Verification Failed' : 'যাচাইকরণ ব্যর্থ হয়েছে'}
            </h2>
            <p className="text-xs text-slate-600 max-w-sm mx-auto">
              {error || (isEn ? 'The scanned QR code or membership identifier does not correspond to an authentic active record.' : 'স্ক্যানকৃত কিউআর কোড বা সদস্য নম্বরটি ডাটাবেজে পাওয়া যায়নি বা অকার্যকর।')}
            </p>
            <div className="pt-2 text-[11px] text-slate-400 font-mono">
              Ref: {reference}
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
            {/* Status Header Banner */}
            <div
              className={`p-6 text-white text-center space-y-1 ${
                data.is_valid && data.status === 'ACTIVE'
                  ? 'bg-gradient-to-r from-emerald-700 to-teal-800'
                  : 'bg-gradient-to-r from-red-700 to-rose-900'
              }`}
            >
              <div className="inline-flex p-2 bg-white/20 rounded-full mb-1">
                {data.is_valid && data.status === 'ACTIVE' ? (
                  <CheckCircle2 className="w-8 h-8 text-white" />
                ) : (
                  <AlertTriangle className="w-8 h-8 text-white" />
                )}
              </div>
              <h2 className="text-xl font-black tracking-wide">
                {data.is_valid && data.status === 'ACTIVE'
                  ? isEn
                    ? 'OFFICIALLY VERIFIED ACTIVE MEMBER'
                    : 'যাচাইকৃত সক্রিয় প্রাতিষ্ঠানিক সদস্য'
                  : isEn
                  ? `MEMBER STATUS: ${data.status}`
                  : `সদস্যপদ স্থিতি: ${data.status}`}
              </h2>
              <p className="text-xs text-white/80">
                {isEn
                  ? 'Real-time authoritative institutional credential confirmation'
                  : 'পাওয়ার গ্রিড কেন্দ্রীয় ডাটাবেজ কর্তৃক সরাসরি সংরক্ষিত ও প্রত্যয়িত'}
              </p>
            </div>

            {/* Member Details */}
            <div className="p-6 space-y-6">
              <div className="flex items-center gap-4 pb-6 border-b border-slate-100">
                <div className="w-20 h-24 rounded-xl bg-slate-100 border border-slate-200 overflow-hidden shadow-inner shrink-0 flex items-center justify-center">
                  {data.photo_url ? (
                    <img
                      src={data.photo_url}
                      alt={data.member_name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <User className="w-10 h-10 text-slate-400" />
                  )}
                </div>

                <div className="space-y-1">
                  <h3 className="font-extrabold text-lg text-slate-900">
                    {data.member_name}
                  </h3>
                  {data.member_name_bn && (
                    <p className="text-sm font-semibold text-emerald-800">
                      {data.member_name_bn}
                    </p>
                  )}
                  <p className="text-xs text-slate-600 font-medium">
                    {data.designation || 'Assistant Engineer'}
                  </p>
                  <p className="text-xs text-slate-500">
                    {data.circle} Grid Circle
                  </p>
                </div>
              </div>

              {/* Data Grid */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block mb-0.5">
                    {isEn ? 'Membership ID' : 'সদস্য আইডি'}
                  </span>
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {data.membership_id}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block mb-0.5">
                    {isEn ? 'Membership Type' : 'সদস্যপদের ধরণ'}
                  </span>
                  <span className="font-bold text-slate-900">
                    {data.membership_type}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block mb-0.5">
                    {isEn ? 'Validity Date' : 'মেয়াদ উত্তীর্ণের তারিখ'}
                  </span>
                  <span className="font-bold text-slate-900">
                    {data.valid_until ? new Date(data.valid_until).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD') : 'N/A'}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <span className="text-slate-400 block mb-0.5">
                    {isEn ? 'Verified Timestamp' : 'যাচাইয়ের সময়'}
                  </span>
                  <span className="font-medium text-slate-700">
                    {new Date(data.verified_at).toLocaleTimeString(isEn ? 'en-GB' : 'bn-BD')}
                  </span>
                </div>
              </div>

              {/* Security watermark notice */}
              <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  {isEn ? 'Tamper-Evident Anti-Fraud Engine' : 'ডিজিটাল জালিয়াতি রোধে সুরক্ষিত'}
                </span>
                <span className="font-mono">{data.verification_reference}</span>
              </div>
            </div>
          </div>
        )}

        <div className="text-center text-xs text-slate-400">
          <Link href="/" className="hover:text-emerald-700 underline transition-colors">
            {isEn ? 'Return to PGCB Portal Homepage' : 'পাওয়ার গ্রিড পোর্টাল হোমপেজে যান'}
          </Link>
        </div>
      </div>
    </div>
  );
}
