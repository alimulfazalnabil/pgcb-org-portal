'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  CreditCard,
  Download,
  Share2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  RefreshCw,
  Copy,
  ExternalLink,
  QrCode,
  Lock,
  Layers,
  Clock,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { DigitalMemberIdData } from '@/lib/api/types';

export default function MemberDigitalIdPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cardData, setCardData] = useState<DigitalMemberIdData | null>(null);
  const [cardSide, setCardSide] = useState<'FRONT' | 'BACK'>('FRONT');
  const [copied, setCopied] = useState(false);

  const isEn = lang === 'en';

  const loadDigitalId = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getDigitalMemberId();
      setCardData(data);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to load Digital Member ID' : 'ডিজিটাল সদস্য পরিচয়পত্র লোড করতে ব্যর্থ হয়েছে'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDigitalId();
  }, []);

  const handleCopyLink = () => {
    if (!cardData?.verification_url) return;
    const fullUrl = `${window.location.origin}${cardData.verification_url}`;
    navigator.clipboard.writeText(fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const renderStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'ACTIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
          {isEn ? '🟢 ACTIVE MEMBER' : '🟢 সক্রিয় সদস্য'}
        </span>
      );
    }
    if (s === 'EXPIRING_SOON') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
          <AlertTriangle className="w-3.5 h-3.5" />
          {isEn ? '🟠 EXPIRING SOON' : '🟠 মেয়াদ শীঘ্রই শেষ হবে'}
        </span>
      );
    }
    if (s === 'EXPIRED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-200 text-slate-800 border border-slate-400">
          <Clock className="w-3.5 h-3.5" />
          {isEn ? '🔴 EXPIRED' : '🔴 মেয়াদোত্তীর্ণ'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">
        <XCircle className="w-3.5 h-3.5" />
        {s}
      </span>
    );
  };

  return (
    <MemberLayout
      title={isEn ? 'Digital Member ID' : 'ডিজিটাল সদস্য পরিচয়পত্র'}
      lang={lang}
      onLangChange={setLang}
      activeTab="digital-id"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-50 text-emerald-700 rounded-xl">
              <CreditCard className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {isEn ? 'DIGITAL MEMBER ID' : 'ডিজিটাল সদস্য পরিচয়পত্র'}
              </h1>
              <p className="text-sm text-slate-500">
                {isEn
                  ? 'Official encrypted credentials for institutional access & verification'
                  : 'প্রাতিষ্ঠানিক পরিচয় ও সরাসরি কিউআর যাচাইযোগ্য অফিসিয়াল পরিচয়পত্র'}
              </p>
            </div>
          </div>

          {cardData && (
            <div className="flex items-center gap-2">
              <a
                href={cardData.pdf_download_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                {isEn ? 'Download PDF Card' : 'পিডিএফ আইডি ডাউনলোড'}
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
              {isEn ? 'Generating secure Digital ID...' : 'ডিজিটাল পরিচয়পত্র প্রস্তুত হচ্ছে...'}
            </p>
          </div>
        ) : !cardData ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">
              {isEn ? 'Digital ID Unavailable' : 'ডিজিটাল পরিচয়পত্র পাওয়া যায়নি'}
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              {isEn
                ? 'Your membership is not currently active or requires document completion.'
                : 'আপনার সদস্যপদ এখনও সক্রিয় নয় অথবা প্রয়োজনীয় ডকুমেন্টস জমা দেওয়া বাকি রয়েছে।'}
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Card Flip Switcher */}
            <div className="flex justify-center">
              <div className="inline-flex p-1 bg-slate-200 rounded-xl">
                <button
                  onClick={() => setCardSide('FRONT')}
                  className={`px-6 py-2 rounded-lg text-xs font-bold transition-all ${
                    cardSide === 'FRONT'
                      ? 'bg-white text-emerald-800 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {isEn ? 'Front Side' : 'সম্মুখ ভাগ'}
                </button>
                <button
                  onClick={() => setCardSide('BACK')}
                  className={`px-6 py-2 rounded-lg text-xs font-bold transition-all ${
                    cardSide === 'BACK'
                      ? 'bg-white text-emerald-800 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {isEn ? 'Back Side' : 'বিপরীত ভাগ'}
                </button>
              </div>
            </div>

            {/* Interactive Physical-like ID Card */}
            <div className="flex justify-center">
              {cardSide === 'FRONT' ? (
                /* Card Front */
                <div className="w-full max-w-[500px] h-[310px] rounded-2xl shadow-xl overflow-hidden border-2 border-emerald-600/30 bg-gradient-to-br from-emerald-900 via-emerald-800 to-teal-900 text-white p-6 relative flex flex-col justify-between select-none">
                  {/* Decorative background watermark */}
                  <div className="absolute right-0 bottom-0 opacity-10 pointer-events-none text-9xl font-black">
                    PGCB
                  </div>

                  {/* Top Bar */}
                  <div className="flex items-center justify-between pb-3 border-b border-emerald-700/60 relative z-10">
                    <div>
                      <h2 className="font-extrabold text-sm tracking-wider uppercase text-emerald-200">
                        {isEn ? 'Power Grid Bangladesh' : 'পাওয়ার গ্রিড বাংলাদেশ'}
                      </h2>
                      <p className="text-[10px] text-emerald-300/80">
                        Diploma Engineers Association
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-400/30">
                        {cardData.status}
                      </span>
                    </div>
                  </div>

                  {/* Middle Content */}
                  <div className="flex items-center gap-4 my-auto relative z-10">
                    <div className="w-24 h-28 rounded-xl bg-slate-100 border-2 border-emerald-400/50 overflow-hidden shadow-inner shrink-0 flex items-center justify-center">
                      {cardData.photo_url ? (
                        <img
                          src={cardData.photo_url}
                          alt={cardData.name_en}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-3xl font-black text-slate-400">
                          {cardData.name_en?.charAt(0) || 'P'}
                        </span>
                      )}
                    </div>

                    <div className="space-y-1 text-xs">
                      <h3 className="font-extrabold text-base text-white leading-tight">
                        {cardData.name_en}
                      </h3>
                      {cardData.name_bn && (
                        <p className="text-xs text-emerald-200 font-medium">
                          {cardData.name_bn}
                        </p>
                      )}
                      <p className="text-[11px] text-emerald-300 font-semibold pt-1">
                        {cardData.designation_en || 'Engineer'}
                      </p>
                      <p className="text-[11px] text-emerald-100">
                        {cardData.circle_en} Grid Circle
                      </p>
                      <div className="pt-1 flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-emerald-950/60 font-mono text-[11px] font-bold text-amber-300 border border-emerald-700/60">
                          {cardData.membership_id}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Bottom Footer */}
                  <div className="flex items-end justify-between pt-2 border-t border-emerald-700/60 relative z-10 text-[10px]">
                    <div>
                      <span className="text-emerald-300 block">{isEn ? 'Valid Until' : 'মেয়াদ'}</span>
                      <span className="font-bold text-white text-xs">
                        {cardData.valid_until_formatted || '31 Dec 2027'}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-emerald-300 block">{isEn ? 'Digital Security' : 'সিকিউরিটি'}</span>
                      <span className="font-mono font-bold text-emerald-200">
                        {cardData.identifier}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                /* Card Back */
                <div className="w-full max-w-[500px] h-[310px] rounded-2xl shadow-xl overflow-hidden border-2 border-slate-300 bg-white text-slate-800 p-6 relative flex flex-col justify-between select-none">
                  {/* Top Bar with QR */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <h3 className="font-bold text-xs uppercase tracking-wider text-emerald-900">
                        {isEn ? 'Verification & Terms' : 'যাচাইকরণ ও শর্তাবলী'}
                      </h3>
                      <p className="text-[11px] text-slate-500 leading-snug">
                        {isEn
                          ? 'This card is the official property of PGCB Diploma Engineers Association. If found, please return to Secretariat.'
                          : 'এই পরিচয়পত্রটি পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির সম্পদ। এটি পাওয়া গেলে অনুগ্রহ করে সমিতিতে ফেরত দিন।'}
                      </p>
                      <p className="text-[11px] text-slate-600 font-medium pt-1">
                        HQ: IEPB Bhaban, Ramna, Dhaka-1000
                      </p>
                    </div>

                    <div className="p-2 bg-slate-50 border border-slate-200 rounded-xl shrink-0 text-center">
                      <img
                        src={`https://api.qrserver.com/v1/create-qr-code/?size=90x90&data=${encodeURIComponent(
                          typeof window !== 'undefined'
                            ? `${window.location.origin}${cardData.verification_url}`
                            : cardData.verification_url
                        )}`}
                        alt="Verification QR"
                        className="w-20 h-20"
                      />
                      <span className="text-[8px] text-slate-500 font-semibold block mt-1">
                        SCAN TO VERIFY
                      </span>
                    </div>
                  </div>

                  {/* Middle Info */}
                  <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-600 flex justify-between">
                    <div>
                      <span className="text-slate-400 block">{isEn ? 'Membership Type' : 'সদস্যপদের ধরণ'}</span>
                      <span className="font-bold text-slate-800">{cardData.membership_type}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">{isEn ? 'Issued Date' : 'ইস্যুর তারিখ'}</span>
                      <span className="font-bold text-slate-800">
                        {cardData.issue_date ? new Date(cardData.issue_date).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD') : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">{isEn ? 'Status' : 'স্থিতি'}</span>
                      <span className="font-bold text-emerald-700">{cardData.status}</span>
                    </div>
                  </div>

                  {/* Signatures */}
                  <div className="flex items-end justify-between pt-2 border-t border-slate-200 text-[10px]">
                    <div className="text-center">
                      <div className="font-serif italic font-bold text-slate-700 text-xs mb-0.5">
                        Alimul Fazal
                      </div>
                      <span className="text-slate-500 border-t border-slate-300 pt-0.5 block">
                        {isEn ? 'Member Signature' : 'সদস্যের স্বাক্ষর'}
                      </span>
                    </div>
                    <div className="text-center">
                      <div className="font-serif italic font-bold text-emerald-800 text-xs mb-0.5">
                        Engr. SecGen
                      </div>
                      <span className="text-slate-500 border-t border-slate-300 pt-0.5 block">
                        {isEn ? 'General Secretary' : 'সাধারণ সম্পাদক'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions & Verification Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <ShieldCheck className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    {isEn ? 'Real-time Anti-Fraud Verification' : 'রিয়েল-টাইম অ্যান্টি-ফ্রড ভেরিফিকেশন'}
                  </h3>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">{isEn ? 'Authoritative Live State:' : 'অনলাইন লাইভ স্থিতি:'}</span>
                    {renderStatusBadge(cardData.status)}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">{isEn ? 'Remaining Validity:' : 'অবশিষ্ট মেয়াদ:'}</span>
                    <span className="font-bold text-slate-800">
                      {cardData.days_remaining !== null && cardData.days_remaining !== undefined
                        ? isEn
                          ? `${cardData.days_remaining} days remaining`
                          : `${cardData.days_remaining} দিন বাকি`
                        : 'Active'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">{isEn ? 'Cryptographic Token:' : 'সুরক্ষিত কিউআর টোকেন:'}</span>
                    <span className="font-mono text-slate-700">{cardData.identifier}</span>
                  </div>
                </div>

                <div className="pt-2 flex items-center gap-2">
                  <button
                    onClick={handleCopyLink}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    {copied ? (isEn ? 'Copied Link!' : 'লিংক কপি হয়েছে!') : (isEn ? 'Copy Public Verify Link' : 'যাচাইকরণ লিংক কপি করুন')}
                  </button>

                  <Link
                    href={cardData.verification_url}
                    target="_blank"
                    className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    {isEn ? 'Verify Screen' : 'যাচাই স্ক্রিন'}
                  </Link>
                </div>
              </div>

              {/* Download Assets Card */}
              <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <Download className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    {isEn ? 'Download & Export Assets' : 'আইডি কার্ড ডাউনলোড অপশন'}
                  </h3>
                </div>

                <div className="space-y-2.5">
                  <a
                    href={cardData.pdf_download_url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-between p-2.5 rounded-lg border border-emerald-200 bg-emerald-50/50 hover:bg-emerald-100 text-xs font-semibold text-emerald-900 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <CreditCard className="w-4 h-4 text-emerald-700" />
                      <span>{isEn ? 'Printable Double-Sided PDF (300 DPI)' : 'প্রিন্টযোগ্য দুই পাতার পিডিএফ (300 DPI)'}</span>
                    </div>
                    <Download className="w-4 h-4" />
                  </a>

                  <a
                    href="/api/v1/member/card?side=front"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <QrCode className="w-4 h-4 text-slate-500" />
                      <span>{isEn ? 'Download Front Side (PNG Image)' : 'সম্মুখ ভাগ ডাউনলোড (পিএনজি)'}</span>
                    </div>
                    <Download className="w-4 h-4" />
                  </a>

                  <a
                    href="/api/v1/member/card?side=back"
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      <QrCode className="w-4 h-4 text-slate-500" />
                      <span>{isEn ? 'Download Back Side (PNG Image)' : 'বিপরীত ভাগ ডাউনলোড (পিএনজি)'}</span>
                    </div>
                    <Download className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
