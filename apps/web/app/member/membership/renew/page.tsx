'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  RefreshCw,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Calendar,
  CreditCard,
  Sparkles,
  ArrowRight,
  Clock,
  Check,
  Info,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MembershipRenewalOptions, MembershipRenewalOption } from '@/lib/api/types';
import { MemberLayout } from '@/components/member/MemberLayout';

export default function MembershipRenewalPage() {
  const router = useRouter();
  const [renewalData, setRenewalData] = useState<MembershipRenewalOptions | null>(null);
  const [selectedDuration, setSelectedDuration] = useState<number>(2); // Default to recommended 2 years
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('en');

  const isEn = lang === 'en';

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRenewalOptions();
      setRenewalData(res);
      // Select recommended plan or first plan
      if (res.options && res.options.length > 0) {
        const rec = res.options.find((o) => o.recommended) || res.options[0];
        setSelectedDuration(rec.duration_years);
      }
    } catch (err: any) {
      if (err?.status === 401) {
        router.push('/login?redirect=/member/membership/renew');
        return;
      }
      setError(err?.message || 'Failed to load renewal options.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleRenewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renewalData || !renewalData.can_renew) return;

    const chosenOption = renewalData.options.find((o) => o.duration_years === selectedDuration);
    if (!chosenOption) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await api.submitRenewal({
        duration_years: chosenOption.duration_years,
        plan_code: chosenOption.plan_code,
        notes: notes.trim() || undefined,
      });

      if (res.payment_checkout_url) {
        window.location.href = res.payment_checkout_url;
      } else {
        router.push('/member/membership?renewed=true');
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate renewal. Please try again.');
      setSubmitting(false);
    }
  };

  const selectedOption = renewalData?.options.find((o) => o.duration_years === selectedDuration);

  return (
    <MemberLayout lang={lang} onLangChange={setLang}>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header Breadcrumbs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 mb-1">
              <Link href="/member/dashboard" className="hover:text-emerald-400 transition-colors">
                {isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}
              </Link>
              <ChevronRight size={14} />
              <Link href="/member/membership" className="hover:text-emerald-400 transition-colors">
                {isEn ? 'Membership' : 'সদস্যপদ'}
              </Link>
              <ChevronRight size={14} />
              <span className="text-emerald-400">{isEn ? 'Renew' : 'নবায়ন'}</span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-black text-white tracking-tight">
              {isEn ? 'RENEW MEMBERSHIP' : 'সদস্যপদ নবায়ন করুন'}
            </h1>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
            <AlertCircle size={20} className="shrink-0 text-rose-400" />
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
            <p className="text-slate-400 font-medium text-sm">
              {isEn ? 'Loading renewal plans...' : 'নবায়ন সংক্রান্ত তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        ) : !renewalData ? null : !renewalData.can_renew ? (
          /* Ineligibility Notice */
          <div className="rounded-3xl bg-slate-900/70 border border-amber-500/40 p-8 text-center space-y-4 shadow-xl">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto">
              <AlertTriangle size={32} />
            </div>
            <h2 className="text-xl font-bold text-white">
              {isEn ? 'Renewal Currently Ineligible' : 'বর্তমানে নবায়ন আবেদন প্রযোজ্য নয়'}
            </h2>
            <p className="text-sm text-slate-300 max-w-lg mx-auto leading-relaxed">
              {renewalData.ineligibility_reason ||
                (isEn
                  ? 'Your membership is not currently eligible for renewal. Please check your existing application status or contact your circle administrator.'
                  : 'আপনার সদস্যপদটি বর্তমানে নবায়নের উপযোগী নয়।')}
            </p>
            <div className="pt-4 flex flex-wrap items-center justify-center gap-3">
              <Link
                href="/member/membership"
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-sm transition-colors border border-slate-700"
              >
                {isEn ? 'Back to Membership' : 'সদস্যপদ পৃষ্ঠায় ফিরুন'}
              </Link>
              <Link
                href="/member/application"
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm transition-colors"
              >
                {isEn ? 'Check Application Status' : 'আবেদন স্থিতি দেখুন'}
              </Link>
            </div>
          </div>
        ) : (
          /* Renewal Form */
          <form onSubmit={handleRenewSubmit} className="space-y-6">
            {/* Current Status Pill */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">{isEn ? 'Membership ID:' : 'সদস্য আইডি:'}</span>
                <span className="font-mono font-bold text-white">{renewalData.membership_id}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">{isEn ? 'Current Expiry:' : 'বর্তমান মেয়াদ:'}</span>
                <span className="font-bold text-emerald-400">{renewalData.current_valid_until || '—'}</span>
              </div>
            </div>

            {/* Plan Cards */}
            <div>
              <label className="block text-sm font-bold text-slate-200 mb-3">
                {isEn ? 'Select Renewal Term' : 'নবায়নের মেয়াদ নির্বাচন করুন'}
              </label>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {renewalData.options.map((option) => {
                  const isSelected = selectedDuration === option.duration_years;
                  return (
                    <div
                      key={option.duration_years}
                      onClick={() => setSelectedDuration(option.duration_years)}
                      className={`relative rounded-2xl p-5 border cursor-pointer transition-all duration-200 flex flex-col justify-between ${
                        isSelected
                          ? 'bg-emerald-950/30 border-emerald-500 shadow-lg shadow-emerald-500/10'
                          : 'bg-slate-900/70 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {option.recommended && (
                        <span className="absolute -top-2.5 right-4 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-500 text-slate-950 shadow-md">
                          {isEn ? 'Recommended' : 'জনপ্রিয়'}
                        </span>
                      )}

                      <div>
                        <div className="flex items-center justify-between mb-3">
                          <h3 className="font-bold text-white text-base">
                            {isEn ? option.label_en : option.label_bn}
                          </h3>
                          <div
                            className={`w-5 h-5 rounded-full border flex items-center justify-center ${
                              isSelected
                                ? 'bg-emerald-500 border-emerald-500 text-slate-950'
                                : 'border-slate-700'
                            }`}
                          >
                            {isSelected && <Check size={12} strokeWidth={3} />}
                          </div>
                        </div>

                        <div className="mb-4">
                          <span className="text-2xl font-black text-white">
                            {option.formatted_net_fee}
                          </span>
                          {option.discount_amount > 0 && (
                            <span className="ml-2 text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                              {isEn ? option.savings_note_en : option.savings_note_bn}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-800/80 text-xs text-slate-400">
                        <span>{isEn ? 'New validity through:' : 'নতুন মেয়াদ পর্যন্ত:'}</span>
                        <div className="font-bold text-slate-200 mt-0.5">
                          {isEn ? option.projected_valid_until : option.projected_valid_until_bn}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Summary & Checkout Card */}
            {selectedOption && (
              <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 lg:p-8 space-y-5 shadow-xl">
                <h3 className="font-bold text-white text-base pb-3 border-b border-slate-800">
                  {isEn ? 'Order Summary' : 'পেমেন্ট ও অর্ডারের বিবরণ'}
                </h3>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between text-slate-300">
                    <span>
                      {isEn
                        ? `Renewal Term (${selectedOption.duration_years} Year${selectedOption.duration_years > 1 ? 's' : ''})`
                        : `নবায়ন মেয়াদ (${selectedOption.duration_years} বছর)`}
                    </span>
                    <span className="font-mono text-white">৳{selectedOption.base_fee.toLocaleString()}</span>
                  </div>

                  {selectedOption.discount_amount > 0 && (
                    <div className="flex justify-between text-emerald-400">
                      <span>{isEn ? 'Multi-Year Incentive Discount' : 'বহু-বর্ষীয় সাশ্রয়ী ছাড়'}</span>
                      <span className="font-mono">-৳{selectedOption.discount_amount.toLocaleString()}</span>
                    </div>
                  )}

                  <div className="pt-3 border-t border-slate-800 flex justify-between items-baseline">
                    <span className="font-bold text-white text-base">
                      {isEn ? 'Total Payable (BDT)' : 'মোট প্রদেয় ফি (টাকা)'}
                    </span>
                    <span className="text-2xl font-black text-emerald-400 font-mono">
                      {selectedOption.formatted_net_fee}
                    </span>
                  </div>
                </div>

                {/* Additional Notes */}
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                    {isEn ? 'Optional Notes / Special Requests' : 'বিশেষ মন্তব্য বা অনুরোধ (ঐচ্ছিক)'}
                  </label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder={isEn ? 'e.g., Circle transfer renewal' : 'প্রয়োজনে মন্তব্য লিখুন...'}
                    className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
                  />
                </div>

                {/* Submission CTA */}
                <div className="pt-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold text-base transition-colors shadow-lg shadow-emerald-600/20"
                  >
                    {submitting ? (
                      <>
                        <RefreshCw size={18} className="animate-spin" />
                        <span>{isEn ? 'Processing Request...' : 'প্রক্রিয়াধীন রয়েছে...'}</span>
                      </>
                    ) : (
                      <>
                        <CreditCard size={18} />
                        <span>
                          {isEn
                            ? `Proceed to Payment (${selectedOption.formatted_net_fee})`
                            : `পেমেন্টে এগিয়ে যান (${selectedOption.formatted_net_fee})`}
                        </span>
                      </>
                    )}
                  </button>
                  <p className="text-[11px] text-slate-500 text-center mt-2 flex items-center justify-center gap-1">
                    <ShieldCheck size={14} className="text-emerald-500" />
                    <span>
                      {isEn
                        ? '100% secure payment gateway with automated digital receipt generation.'
                        : '১০০% নিরাপদ পেমেন্ট গেটওয়ে ও স্বয়ংক্রিয় ডিজিটাল রসিদ সেবা।'}
                    </span>
                  </p>
                </div>
              </div>
            )}
          </form>
        )}
      </div>
    </MemberLayout>
  );
}
