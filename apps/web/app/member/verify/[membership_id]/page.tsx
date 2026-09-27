'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Award,
  Building2,
  User,
  Calendar,
  Lock,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react';

interface MemberVerifyResponse {
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

export default function DynamicMemberVerifyPage() {
  const params = useParams<{ membership_id: string }>();
  const rawId = decodeURIComponent(params?.membership_id || '');
  const [data, setData] = useState<MemberVerifyResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!rawId) {
      setLoading(false);
      return;
    }

    const isToken = rawId.includes('.');
    const endpoint = isToken
      ? `/backend/api/v1/public/verify-token/${encodeURIComponent(rawId)}`
      : `/backend/api/v1/public/verify/${encodeURIComponent(rawId)}`;

    fetch(endpoint)
      .then(async (res) => {
        if (res.ok) {
          const json = await res.json();
          setData(json);
        } else {
          const err = await res.json().catch(() => ({}));
          setData({
            verified: false,
            name_bn: '',
            membership_id: rawId,
            status: 'NOT_FOUND',
            error: err.detail || 'প্রদত্ত সদস্য আইডি বা টোকেন কেন্দ্রীয় ডাটাবেসে পাওয়া যায়নি।',
          });
        }
      })
      .catch(() => {
        setData({
          verified: false,
          name_bn: '',
          membership_id: rawId,
          status: 'SERVER_ERROR',
          error: 'সার্ভারের সাথে সংযোগ স্থাপন করা সম্ভব হয়নি।',
        });
      })
      .finally(() => setLoading(false));
  }, [rawId]);

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <Link
            href="/verify"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
          >
            <ArrowLeft size={15} /> ভেরিফিকেশন পোর্টালে ফিরে যান
          </Link>
          <span className="text-[11px] font-mono text-secondary">ID: {rawId}</span>
        </div>

        {loading ? (
          <div className="bg-card border border-border rounded-2xl p-12 text-center space-y-3 shadow-sm">
            <RefreshCw size={28} className="animate-spin text-primary mx-auto" />
            <p className="text-sm font-bold text-foreground">সদস্যের পরিচয়পত্র যাচাই করা হচ্ছে...</p>
          </div>
        ) : !data || data.error ? (
          <div className="bg-rose-50 dark:bg-rose-950/40 border-2 border-rose-500/40 rounded-2xl p-6 sm:p-8 space-y-4 shadow-lg">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-rose-500/20 text-rose-600">
                <XCircle size={28} />
              </div>
              <div className="space-y-1">
                <h1 className="text-xl font-bold text-rose-800 dark:text-rose-300">
                  যাচাইকরণ ব্যর্থ হয়েছে (Unverified Member ID)
                </h1>
                <p className="text-sm text-rose-700 dark:text-rose-400">
                  {data?.error || 'এই সদস্য আইডি অনুমোদিত নয়।'}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-card rounded-2xl border-2 border-emerald-500/40 shadow-2xl overflow-hidden">
            <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 p-5 text-white flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-white/20">
                  <ShieldCheck size={26} />
                </div>
                <div>
                  <span className="text-[11px] uppercase tracking-widest font-extrabold text-emerald-100">
                    OFFICIAL DIGITAL MEMBER CREDENTIAL
                  </span>
                  <h1 className="text-xl sm:text-2xl font-black">বৈধ ও যাচাইকৃত সদস্য</h1>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-white text-emerald-800">
                <CheckCircle2 size={14} className="text-emerald-600" /> {data.status}
              </span>
            </div>

            <div className="p-6 sm:p-8 space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-border">
                <div>
                  <span className="text-xs font-bold text-secondary uppercase">সদস্যের নাম</span>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground mt-0.5">
                    {data.name_bn}
                  </h2>
                  {data.name_en && <p className="text-sm text-secondary mt-0.5">{data.name_en}</p>}
                </div>
                <div className="bg-surface rounded-xl p-3.5 border border-border sm:text-right">
                  <span className="text-xs text-secondary font-semibold uppercase">Member ID</span>
                  <div className="text-xl font-mono font-black text-primary mt-0.5">
                    {data.membership_id}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                    <Award size={15} className="text-primary" /> পদবী (Designation)
                  </div>
                  <p className="font-bold text-foreground">{data.designation_bn || 'প্রকৌশলী'}</p>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                    <Building2 size={15} className="text-primary" /> গ্রিড সার্কেল (Circle)
                  </div>
                  <p className="font-bold text-foreground">{data.circle_bn || 'কেন্দ্রীয় সচিবালয়'}</p>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                    <User size={15} className="text-primary" /> PGCB Employee ID
                  </div>
                  <p className="font-bold font-mono text-foreground">{data.employee_id || 'VERIFIED'}</p>
                </div>

                <div className="p-4 rounded-xl bg-surface border border-border space-y-1">
                  <div className="flex items-center gap-2 text-secondary text-xs font-semibold">
                    <Calendar size={15} className="text-primary" /> মেয়াদকাল (Validity)
                  </div>
                  <p className="font-bold text-foreground">{data.validity_date || 'সক্রিয়'}</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/5 border border-primary/20 flex items-center justify-between text-xs text-secondary flex-wrap gap-2">
                <span className="flex items-center gap-1.5 font-medium">
                  <Lock size={14} className="text-emerald-600" /> কেন্দ্রীয় ডাটাবেস দ্বারা স্বয়ংক্রিয়ভাবে যাচাইকৃত
                </span>
                <span className="font-mono text-[11px]">{data.verified_at || new Date().toISOString()}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
