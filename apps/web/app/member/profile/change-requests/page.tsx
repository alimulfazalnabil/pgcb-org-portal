'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  User,
  ShieldCheck,
  CreditCard,
  FileText,
  FileCheck,
  Award,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  Languages,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ChevronRight,
  ArrowLeft,
  FileEdit,
  Plus,
  Upload,
  Check,
  Trash2,
  Layers,
  Lock,
  ExternalLink,
  Info,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MemberProfile, ProfileChangeRequest } from '@/lib/api/types';

const PROTECTED_FIELDS = [
  { value: 'name_en', labelEn: 'Full Name (English)', labelBn: 'পূর্ণ নাম (ইংরেজি)' },
  { value: 'name_bn', labelEn: 'Full Name (Bangla)', labelBn: 'পূর্ণ নাম (বাংলা)' },
  { value: 'date_of_birth', labelEn: 'Date of Birth (YYYY-MM-DD)', labelBn: 'জন্ম তারিখ' },
  { value: 'nid_number', labelEn: 'National ID / Passport Number', labelBn: 'জাতীয় পরিচয়পত্র / পাসপোর্ট নম্বর' },
  { value: 'grid_circle', labelEn: 'Grid Circle Transfer', labelBn: 'গ্রিড সার্কেল পরিবর্তন' },
];

export default function MemberProfileChangeRequestsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [requests, setRequests] = useState<ProfileChangeRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<'bn' | 'en'>('en');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // New Request Form State
  const [fieldName, setFieldName] = useState('name_en');
  const [requestedValue, setRequestedValue] = useState('');
  const [reason, setReason] = useState('');
  const [supportingDocUrl, setSupportingDocUrl] = useState<string | null>(null);
  const [supportingDocId, setSupportingDocId] = useState<number | null>(null);
  const [supportingDocName, setSupportingDocName] = useState<string | null>(null);

  const isEn = lang === 'en';

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [profData, crData] = await Promise.all([
          api.getProfile(),
          api.getProfileChangeRequests(),
        ]);
        setProfile(profData);
        if (profData.preferred_language === 'bn') {
          setLang('bn');
        }
        setRequests(crData.items || crData.change_requests || []);
      } catch (err: any) {
        if (err?.status === 401) {
          router.push('/login?redirect=/member/profile/change-requests');
          return;
        }
        setError(err?.message || 'Failed to load change requests');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [router]);

  // Derive current value of the selected protected field
  const getCurrentValue = (fName: string): string => {
    if (!profile) return '—';
    const pInfo = profile.personal_information || {};
    const cInfo = profile.contact_information || {};
    switch (fName) {
      case 'name_en':
        return pInfo.name_en || profile.name_en || '—';
      case 'name_bn':
        return pInfo.name_bn || profile.name_bn || '—';
      case 'date_of_birth':
        return pInfo.date_of_birth || profile.date_of_birth || '—';
      case 'nid_number':
        return pInfo.nid_number || profile.nid_number || '—';
      case 'grid_circle':
        return cInfo.circle_en || profile.circle_en || String(profile.circle_id || '—');
      default:
        return '—';
    }
  };

  const handleDocumentSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setError(
        isEn
          ? 'Supporting document exceeds 5MB limit.'
          : 'সংযুক্ত ফাইলের আকার ৫ মেগাবাইটের বেশি।'
      );
      return;
    }

    try {
      setUploadingDoc(true);
      const res = await api.uploadMemberDocument('OTHER', file);
      if (res?.document) {
        setSupportingDocId(res.document.id);
        setSupportingDocUrl(res.document.file_path || res.document.url);
        setSupportingDocName(file.name);
      } else if (res?.id) {
        setSupportingDocId(res.id);
        setSupportingDocUrl(res.file_path || res.url);
        setSupportingDocName(file.name);
      }
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to upload supporting document.' : 'ডকুমেন্ট আপলোড ব্যর্থ হয়েছে।'));
    } finally {
      setUploadingDoc(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleCreateRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requestedValue.trim()) {
      setError(isEn ? 'Please enter the requested new value.' : 'অনুগ্রহ করে নতুন তথ্য লিখুন।');
      return;
    }

    setError(null);
    setSuccessMsg(null);
    setSubmitting(true);

    try {
      const payload: any = {
        field_name: fieldName,
        requested_value: requestedValue.trim(),
        reason: reason.trim() || 'Requested via Member Portal',
      };
      if (supportingDocUrl) {
        payload.supporting_doc_url = supportingDocUrl;
      }
      if (supportingDocId) {
        payload.supporting_document_id = supportingDocId;
      }

      const res = await api.createProfileChangeRequest(payload);
      setRequests((prev) => [res, ...prev]);
      setSuccessMsg(
        isEn
          ? 'Change request submitted successfully for Secretariat review!'
          : 'সংশোধন আবেদন সফলভাবে সচিবালয় পর্যালোচনার জন্য জমা হয়েছে!'
      );
      setModalOpen(false);
      setRequestedValue('');
      setReason('');
      setSupportingDocUrl(null);
      setSupportingDocId(null);
      setSupportingDocName(null);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to submit change request.' : 'আবেদন জমা দিতে সমস্যা হয়েছে।'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelRequest = async (id: number) => {
    if (!confirm(isEn ? 'Are you sure you want to cancel this pending change request?' : 'আপনি কি নিশ্চিত যে এই আবেদনটি বাতিল করতে চান?')) {
      return;
    }

    setCancellingId(id);
    setError(null);
    setSuccessMsg(null);

    try {
      await api.cancelProfileChangeRequest(id);
      setRequests((prev) =>
        prev.map((r) => (r.id === id ? { ...r, status: 'CANCELLED' } : r))
      );
      setSuccessMsg(isEn ? 'Change request cancelled.' : 'আবেদন বাতিল করা হয়েছে।');
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to cancel change request.' : 'আবেদন বাতিল করা যায়নি।'));
    } finally {
      setCancellingId(null);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      router.push('/login');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-slate-400 font-medium text-sm">
            {isEn ? 'Loading change requests...' : 'আবেদনসমূহ লোড হচ্ছে...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link href="/member/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-emerald-600/30">
              P
            </div>
            <div className="hidden sm:block">
              <span className="font-extrabold tracking-tight text-white text-sm">PGCB</span>
              <span className="text-emerald-400 font-bold text-xs ml-1.5 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/50">
                MEMBER PORTAL
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-2.5 sm:gap-3">
          <button
            onClick={() => setLang((prev) => (prev === 'en' ? 'bn' : 'en'))}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 hover:border-slate-600 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            <Languages size={15} />
            <span className="uppercase">{lang}</span>
          </button>

          <Link
            href="/member/profile"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-bold transition-colors"
          >
            <ArrowLeft size={14} />
            <span>{isEn ? 'View Profile' : 'প্রোফাইল'}</span>
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside
          className={`lg:w-64 bg-slate-900/60 lg:bg-slate-900/30 border-r border-slate-800/80 p-4 lg:p-6 shrink-0 transition-all duration-300 ${
            mobileMenuOpen ? 'block' : 'hidden lg:block'
          }`}
        >
          <div className="space-y-1">
            <Link
              href="/member/dashboard"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Layers size={18} />
              <span>{isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}</span>
            </Link>

            <Link
              href="/member/profile"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <User size={18} />
              <span>{isEn ? 'My Profile' : 'আমার প্রোফাইল'}</span>
            </Link>

            <Link
              href="/member/profile/edit"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors pl-8 text-xs"
            >
              <FileEdit size={15} />
              <span>{isEn ? 'Edit Profile' : 'তথ্য পরিবর্তন'}</span>
            </Link>

            <Link
              href="/member/profile/change-requests"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm bg-emerald-600/15 border border-emerald-500/30 text-emerald-300 transition-colors pl-8 text-xs"
            >
              <ShieldCheck size={15} className="text-emerald-400" />
              <span>{isEn ? 'Change Requests' : 'ভেরিফিকেশন আবেদন'}</span>
            </Link>

            <div className="pt-4 mt-4 border-t border-slate-800/80 space-y-1">
              <Link
                href="/portal?tab=settings"
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <Settings size={18} />
                <span>{isEn ? 'Settings' : 'সেটিংস'}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:bg-rose-500/10 transition-colors text-left"
              >
                <LogOut size={18} />
                <span>{isEn ? 'Sign Out' : 'লগ আউট'}</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Content Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto w-full space-y-6">
          {/* Header & New Request Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs text-slate-400 font-medium mb-1">
                <Link href="/member/dashboard" className="hover:text-slate-200">
                  {isEn ? 'Portal' : 'পোর্টাল'}
                </Link>
                <ChevronRight size={13} />
                <Link href="/member/profile" className="hover:text-slate-200">
                  {isEn ? 'Profile' : 'প্রোফাইল'}
                </Link>
                <ChevronRight size={13} />
                <span className="text-emerald-400 font-bold">{isEn ? 'Change Requests' : 'পরিবর্তন আবেদন'}</span>
              </div>
              <h1 className="text-2xl font-black text-white tracking-tight">
                {isEn ? 'Profile Change Requests' : 'সুরক্ষিত তথ্য পরিবর্তন আবেদন'}
              </h1>
            </div>

            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-all shadow-lg shadow-emerald-600/30 self-start sm:self-auto"
            >
              <Plus size={16} />
              <span>{isEn ? 'New Change Request' : 'নতুন আবেদন জমা দিন'}</span>
            </button>
          </div>

          {/* Feedback Alerts */}
          {successMsg && (
            <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 flex items-center gap-3 text-sm">
              <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}
          {error && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center gap-3 text-sm">
              <AlertCircle size={18} className="text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Info Card */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex items-start gap-3.5">
            <Lock size={20} className="text-emerald-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs leading-relaxed text-slate-300">
              <p className="font-bold text-white text-sm">
                {isEn ? 'How Profile Change Requests Work' : 'তথ্য সংশোধন প্রক্রিয়া'}
              </p>
              <p className="text-slate-400">
                {isEn
                  ? 'To maintain institutional compliance and the authenticity of your Digital ID card, modifications to critical identity attributes (Full Name, Date of Birth, NID, and Grid Circle) require document validation. Once submitted, requests are reviewed by Central Secretariat Officers.'
                  : 'ডিজিটাল আইডি কার্ড ও সাংগঠনিক রেকর্ডের বিশ্বস্ততা বজায় রাখতে মূল পরিচিতি তথ্য (নাম, জন্ম তারিখ, এনআইডি, সার্কেল) পরিবর্তনের ক্ষেত্রে প্রাসঙ্গিক ডকুমেন্ট যাচাই করা হয়। আবেদন জমা হওয়ার পর কেন্দ্রীয় সচিবালয়ের কর্মকর্তা পর্যালোচনা ও অনুমোদন প্রদান করবেন।'}
              </p>
            </div>
          </div>

          {/* Change Requests History Table */}
          <div className="rounded-2xl bg-slate-900/80 border border-slate-800 overflow-hidden shadow-xl">
            <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between">
              <h2 className="font-extrabold text-sm sm:text-base text-white flex items-center gap-2">
                <FileCheck size={18} className="text-emerald-400" />
                <span>{isEn ? 'Submission History' : 'আবেদনের বিবরণ'}</span>
              </h2>
              <span className="text-xs text-slate-400 font-medium">
                {requests.length} {isEn ? 'Requests total' : 'টি আবেদন'}
              </span>
            </div>

            {requests.length === 0 ? (
              <div className="p-12 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-slate-500">
                  <FileText size={22} />
                </div>
                <h3 className="text-sm font-bold text-slate-300">
                  {isEn ? 'No change requests submitted yet' : 'কোনো আবেদন জমা দেওয়া হয়নি'}
                </h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  {isEn
                    ? 'When you need to update protected identity fields, click "New Change Request" above.'
                    : 'সুরক্ষিত তথ্য সংশোধনের জন্য উপরের "নতুন আবেদন জমা দিন" বাটনে ক্লিক করুন।'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-800/60 text-slate-400 font-bold uppercase tracking-wider text-[11px] border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3">ID</th>
                      <th className="px-4 py-3">{isEn ? 'Field' : 'ক্ষেত্র'}</th>
                      <th className="px-4 py-3">{isEn ? 'Current Value' : 'বর্তমান মান'}</th>
                      <th className="px-4 py-3">{isEn ? 'Requested Value' : 'প্রস্তাবিত মান'}</th>
                      <th className="px-4 py-3">{isEn ? 'Status' : 'অবস্থা'}</th>
                      <th className="px-4 py-3">{isEn ? 'Submitted' : 'তারিখ'}</th>
                      <th className="px-4 py-3">{isEn ? 'Reviewer Note' : 'মন্তব্য'}</th>
                      <th className="px-4 py-3 text-right">{isEn ? 'Actions' : 'অ্যাকশন'}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-200">
                    {requests.map((r) => {
                      const statusColors: Record<string, string> = {
                        PENDING: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
                        UNDER_REVIEW: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
                        APPROVED: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
                        REJECTED: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
                        CANCELLED: 'bg-slate-700/30 text-slate-400 border-slate-700',
                      };

                      return (
                        <tr key={r.id} className="hover:bg-slate-800/30 transition-colors">
                          <td className="px-4 py-3 font-mono font-bold text-slate-400">#{r.id}</td>
                          <td className="px-4 py-3 font-semibold text-white">
                            {isEn ? r.field_label_en || r.field_name : r.field_label_bn || r.field_name}
                          </td>
                          <td className="px-4 py-3 text-slate-400 max-w-[140px] truncate">
                            {r.current_value || '—'}
                          </td>
                          <td className="px-4 py-3 font-bold text-emerald-400 max-w-[180px] truncate">
                            {r.requested_value}
                          </td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${
                                statusColors[r.status] || 'bg-slate-800 text-slate-300 border-slate-700'
                              }`}
                            >
                              {r.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400 whitespace-nowrap">
                            {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                          </td>
                          <td className="px-4 py-3 text-slate-400 max-w-[160px] truncate">
                            {r.reviewer_comment || r.reviewer_note || r.review_note || '—'}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {r.status === 'PENDING' && (
                              <button
                                onClick={() => handleCancelRequest(r.id)}
                                disabled={cancellingId === r.id}
                                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-bold transition-colors"
                              >
                                {cancellingId === r.id ? '...' : isEn ? 'Cancel' : 'বাতিল'}
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Submit Change Request Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-lg w-full bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileEdit size={20} className="text-emerald-400" />
                <h3 className="font-extrabold text-base text-white">
                  {isEn ? 'Submit Profile Change Request' : 'নতুন পরিবর্তন আবেদন'}
                </h3>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateRequest} className="space-y-4 text-xs">
              {/* Field Select */}
              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  {isEn ? 'Protected Field to Modify *' : 'পরিবর্তনযোগ্য সংরক্ষিত ক্ষেত্র *'}
                </label>
                <select
                  value={fieldName}
                  onChange={(e) => setFieldName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                >
                  {PROTECTED_FIELDS.map((f) => (
                    <option key={f.value} value={f.value}>
                      {isEn ? f.labelEn : f.labelBn}
                    </option>
                  ))}
                </select>
              </div>

              {/* Current Value Display */}
              <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800">
                <span className="text-slate-400 block text-[11px] mb-0.5">
                  {isEn ? 'Current Record Value:' : 'বর্তমানে সংরক্ষিত তথ্য:'}
                </span>
                <span className="font-bold text-slate-200 block truncate">
                  {getCurrentValue(fieldName)}
                </span>
              </div>

              {/* Requested Value Input */}
              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  {isEn ? 'Requested New Value *' : 'সংশোধিত নতুন মান *'}
                </label>
                <input
                  type="text"
                  required
                  value={requestedValue}
                  onChange={(e) => setRequestedValue(e.target.value)}
                  placeholder={isEn ? 'Enter the exact correct value' : 'সঠিক তথ্যটি এখানে লিখুন'}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>

              {/* Reason / Justification */}
              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  {isEn ? 'Reason / Justification' : 'আবেদনের কারণ বা বিবরণ'}
                </label>
                <textarea
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder={
                    isEn
                      ? 'e.g. Updating name as per new National ID card or Gazette'
                      : 'উদাহরণ: নতুন জাতীয় পরিচয়পত্র বা প্রজ্ঞাপন অনুযায়ী নাম পরিবর্তন'
                  }
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none"
                />
              </div>

              {/* Supporting Document Upload */}
              <div>
                <label className="block text-slate-300 font-bold mb-1.5">
                  {isEn ? 'Supporting Document (PDF, JPG, PNG - Max 5MB)' : 'সমর্থনকারী নথি (পিডিএফ বা ছবি - সর্বোচ্চ ৫MB)'}
                </label>
                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf,image/jpeg,image/png"
                    onChange={handleDocumentSelect}
                    className="hidden"
                  />
                  <button
                    type="button"
                    disabled={uploadingDoc}
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold"
                  >
                    <Upload size={14} />
                    <span>
                      {uploadingDoc
                        ? isEn
                          ? 'Uploading...'
                          : 'আপলোড হচ্ছে...'
                        : isEn
                        ? 'Attach Document'
                        : 'নথি সংযুক্ত করুন'}
                    </span>
                  </button>
                  {supportingDocName && (
                    <span className="text-emerald-400 font-medium truncate max-w-[200px]">
                      ✓ {supportingDocName}
                    </span>
                  )}
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold"
                >
                  {isEn ? 'Cancel' : 'বাতিল'}
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold transition-all shadow-md shadow-emerald-600/30"
                >
                  {submitting && (
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  )}
                  <span>{isEn ? 'Submit Request' : 'আবেদন জমা দিন'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
