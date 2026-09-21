'use client';

import { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { ShieldCheck, XCircle, Award, Calendar, FileText, CheckCircle2, ArrowLeft } from 'lucide-react';

interface CertificateData {
  certificate_no: string;
  recipient_name: string;
  title_bn: string;
  issue_date: string;
  event_id?: number;
  error?: string;
}

export default function PublicCertificateView({ params }: { params: Promise<{ token: string }> }) {
  const resolvedParams = use(params);
  const token = resolvedParams.token;
  
  const [data, setData] = useState<CertificateData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetch(`/backend/api/v1/certificates/verify/${encodeURIComponent(token)}`)
      .then(async (res) => {
        if (res.ok) {
          setData(await res.json());
        } else {
          setData({
            error: 'সনদপত্রটি খুঁজে পাওয়া যায়নি',
            certificate_no: '',
            recipient_name: '',
            title_bn: '',
            issue_date: ''
          });
        }
      })
      .catch(() => {
        setData({
          error: 'সনদপত্রটি খুঁজে পাওয়া যায়নি',
          certificate_no: '',
          recipient_name: '',
          title_bn: '',
          issue_date: ''
        });
      })
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-6">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium text-secondary">সনদপত্র যাচাই করা হচ্ছে...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Link 
            href="/" 
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition-colors"
          >
            <ArrowLeft size={14} /> প্রধান পাতায় ফিরুন
          </Link>
          <span className="text-xs font-mono text-secondary">
            TOKEN: {token}
          </span>
        </div>

        {data?.error ? (
          /* Error State matching Playwright assertion 'সনদপত্রটি খুঁজে পাওয়া যায়নি' */
          <div className="bg-background rounded-2xl border-2 border-rose-500/30 p-8 shadow-xl text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950 dark:text-rose-400 flex items-center justify-center mx-auto">
              <XCircle size={36} />
            </div>
            <div className="space-y-1">
              <h1 className="text-2xl font-extrabold text-rose-700 dark:text-rose-300">
                সনদপত্রটি খুঁজে পাওয়া যায়নি
              </h1>
              <p className="text-sm text-secondary max-w-md mx-auto">
                আপনার প্রদত্ত টোকেনটির সাথে কোনো অনুমোদিত পিজিডিইএ অফিসিয়াল সনদের রেকর্ড মেলেনি বা এটি বাতিল করা হয়েছে।
              </p>
            </div>
            <div className="pt-2">
              <Link
                href="/verify"
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary/90 transition-colors shadow-md"
              >
                সদস্য ও সনদ যাচাই পোর্টাল
              </Link>
            </div>
          </div>
        ) : (
          /* Verified Certificate View */
          <div className="bg-background rounded-2xl border-2 border-emerald-500/40 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 p-6 text-white text-center space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-sm text-xs font-bold uppercase tracking-wider">
                <CheckCircle2 size={15} /> VERIFIED CERTIFICATE OF PARTICIPATION
              </div>
              <h1 className="text-2xl sm:text-3xl font-black">
                অফিসিয়াল অংশগ্রহণ ও অবদানের সনদ
              </h1>
              <p className="text-xs text-emerald-100 font-mono">
                সনদ নং: {data?.certificate_no}
              </p>
            </div>

            <div className="p-6 sm:p-8 space-y-6">
              <div className="text-center space-y-2 border-b border-border pb-6">
                <span className="text-xs font-bold text-secondary uppercase">প্রাপকের নাম (Recipient)</span>
                <h2 className="text-3xl font-extrabold text-primary dark:text-white">
                  {data?.recipient_name}
                </h2>
                <p className="text-base text-secondary font-medium">
                  {data?.title_bn}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <span className="text-secondary font-semibold">ইস্যুর তারিখ (Issue Date)</span>
                  <p className="font-bold text-primary dark:text-white text-sm">
                    {data?.issue_date ? new Date(data.issue_date).toLocaleDateString('bn-BD') : '—'}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <span className="text-secondary font-semibold">স্ট্যাটাস (Status)</span>
                  <p className="font-bold text-success text-sm">
                    সক্রিয় ও বৈধ (OFFICIALLY ISSUED)
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex items-start gap-3">
                <ShieldCheck size={20} className="text-primary flex-shrink-0 mt-0.5" />
                <p className="text-xs text-secondary leading-relaxed">
                  এই সনদটি পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতি কর্তৃক আয়োজিত কারিগরি অধিবেশন ও সাধারণ সভায় উপস্থিতি সাপেক্ষে কেন্দ্রীয় নির্বাহী পরিষদ কর্তৃক ডিজিটালি অনুমোদিত।
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
