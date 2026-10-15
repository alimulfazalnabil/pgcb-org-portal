'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FileText,
  ChevronRight,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  AlertTriangle,
  Upload,
  CreditCard,
  ExternalLink,
  ShieldCheck,
  FileCheck,
  Layers,
  MapPin,
  Tag,
  Check,
  X,
} from 'lucide-react';
import { api } from '@/lib/api';
import { ApplicationCenterDetails, ApplicationTimelineStep } from '@/lib/api/types';
import { MemberLayout } from '@/components/member/MemberLayout';

export default function MemberApplicationCenterPage() {
  const router = useRouter();
  const [appDetails, setAppDetails] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<'en' | 'bn'>('en');

  // Inline upload state
  const [uploadDocType, setUploadDocType] = useState<string>('ACADEMIC');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const isEn = lang === 'en';

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getApplicationDetails();
      setAppDetails(res);
    } catch (err: any) {
      if (err?.status === 401) {
        router.push('/login?redirect=/member/application');
        return;
      }
      setError(err?.message || 'Failed to load application details.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError(isEn ? 'Please select a document to upload.' : 'অনুগ্রহ করে আপলোডের জন্য একটি ফাইল নির্বাচন করুন।');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const res = await api.uploadApplicationDocument(selectedFile, uploadDocType);
      setSuccessMsg(res.message || (isEn ? 'Document uploaded successfully.' : 'ডকুমেন্ট সফলভাবে আপলোড করা হয়েছে।'));
      setSelectedFile(null);
      await loadData();
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to upload document.' : 'ডকুমেন্ট আপলোড ব্যর্থ হয়েছে।'));
    } finally {
      setUploading(false);
    }
  };

  const getStepIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return <CheckCircle2 size={18} className="text-emerald-400" />;
      case 'CURRENT':
        return <Clock size={18} className="text-amber-400 animate-pulse" />;
      case 'REQUIRED':
        return <AlertTriangle size={18} className="text-amber-400" />;
      case 'REJECTED':
        return <AlertCircle size={18} className="text-rose-400" />;
      default:
        return <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />;
    }
  };

  const getStepBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'COMPLETED':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          label: isEn ? 'Completed' : 'সম্পন্ন',
        };
      case 'CURRENT':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          label: isEn ? 'In Progress' : 'চলমান',
        };
      case 'REQUIRED':
        return {
          bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
          label: isEn ? 'Action Required' : 'পদক্ষেপ আবশ্যক',
        };
      case 'REJECTED':
        return {
          bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
          label: isEn ? 'Correction Needed' : 'সংশোধন প্রয়োজন',
        };
      default:
        return {
          bg: 'bg-slate-800 text-slate-500 border-slate-700/50',
          label: isEn ? 'Upcoming' : 'পরবর্তী ধাপ',
        };
    }
  };

  const timelineSteps: any[] = appDetails?.timeline || [];
  const requiredDocs: any[] = appDetails?.required_document_types || [];
  const pendingPayment = appDetails?.pending_payment;

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
              <span className="text-emerald-400">{isEn ? 'Application Center' : 'আবেদন কেন্দ্র'}</span>
            </div>
            <h1 className="text-2xl lg:text-3xl font-black text-white tracking-tight">
              {isEn ? 'APPLICATION STATUS & LIFECYCLE' : 'আবেদনের স্থিতি ও ট্র্যাকিং'}
            </h1>
          </div>

          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            className="self-start sm:self-auto p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-colors"
            title={isEn ? 'Refresh' : 'রিফ্রেশ'}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center gap-3">
            <AlertCircle size={20} className="shrink-0 text-rose-400" />
            <p>{error}</p>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-3">
            <CheckCircle2 size={20} className="shrink-0 text-emerald-400" />
            <p>{successMsg}</p>
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
            <p className="text-slate-400 font-medium text-sm">
              {isEn ? 'Loading application lifecycle...' : 'আবেদন ট্র্যাকিং তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        ) : appDetails ? (
          <>
            {/* Top Application Overview Card */}
            <div className="rounded-3xl bg-slate-900/70 border border-slate-800 p-6 lg:p-8 backdrop-blur-md shadow-xl">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 block uppercase">
                    {isEn ? 'Application Number' : 'আবেদন নম্বর'}
                  </span>
                  <span className="text-xl font-black text-white font-mono tracking-wider">
                    {appDetails.application_no || 'PGCB-APP-PENDING'}
                  </span>
                </div>

                <div className="flex items-center gap-3">
                  <span className="px-3.5 py-1.5 rounded-full border text-xs font-bold bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                    {isEn ? appDetails.status_label_en : appDetails.status_label_bn}
                  </span>
                  {appDetails.membership_type && (
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                      {appDetails.membership_type}
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">{isEn ? 'Submitted On:' : 'জমা দেওয়ার তারিখ:'}</span>
                  <span className="font-semibold text-slate-200">{appDetails.submitted_at || '—'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">{isEn ? 'Grid Circle:' : 'গ্রিড সার্কেল:'}</span>
                  <span className="font-semibold text-slate-200">
                    {isEn ? appDetails.circle?.name_en || 'Dhaka' : appDetails.circle?.name_bn || 'ঢাকা'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">{isEn ? 'Last Updated:' : 'সর্বশেষ হালনাগাদ:'}</span>
                  <span className="font-semibold text-slate-200">{appDetails.reviewed_at || 'In Progress'}</span>
                </div>
              </div>
            </div>

            {/* Payment Callout Banner if Fee Pending */}
            {pendingPayment && (
              <div className="p-6 rounded-3xl bg-emerald-950/40 border border-emerald-500/40 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <CreditCard size={24} className="shrink-0 text-emerald-400 mt-0.5" />
                  <div>
                    <h3 className="font-bold text-white text-base">
                      {isEn ? 'Membership Fee Payment Ready' : 'সদস্যপদ ফি পরিশোধের অনুরোধ'}
                    </h3>
                    <p className="text-xs text-emerald-200/90 mt-1">
                      {isEn
                        ? `Application approved! Please proceed with payment of ${pendingPayment.amount_formatted} to activate your membership.`
                        : `আপনার আবেদনটি অনুমোদিত হয়েছে। সদস্যপদ সক্রিয় করতে ${pendingPayment.amount_formatted} ফি পরিশোধ করুন।`}
                    </p>
                  </div>
                </div>

                <a
                  href={pendingPayment.checkout_url}
                  className="shrink-0 inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-sm transition-colors shadow-lg shadow-emerald-500/20"
                >
                  <CreditCard size={16} />
                  <span>{isEn ? 'Pay Now' : 'ফি পরিশোধ করুন'}</span>
                </a>
              </div>
            )}

            {/* 6-Stage Timeline Section */}
            <div className="rounded-3xl bg-slate-900/60 border border-slate-800 p-6 lg:p-8 backdrop-blur-md shadow-xl space-y-6">
              <div className="flex items-center gap-2.5 pb-4 border-b border-slate-800">
                <Layers size={20} className="text-emerald-400" />
                <h2 className="text-lg font-bold text-white tracking-tight">
                  {isEn ? 'Application Timeline & Progress' : 'আবেদনের অগ্রগতির পর্যায়ক্রম'}
                </h2>
              </div>

              <div className="relative pl-6 space-y-8 before:content-[''] before:absolute before:left-3 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-800">
                {timelineSteps.map((step, idx) => {
                  const badge = getStepBadge(step.status);
                  const isLast = idx === timelineSteps.length - 1;

                  return (
                    <div key={step.step_key || idx} className="relative group">
                      {/* Step Indicator Dot */}
                      <div className="absolute -left-[23px] top-1 w-6 h-6 rounded-full bg-slate-900 border-2 border-slate-800 flex items-center justify-center ring-4 ring-slate-950">
                        {getStepIcon(step.status)}
                      </div>

                      <div className="bg-slate-900/40 rounded-2xl p-4 border border-slate-800/80 hover:border-slate-700/80 transition-colors">
                        <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                          <h3 className="font-bold text-white text-sm">
                            {isEn ? step.title_en : step.title_bn}
                          </h3>
                          <span className={`px-2 py-0.5 rounded-full border text-[10px] font-bold ${badge.bg}`}>
                            {badge.label}
                          </span>
                        </div>

                        {step.description && (
                          <p className="text-xs text-slate-400 leading-relaxed mb-2">
                            {step.description}
                          </p>
                        )}

                        {step.timestamp && (
                          <span className="text-[11px] font-mono text-emerald-400 block">
                            {step.timestamp}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Inline Missing / Required Document Upload */}
            {requiredDocs.length > 0 && (
              <div className="rounded-3xl bg-slate-900/70 border border-amber-500/30 p-6 lg:p-8 backdrop-blur-md shadow-xl space-y-5">
                <div className="flex items-center gap-2.5 pb-4 border-b border-slate-800">
                  <Upload size={20} className="text-amber-400" />
                  <div>
                    <h2 className="text-base font-bold text-white">
                      {isEn ? 'Required / Missing Documents' : 'প্রয়োজনীয় বা অসম্পূর্ণ ডকুমেন্ট সংযুক্তি'}
                    </h2>
                    <span className="text-xs text-slate-400">
                      {isEn
                        ? 'Please upload clear scans of the required documents below to proceed.'
                        : 'অনুমোদনের জন্য অনুগ্রহ করে নিম্নোক্ত ডকুমেন্টগুলো আপলোড করুন।'}
                    </span>
                  </div>
                </div>

                {/* List of Required Items */}
                <div className="space-y-2.5">
                  {requiredDocs.map((req, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 flex items-start gap-3"
                    >
                      <AlertTriangle size={17} className="text-amber-400 shrink-0 mt-0.5" />
                      <div className="text-xs">
                        <span className="font-bold text-white block">
                          {req.label_bn || req.type}
                        </span>
                        <span className="text-slate-400">{req.reason}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Upload Form */}
                <form onSubmit={handleFileUpload} className="space-y-4 pt-2">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                        {isEn ? 'Document Category' : 'ডকুমেন্টের ধরন'}
                      </label>
                      <select
                        value={uploadDocType}
                        onChange={(e) => setUploadDocType(e.target.value)}
                        className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-100 focus:outline-none focus:border-emerald-500"
                      >
                        <option value="ACADEMIC">{isEn ? 'Diploma Certificate (Academic)' : 'ডিপ্লোমা সনদপত্র'}</option>
                        <option value="NID">{isEn ? 'NID / Passport' : 'জাতীয় পরিচয়পত্র / পাসপোর্ট'}</option>
                        <option value="APPOINTMENT_LETTER">{isEn ? 'Appointment Letter' : 'নিয়োগপত্র'}</option>
                        <option value="PHOTO">{isEn ? 'Passport Photo' : 'পাসপোর্ট সাইজ ছবি'}</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                        {isEn ? 'Select File (PDF, JPEG, PNG, WEBP <= 5MB)' : 'ফাইল নির্বাচন করুন (সর্বোচ্চ ৫ মেগাবাইট)'}
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,.webp"
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-emerald-400 hover:file:bg-slate-700 cursor-pointer"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={uploading || !selectedFile}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-bold text-xs transition-colors shadow-md shadow-emerald-600/20"
                  >
                    {uploading ? (
                      <>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>{isEn ? 'Uploading...' : 'আপলোড হচ্ছে...'}</span>
                      </>
                    ) : (
                      <>
                        <Upload size={14} />
                        <span>{isEn ? 'Upload Document' : 'ডকুমেন্ট আপলোড করুন'}</span>
                      </>
                    )}
                  </button>
                </form>
              </div>
            )}
          </>
        ) : null}
      </div>
    </MemberLayout>
  );
}
