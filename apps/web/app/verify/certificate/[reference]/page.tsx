'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  Award,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Calendar,
  Lock,
} from 'lucide-react';
import { membersApi } from '@/lib/api/members';
import { PublicCertificateVerificationResult } from '@/lib/api/types';

export default function PublicCertificateVerifyPage() {
  const params = useParams();
  const reference = String(params?.reference || '');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PublicCertificateVerificationResult | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('bn');

  const isEn = lang === 'en';

  useEffect(() => {
    async function verify() {
      if (!reference) return;
      try {
        setLoading(true);
        setError(null);
        const res = await membersApi.verifyCertificatePublic(reference);
        setData(res);
      } catch (err: any) {
        setError(err?.message || (isEn ? 'Certificate verification record not found.' : 'সনদপত্র যাচাইকরণ রেকর্ড পাওয়া যায়নি।'));
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
          <div className="inline-flex p-3 bg-amber-700 text-white rounded-2xl shadow-md mb-2">
            <Award className="w-8 h-8" />
          </div>
          <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
            {isEn ? 'Power Grid Bangladesh' : 'পাওয়ার গ্রিড বাংলাদেশ'}
          </h1>
          <p className="text-xs text-slate-500 font-medium">
            {isEn
              ? 'Institutional Certificate Registry & Authenticity Check'
              : 'প্রাতিষ্ঠানিক সনদপত্র নিবন্ধন ও সত্যতা যাচাই'}
          </p>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
            <RefreshCw className="w-8 h-8 text-amber-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-600">
              {isEn ? 'Verifying certificate authenticity...' : 'সনদের সত্যতা যাচাই করা হচ্ছে...'}
            </p>
          </div>
        ) : error || !data ? (
          <div className="bg-white rounded-2xl border border-red-200 p-8 text-center shadow-sm space-y-3">
            <div className="w-14 h-14 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
              <XCircle className="w-8 h-8" />
            </div>
            <h2 className="text-lg font-bold text-red-900">
              {isEn ? 'Certificate Not Found' : 'সনদপত্রটি পাওয়া যায়নি'}
            </h2>
            <p className="text-xs text-slate-600 max-w-sm mx-auto">
              {error || (isEn ? 'The provided certificate number or token does not match any official issued record.' : 'প্রদত্ত সনদ নম্বর বা টোকেনের অনুকূলে কোনো আনুষ্ঠানিক রেকর্ড পাওয়া যায়নি।')}
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
                data.is_valid && data.status === 'VALID'
                  ? 'bg-gradient-to-r from-emerald-700 to-teal-800'
                  : 'bg-gradient-to-r from-red-700 to-rose-900'
              }`}
            >
              <div className="inline-flex p-2 bg-white/20 rounded-full mb-1">
                {data.is_valid && data.status === 'VALID' ? (
                  <CheckCircle2 className="w-8 h-8 text-white" />
                ) : (
                  <XCircle className="w-8 h-8 text-white" />
                )}
              </div>
              <h2 className="text-xl font-black tracking-wide">
                {data.is_valid && data.status === 'VALID'
                  ? isEn
                    ? 'GENUINE & VALID CERTIFICATE'
                    : 'যাচাইকৃত ও অনুমোদিত মূল সনদপত্র'
                  : isEn
                  ? 'CERTIFICATE REVOKED'
                  : 'সনদপত্রটি প্রত্যাহার / বাতিল করা হয়েছে'}
              </h2>
              <p className="text-xs text-white/80">
                {isEn
                  ? 'Officially recorded in PGCB Central Certificate Registry'
                  : 'পাওয়ার গ্রিড কেন্দ্রীয় সনদ রেজিস্ট্রি অনুযায়ী সংরক্ষিত'}
              </p>
            </div>

            {/* Certificate Details */}
            <div className="p-6 space-y-4">
              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-center">
                  <span className="text-slate-500">{isEn ? 'Certificate Number:' : 'সনদপত্র নং:'}</span>
                  <span className="font-mono font-bold text-slate-900 text-sm">
                    {data.certificate_no}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-center">
                  <span className="text-slate-500">{isEn ? 'Awarded / Issued To:' : 'প্রাপকের নাম:'}</span>
                  <span className="font-bold text-slate-900 text-sm">
                    {data.recipient_name}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-center">
                  <span className="text-slate-500">{isEn ? 'Certificate Type:' : 'সনদের ধরণ:'}</span>
                  <span className="font-bold text-slate-800">
                    {data.certificate_type}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-center">
                  <span className="text-slate-500">{isEn ? 'Issue Date:' : 'ইস্যুর তারিখ:'}</span>
                  <span className="font-medium text-slate-800">
                    {data.issue_date || 'N/A'}
                  </span>
                </div>

                {data.status === 'REVOKED' && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-900 space-y-1">
                    <span className="font-bold block flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      {isEn ? 'Revocation Reason:' : 'প্রত্যাহারের কারণ:'}
                    </span>
                    <p className="text-xs">
                      {data.revocation_reason || (isEn ? 'Revoked by official authority.' : 'কর্তৃপক্ষ কর্তৃক প্রত্যাহারকৃত।')}
                    </p>
                    {data.revoked_at && (
                      <p className="text-[11px] text-red-700 pt-1">
                        {isEn ? 'Date of revocation:' : 'প্রত্যাহারের তারিখ:'} {new Date(data.revoked_at).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD')}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Security signature */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  {isEn ? 'Cryptographically Verified Registry' : 'ক্রিপ্টোগ্রাফিক সনদপত্র রেজিস্ট্রি'}
                </span>
                <span>{new Date(data.verified_at).toLocaleTimeString(isEn ? 'en-GB' : 'bn-BD')}</span>
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
