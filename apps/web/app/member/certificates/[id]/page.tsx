'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Award,
  ArrowLeft,
  Download,
  Share2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  Copy,
  Printer,
  ShieldCheck,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberCertificateItem } from '@/lib/api/types';

export default function MemberCertificateDetailPage() {
  const params = useParams();
  const certId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cert, setCert] = useState<MemberCertificateItem | null>(null);
  const [copied, setCopied] = useState(false);

  const isEn = lang === 'en';

  const loadCertificate = async () => {
    if (!certId || isNaN(certId)) return;
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getMemberCertificateDetail(certId);
      setCert(data);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to load certificate' : 'সনদপত্র লোড করতে ব্যর্থ হয়েছে'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCertificate();
  }, [certId]);

  const handleCopyLink = () => {
    if (!cert?.certificate_no) return;
    const verifyUrl = `${window.location.origin}/verify/certificate/${cert.certificate_no}`;
    navigator.clipboard.writeText(verifyUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const isRevoked = (cert?.status || '').toUpperCase() === 'REVOKED';

  return (
    <MemberLayout
      title={cert?.title_en || (isEn ? 'Certificate Viewer' : 'সনদপত্র প্রিভিউ')}
      lang={lang}
      onLangChange={setLang}
      activeTab="certificates"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/member/certificates"
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-emerald-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isEn ? 'Back to All Certificates' : 'সকল সনদপত্রে ফিরে যান'}
          </Link>

          {cert && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors"
              >
                <Printer className="w-4 h-4 text-slate-500" />
                {isEn ? 'Print' : 'প্রিন্ট'}
              </button>

              <a
                href={cert.download_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                {isEn ? 'Download PDF Certificate' : 'পিডিএফ সনদপত্র ডাউনলোড'}
              </a>
            </div>
          )}
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
              {isEn ? 'Loading certificate details...' : 'সনদপত্র লোড হচ্ছে...'}
            </p>
          </div>
        ) : !cert ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Award className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">
              {isEn ? 'Certificate Not Found' : 'সনদপত্রটি পাওয়া যায়নি'}
            </h3>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Certificate Preview Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base text-emerald-300">
                    {isEn ? cert.title_en : cert.title_bn}
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    {cert.certificate_no}
                  </p>
                </div>
                <div>
                  {isRevoked ? (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/40">
                      ✕ {isEn ? 'REVOKED' : 'প্রত্যাহৃত'}
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      ✓ {isEn ? 'VALID & VERIFIED' : 'বৈধ ও যাচাইকৃত'}
                    </span>
                  )}
                </div>
              </div>

              {/* Render Image or Canvas */}
              <div className="p-6 bg-slate-100 flex items-center justify-center min-h-[480px]">
                <div className="bg-white p-2 rounded-xl shadow-md border border-slate-200 max-w-full">
                  <img
                    src={cert.preview_url}
                    alt={cert.title_en}
                    className="max-h-[550px] w-auto object-contain rounded-lg"
                    onError={(e) => {
                      // Fallback display if png is generating
                      (e.target as any).style.display = 'none';
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Verification & Metadata Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <ShieldCheck className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    {isEn ? 'Certificate Credentials' : 'সনদপত্রের তথ্যাবলী'}
                  </h3>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">{isEn ? 'Recipient Name:' : 'প্রাপকের নাম:'}</span>
                    <span className="font-bold text-slate-900">{cert.recipient_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{isEn ? 'Certificate Number:' : 'সনদপত্র নং:'}</span>
                    <span className="font-mono font-semibold text-slate-800">{cert.certificate_no}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{isEn ? 'Certificate Type:' : 'সনদের ধরণ:'}</span>
                    <span className="font-semibold text-slate-800">{cert.certificate_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">{isEn ? 'Issue Date:' : 'ইস্যুর তারিখ:'}</span>
                    <span className="font-semibold text-slate-800">{cert.issue_date}</span>
                  </div>
                </div>

                {isRevoked && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-900 space-y-1">
                    <span className="font-bold block flex items-center gap-1">
                      <XCircle className="w-4 h-4 text-red-600" />
                      {isEn ? 'Revocation Reason:' : 'প্রত্যাহারের কারণ:'}
                    </span>
                    <p>{cert.revocation_reason || (isEn ? 'Certificate revoked by administrative authority.' : 'কর্তৃপক্ষ কর্তৃক সনদপত্র প্রত্যাহার করা হয়েছে।')}</p>
                  </div>
                )}
              </div>

              {/* Public Verification Link Card */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                    <ExternalLink className="w-5 h-5 text-emerald-700" />
                    <h3 className="font-bold text-slate-900 text-sm">
                      {isEn ? 'Instant Public QR Verification' : 'অনলাইন কিউআর যাচাইকরণ'}
                    </h3>
                  </div>

                  <p className="text-xs text-slate-500 mt-3 leading-relaxed">
                    {isEn
                      ? 'Anyone can scan the certificate QR code or use the official link to confirm authenticity directly from the PGCB database.'
                      : 'যে কেউ এই সনদপত্রের কিউআর স্ক্যান করে অথবা সরাসরি লিংকে প্রবেশ করে পাওয়ার গ্রিড ডাটাবেজ থেকে সত্যতা যাচাই করতে পারবে।'}
                  </p>
                </div>

                <div className="pt-2 flex items-center gap-2">
                  <button
                    onClick={handleCopyLink}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copied ? (isEn ? 'Copied Link!' : 'লিংক কপি হয়েছে!') : (isEn ? 'Copy Verify Link' : 'যাচাই লিংক কপি করুন')}
                  </button>

                  <Link
                    href={`/verify/certificate/${cert.certificate_no}`}
                    target="_blank"
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    {isEn ? 'Verify Screen' : 'যাচাই স্ক্রিন'}
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
