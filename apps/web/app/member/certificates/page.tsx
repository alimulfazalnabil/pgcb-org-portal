'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Award,
  Download,
  Eye,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Calendar,
  FileBadge,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberCertificateItem } from '@/lib/api/types';

export default function MemberCertificatesPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [certs, setCerts] = useState<MemberCertificateItem[]>([]);

  const isEn = lang === 'en';

  const loadCertificates = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getMemberCertificatesList();
      setCerts(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to load certificates' : 'সনদপত্র লোড করতে সমস্যা হয়েছে'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCertificates();
  }, []);

  const renderStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'VALID') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {isEn ? '✓ Valid' : '✓ বৈধ'}
        </span>
      );
    }
    if (s === 'REVOKED') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200">
          <XCircle className="w-3.5 h-3.5" />
          {isEn ? '✕ Revoked' : '✕ প্রত্যাহৃত'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-300">
        <AlertTriangle className="w-3.5 h-3.5" />
        {status}
      </span>
    );
  };

  return (
    <MemberLayout
      title={isEn ? 'My Certificates' : 'আমার সনদপত্রসমূহ'}
      lang={lang}
      onLangChange={setLang}
      activeTab="certificates"
    >
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-50 text-emerald-700 rounded-xl">
              <Award className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {isEn ? 'CERTIFICATE WALLET' : 'সনদপত্র ওয়ালেট'}
              </h1>
              <p className="text-sm text-slate-500">
                {isEn
                  ? 'Official membership credentials, conference and training certificates'
                  : 'প্রাতিষ্ঠানিক সদস্যপদ, প্রশিক্ষণ ও সম্মেলনের প্রাতিষ্ঠানিক সনদপত্র'}
              </p>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-sm">
              {isEn ? 'Loading certificates...' : 'সনদপত্র লোড হচ্ছে...'}
            </p>
          </div>
        ) : certs.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Award className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">
              {isEn ? 'No Certificates Issued' : 'কোনো সনদপত্র ইস্যু করা হয়নি'}
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              {isEn
                ? 'Your membership certificate will be available once your application is fully approved.'
                : 'আপনার আবেদন অনুমোদিত হওয়ার সাথে সাথে সদস্যপদ সনদপত্রটি এখানে প্রদর্শিত হবে।'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {certs.map((c) => {
              const isRevoked = (c.status || '').toUpperCase() === 'REVOKED';
              return (
                <div
                  key={c.id}
                  className={`bg-white rounded-xl border p-6 flex flex-col justify-between transition-all hover:shadow-md ${
                    isRevoked ? 'border-red-200 bg-red-50/20' : 'border-slate-200'
                  }`}
                >
                  <div className="space-y-4">
                    <div className="flex items-start justify-between gap-3">
                      <span className="p-3 bg-amber-50 text-amber-700 border border-amber-200/60 rounded-xl">
                        <Award className="w-6 h-6" />
                      </span>
                      <div>{renderStatusBadge(c.status)}</div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {c.certificate_type || 'MEMBERSHIP'}
                      </span>
                      <h3 className="text-lg font-bold text-slate-900 mt-2 leading-snug">
                        {isEn ? c.title_en || c.title_bn : c.title_bn || c.title_en}
                      </h3>
                      <p className="text-xs text-slate-500 mt-1 font-mono">
                        {c.certificate_no}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 space-y-1">
                      <div className="flex justify-between">
                        <span className="text-slate-400">{isEn ? 'Recipient:' : 'প্রাপক:'}</span>
                        <span className="font-semibold text-slate-800">{c.recipient_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">{isEn ? 'Issue Date:' : 'ইস্যুর তারিখ:'}</span>
                        <span className="font-semibold text-slate-800">{c.issue_date}</span>
                      </div>
                    </div>

                    {isRevoked && (
                      <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 space-y-1">
                        <span className="font-bold flex items-center gap-1 text-red-900">
                          <XCircle className="w-3.5 h-3.5 text-red-600" />
                          {isEn ? 'Revocation Reason:' : 'প্রত্যাহারের কারণ:'}
                        </span>
                        <p>{c.revocation_reason || (isEn ? 'Revoked by authority' : 'কর্তৃপক্ষ কর্তৃক প্রত্যাহারকৃত')}</p>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                    <Link
                      href={`/member/certificates/${c.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      {isEn ? 'View Certificate' : 'সনদপত্র দেখুন'}
                    </Link>

                    <div className="flex items-center gap-2">
                      <a
                        href={c.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        {isEn ? 'PDF' : 'পিডিএফ'}
                      </a>

                      <Link
                        href={`/verify/certificate/${c.certificate_no}`}
                        target="_blank"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                        {isEn ? 'Verify' : 'যাচাই'}
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
