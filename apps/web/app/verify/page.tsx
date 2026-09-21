'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  ShieldCheck, 
  Search, 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  Lock, 
  QrCode, 
  Building2, 
  Calendar, 
  User, 
  Award,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

interface VerificationData {
  verified: boolean;
  name_bn: string;
  name_en?: string | null;
  membership_id: string;
  employee_id?: string | null;
  designation_bn?: string | null;
  circle_bn?: string | null;
  status: string;
  validity_date?: string | null;
  verified_at?: string | null;
  error?: string;
}

export default function VerifyPage() {
  const [queryId, setQueryId] = useState('');
  const [result, setResult] = useState<VerificationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [isTokenScan, setIsTokenScan] = useState(false);

  async function performLookup(value: string = queryId) {
    const trimmed = value.trim();
    if (!trimmed) return;
    
    setLoading(true);
    setResult(null);

    const isToken = trimmed.includes('.');
    setIsTokenScan(isToken);

    try {
      const path = isToken
        ? `/backend/api/v1/public/verify-token/${encodeURIComponent(trimmed)}`
        : `/backend/api/v1/public/verify/${encodeURIComponent(trimmed)}`;

      const res = await fetch(path);
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        const err = await res.json().catch(() => ({}));
        setResult({
          error: err.detail || 'কোনো অনুমোদিত রেকর্ড পাওয়া যায়নি বা যাচাইকরণ টোকেনটি অবৈধ।',
          verified: false,
          name_bn: '',
          membership_id: trimmed,
          status: 'NOT_FOUND'
        });
      }
    } catch (e) {
      setResult({
        error: 'কেন্দ্রীয় ডেটাবেস সার্ভারের সাথে যোগাযোগ স্থাপন করা সম্ভব হয়নি। অনুগ্রহ করে পুনরায় চেষ্টা করুন।',
        verified: false,
        name_bn: '',
        membership_id: trimmed,
        status: 'SERVER_ERROR'
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const token = params.get('token');
      const membership = params.get('membership_id') || params.get('id');
      const target = token || membership;
      if (target) {
        setQueryId(target);
        performLookup(target);
      }
    }
  }, []);

  const getStatusBadge = (status: string, verified: boolean) => {
    if (verified && status === 'ACTIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/30">
          <CheckCircle2 size={14} className="text-emerald-600" /> সক্রিয় সদস্য (ACTIVE)
        </span>
      );
    }
    switch (status) {
      case 'UNDER_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-500/30">
            পর্যালোচনাধীন (UNDER REVIEW)
          </span>
        );
      case 'SUBMITTED':
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-500/30">
            আবেদন জমা (SUBMITTED)
          </span>
        );
      case 'SUSPENDED':
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300 border border-purple-500/30">
            স্থগিত (SUSPENDED)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-500/30">
            অননুমোদিত (INACTIVE / REJECTED)
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Institutional Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary dark:text-accent text-xs font-bold uppercase tracking-wider">
            <ShieldCheck size={16} /> NATIONAL VERIFICATION SYSTEM
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-primary dark:text-white tracking-tight">
            অফিসিয়াল সদস্য কার্ড ও ডিজিটাল সনদ যাচাই
          </h1>
          <p className="text-sm sm:text-base text-secondary max-w-2xl mx-auto">
            পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির অফিসিয়াল পরিচয়পত্র নম্বর অথবা ডিজিটাল কার্ডের কিউআর কোড টোকেন যাচাই করুন।
          </p>
        </div>

        {/* Verification Search Box */}
        <div className="bg-background rounded-2xl shadow-xl border border-border p-6 sm:p-8 space-y-4">
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              performLookup();
            }}
            className="flex flex-col sm:flex-row gap-3"
          >
            <div className="relative flex-1">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary">
                <Search size={18} />
              </div>
              <input 
                type="text"
                required
                value={queryId}
                onChange={(e) => setQueryId(e.target.value)}
                placeholder="সদস্য আইডি (যেমন: PGD-2026-1001) বা QR টোকেন লিখুন"
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-border bg-surface text-primary dark:text-white placeholder:text-secondary/60 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-sm sm:text-base"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !queryId.trim()}
              className="px-6 py-3 rounded-xl bg-primary hover:bg-primary/90 text-white font-bold text-sm sm:text-base transition-all shadow-md hover:shadow-lg disabled:opacity-50 inline-flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw size={18} className="animate-spin" /> যাচাই হচ্ছে...
                </>
              ) : (
                <>
                  <ShieldCheck size={18} /> আইডি যাচাই করুন
                </>
              )}
            </button>
          </form>

          {/* Helper Pills */}
          <div className="flex items-center justify-between text-xs text-secondary flex-wrap gap-2 pt-1 border-t border-border/50">
            <div className="flex items-center gap-1.5">
              <Lock size={13} className="text-success" />
              <span>ক্রিপ্টোগ্রাফিক HMAC-SHA256 দ্বারা সুরক্ষিত</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-secondary/70">নমুনা আইডি:</span>
              <button 
                type="button"
                onClick={() => {
                  setQueryId('PGD-2026-1001');
                  performLookup('PGD-2026-1001');
                }}
                className="font-mono text-primary dark:text-accent underline hover:opacity-80"
              >
                PGD-2026-1001
              </button>
            </div>
          </div>
        </div>

        {/* Dynamic Result Container */}
        {result && (
          <div className="animate-in fade-in-50 slide-in-from-bottom-4 duration-300">
            {result.error ? (
              /* Error / Not Found Alert */
              <div className="bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-500/40 rounded-2xl p-6 sm:p-8 space-y-4 shadow-lg">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-rose-500/20 text-rose-600 dark:text-rose-400">
                    <XCircle size={28} />
                  </div>
                  <div className="space-y-1">
                    <h2 className="text-xl font-bold text-rose-800 dark:text-rose-300">
                      যাচাইকরণ ব্যর্থ হয়েছে
                    </h2>
                    <p className="text-sm text-rose-700 dark:text-rose-400">
                      {result.error}
                    </p>
                  </div>
                </div>

                <div className="bg-background/80 rounded-xl p-4 border border-rose-500/20 text-xs text-secondary space-y-2">
                  <p className="font-bold text-primary dark:text-white">সম্ভাব্য কারণ ও পরামর্শ:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>প্রদত্ত সদস্য আইডি নম্বরে কোনো টাইপিং ভুল হতে পারে (নমুনা ফরম্যাট: PGD-2026-1001)।</li>
                    <li>কিউআর কোড টোকেনটি পরিবর্তিত বা ডিজিটাল স্বাক্ষরটি মেয়াদোত্তীর্ণ হতে পারে।</li>
                    <li>আবেদনটি এখনও অনুমোদিত হয়নি অথবা প্রশাসনিক পর্যালোচনায় রয়েছে।</li>
                  </ul>
                </div>
              </div>
            ) : (
              /* Valid Member Certificate Card */
              <div className="bg-background rounded-2xl border-2 border-emerald-500/40 shadow-2xl overflow-hidden">
                {/* Status Bar */}
                <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 p-4 sm:p-5 text-white flex items-center justify-between flex-wrap gap-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-full bg-white/20 backdrop-blur-sm">
                      <ShieldCheck size={26} className="text-white" />
                    </div>
                    <div>
                      <span className="text-xs uppercase tracking-widest font-extrabold text-emerald-100">
                        OFFICIAL VERIFIED CREDENTIAL
                      </span>
                      <h2 className="text-xl sm:text-2xl font-black">
                        বৈধ ও অনুমোদিত সদস্য
                      </h2>
                    </div>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(result.status, result.verified)}
                  </div>
                </div>

                {/* Main Content Body */}
                <div className="p-6 sm:p-8 space-y-6">
                  {/* Name and Monospace ID */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border">
                    <div>
                      <span className="text-xs font-bold text-secondary uppercase">সদস্যের নাম</span>
                      <h3 className="text-2xl sm:text-3xl font-extrabold text-primary dark:text-white mt-0.5">
                        {result.name_bn}
                      </h3>
                      {result.name_en && (
                        <p className="text-base font-medium text-secondary mt-0.5">
                          {result.name_en}
                        </p>
                      )}
                    </div>
                    <div className="bg-surface rounded-xl p-3.5 border border-border sm:text-right">
                      <span className="text-xs text-secondary font-semibold uppercase">সদস্যতা নম্বর (Member ID)</span>
                      <div className="text-xl sm:text-2xl font-mono font-black text-primary dark:text-accent mt-0.5">
                        {result.membership_id}
                      </div>
                    </div>
                  </div>

                  {/* Information Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <Award size={15} className="text-primary" /> পদবী (Designation)
                      </div>
                      <p className="font-bold text-primary dark:text-white text-base">
                        {result.designation_bn || '—'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <Building2 size={15} className="text-primary" /> গ্রিড সার্কেল (Grid Circle)
                      </div>
                      <p className="font-bold text-primary dark:text-white text-base">
                        {result.circle_bn || 'কেন্দ্রীয় সচিবালয়'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <User size={15} className="text-primary" /> PGCB Employee ID
                      </div>
                      <p className="font-bold font-mono text-primary dark:text-white text-base">
                        {result.employee_id || 'PGCB-STAFF'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <Calendar size={15} className="text-primary" /> কার্ডের মেয়াদকাল (Validity)
                      </div>
                      <p className="font-bold text-primary dark:text-white text-base">
                        {result.validity_date || '31-12-2027'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <Lock size={15} className="text-primary" /> যাচাই পদ্ধতি (Method)
                      </div>
                      <p className="font-semibold text-primary dark:text-white text-sm">
                        {isTokenScan ? 'HMAC-SHA256 Signed QR' : 'Direct Database Verification'}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                      <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                        <CheckCircle2 size={15} className="text-success" /> যাচাই সময় (Timestamp)
                      </div>
                      <p className="font-mono text-primary dark:text-white text-xs">
                        {result.verified_at || new Date().toISOString()}
                      </p>
                    </div>
                  </div>

                  {/* Official Secretariat Authenticity Notice */}
                  <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex items-start gap-3">
                    <ShieldCheck size={20} className="text-primary flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-secondary leading-relaxed">
                      <strong className="text-primary dark:text-white font-bold">প্রাতিষ্ঠানিক স্বীকৃতি:</strong> এই ডিজিটাল পরিচয়পত্রটি পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ লিমিটেড-এর ডিপ্লোমা প্রকৌশলী সমিতি (আইডিইবি অধিভুক্ত) কেন্দ্রীয় সচিবালয় দ্বারা অনুমোদিত। এই পরিচয়পত্রের কোনো তথ্যের অমিল পাওয়া গেলে সরাসরি কেন্দ্রীয় রেজিস্ট্রারের সাথে যোগাযোগ করুন।
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* How It Works Explainer Grid */}
        <div className="pt-8 border-t border-border space-y-6">
          <div className="text-center">
            <h3 className="text-xl font-bold text-primary dark:text-white">
              ডিজিটাল যাচাইকরণ প্রক্রিয়া
            </h3>
            <p className="text-xs text-secondary mt-1">
              স্বচ্ছতা ও প্রাতিষ্ঠানিক নিরাপত্তা বজায় রাখতে তিন স্তরের ক্রিপ্টোগ্রাফিক সুরক্ষা ব্যবস্থা
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-5 rounded-xl bg-background border border-border space-y-2">
              <div className="w-9 h-9 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-bold">
                1
              </div>
              <h4 className="font-bold text-sm text-primary dark:text-white">আইডি বা কিউআর স্ক্যান</h4>
              <p className="text-xs text-secondary leading-relaxed">
                সদস্যের ফিজিক্যাল পরিচয়পত্র বা ডিজিটাল কার্ডের কিউআর কোড স্ক্যান করে এই লিংকে প্রবেশ করুন।
              </p>
            </div>

            <div className="p-5 rounded-xl bg-background border border-border space-y-2">
              <div className="w-9 h-9 rounded-lg bg-accent/20 text-accent flex items-center justify-center font-bold">
                2
              </div>
              <h4 className="font-bold text-sm text-primary dark:text-white">স্বাক্ষর প্রমাণীকরণ</h4>
              <p className="text-xs text-secondary leading-relaxed">
                টোকেনের ভেতর থাকা HMAC ক্রিপ্টোগ্রাফিক ডিজিটাল হ্যাশ সার্ভারের গোপন চাবির সাথে মেলানো হয়।
              </p>
            </div>

            <div className="p-5 rounded-xl bg-background border border-border space-y-2">
              <div className="w-9 h-9 rounded-lg bg-success/20 text-success flex items-center justify-center font-bold">
                3
              </div>
              <h4 className="font-bold text-sm text-primary dark:text-white">লাইভ প্রাতিষ্ঠানিক সনদ</h4>
              <p className="text-xs text-secondary leading-relaxed">
                লাইভ ডেটাবেস থেকে সদস্যের নাম, সার্কেল, মেয়াদ ও সক্রিয় স্ট্যাটাস রিয়েল-টাইমে প্রদর্শিত হয়।
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
