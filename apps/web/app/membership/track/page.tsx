'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api } from '../../../lib/api';
import { LoadingState } from '../../../components/ui/LoadingState';
import { ErrorState } from '../../../components/ui/ErrorState';
import { Search, CheckCircle2, Clock, XCircle, ArrowRight, ShieldCheck, FileText } from 'lucide-react';

interface TimelineStep {
  step: number;
  title: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'REJECTED';
  date: string | null;
  description: string;
}

interface TrackResult {
  application_no: string;
  status: string;
  applicant_name_masked: string;
  circle_bn: string;
  submission_date: string;
  application_note: string;
  timeline: TimelineStep[];
  membership_id: string | null;
}

function TrackContent() {
  const searchParams = useSearchParams();
  const initialAppNo = searchParams.get('app_no') || '';

  const [appNo, setAppNo] = useState(initialAppNo);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TrackResult | null>(null);

  const fetchStatus = (trackingNo: string) => {
    if (!trackingNo.trim()) {
      setError('অনুগ্রহ করে ট্র্যাকিং নম্বরটি লিখুন');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    api.trackApplication(trackingNo.trim())
      .then((data) => {
        setResult(data);
      })
      .catch((err) => {
        setError(err.message || 'আবেদন নম্বরটি সঠিক নয় বা খুঁজে পাওয়া যায়নি');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    if (initialAppNo) {
      fetchStatus(initialAppNo);
    }
  }, [initialAppNo]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStatus(appNo);
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 min-h-screen">
      <div className="text-center mb-10">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 mb-3">
          অনলাইন ট্র্যাকিং সিস্টেম
        </span>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">সদস্যপদ আবেদনের অগ্রগতি ট্র্যাকিং</h1>
        <p className="text-slate-600 text-sm md:text-base">
          আপনার আবেদনের ট্র্যাকিং নম্বর (যেমন: APP-2026-XXXX) দিয়ে বর্তমান অবস্থা ও অনুমোদনের ধাপসমূহ দেখুন।
        </p>
      </div>

      {/* Search Input Box */}
      <div className="bg-white p-6 md:p-8 rounded-2xl border border-slate-200 shadow-sm mb-10">
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="আবেদন ট্র্যাকিং নম্বর দিন (যেমন: APP-2026-A1B2C3)..."
              value={appNo}
              onChange={(e) => setAppNo(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-lg text-sm font-mono tracking-wide focus:outline-none focus:ring-2 focus:ring-emerald-600 uppercase"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold text-sm transition-colors shadow-sm whitespace-nowrap"
          >
            {loading ? 'অনুসন্ধান হচ্ছে...' : 'স্ট্যাটাস দেখুন'}
          </button>
        </form>
      </div>

      {/* Loading & Error States */}
      {loading && <LoadingState message="আবেদনের তথ্য অনুসন্ধান করা হচ্ছে..." />}
      {error && !loading && <ErrorState message={error} onRetry={() => fetchStatus(appNo)} />}

      {/* Result View */}
      {result && !loading && (
        <div className="space-y-8 animate-fadeIn">
          {/* Status Header Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6 mb-6">
              <div>
                <span className="text-xs text-slate-500 block mb-1">ট্র্যাকিং নম্বর:</span>
                <span className="text-2xl font-mono font-bold text-slate-900">{result.application_no}</span>
              </div>

              <div>
                {result.status === 'ACTIVE' && (
                  <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                    <CheckCircle2 size={16} /> সক্রিয় সদস্য (ACTIVE)
                  </span>
                )}
                {result.status === 'SUBMITTED' && (
                  <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200">
                    <Clock size={16} /> দাখিলকৃত (SUBMITTED)
                  </span>
                )}
                {result.status === 'UNDER_REVIEW' && (
                  <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                    <Clock size={16} /> পর্যালোচনায় (UNDER REVIEW)
                  </span>
                )}
                {result.status === 'REJECTED' && (
                  <span className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200">
                    <XCircle size={16} /> বাতিল / স্থগিত (REJECTED)
                  </span>
                )}
              </div>
            </div>

            {/* Applicant Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-xs text-slate-400 block">আবেদনকারীর নাম:</span>
                <span className="font-semibold text-slate-800">{result.applicant_name_masked}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">গ্রিড সার্কেল:</span>
                <span className="font-semibold text-slate-800">{result.circle_bn}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">আবেদনের তারিখ:</span>
                <span className="font-semibold text-slate-800">{result.submission_date || '—'}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">সদস্য নম্বর:</span>
                <span className="font-mono font-bold text-emerald-700">
                  {result.membership_id || 'অপেক্ষমাণ'}
                </span>
              </div>
            </div>

            {result.application_note && (
              <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600">
                <strong>কর্তৃপক্ষের নোট:</strong> {result.application_note}
              </div>
            )}
          </div>

          {/* Chronological Timeline */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
              <span>🕒</span> অনুমোদনের পর্যায়ক্রমিক অগ্রগতি
            </h3>

            <div className="space-y-8 relative before:absolute before:inset-0 before:left-5 before:h-full before:w-0.5 before:bg-slate-200">
              {result.timeline.map((step) => {
                const isCompleted = step.status === 'COMPLETED';
                const isInProgress = step.status === 'IN_PROGRESS';
                const isFailed = step.status === 'REJECTED';

                return (
                  <div key={step.step} className="relative flex items-start gap-5">
                    <div
                      className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0 border-2 transition-all ${
                        isCompleted
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : isInProgress
                          ? 'bg-amber-100 text-amber-800 border-amber-500 animate-pulse'
                          : isFailed
                          ? 'bg-red-600 text-white border-red-600'
                          : 'bg-white text-slate-400 border-slate-300'
                      }`}
                    >
                      {isCompleted ? <CheckCircle2 size={20} /> : step.step}
                    </div>

                    <div className="flex-1 pt-1">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                        <h4 className="font-bold text-slate-900 text-base">{step.title}</h4>
                        {step.date && <span className="text-xs font-medium text-slate-500">{step.date}</span>}
                      </div>
                      <p className="text-xs md:text-sm text-slate-600 leading-relaxed">
                        {step.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Links */}
          {result.status === 'ACTIVE' && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-6 text-center">
              <h4 className="text-lg font-bold text-emerald-900 mb-2">
                অভিনন্দন! আপনার সদস্যপদ সক্রিয় করা হয়েছে।
              </h4>
              <p className="text-xs text-emerald-700 mb-4">
                আপনার মেম্বার পোর্টালে লগইন করে ডিজিটাল পরিচয়পত্র ও সার্টিফিকেট ডাউনলোড করুন।
              </p>
              <div className="flex justify-center gap-3">
                <Link
                  href="/portal"
                  className="px-6 py-2.5 bg-emerald-700 text-white rounded-lg font-semibold hover:bg-emerald-800 transition-colors text-sm shadow-sm"
                >
                  মেম্বার পোর্টালে যান
                </Link>
                <Link
                  href={`/verify?membership_id=${encodeURIComponent(result.membership_id || '')}`}
                  className="px-6 py-2.5 bg-white border border-emerald-300 text-emerald-800 rounded-lg font-semibold hover:bg-emerald-50 transition-colors text-sm"
                >
                  সার্টিফিকেট যাচাই করুন
                </Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MembershipTrackPage() {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto px-6 py-12">
          <LoadingState message="ট্র্যাকিং পৃষ্ঠা লোড হচ্ছে..." />
        </div>
      }
    >
      <TrackContent />
    </Suspense>
  );
}
