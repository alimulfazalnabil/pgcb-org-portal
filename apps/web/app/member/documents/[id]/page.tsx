'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  FileText,
  ArrowLeft,
  Download,
  Eye,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  RefreshCw,
  History,
  ShieldCheck,
  Calendar,
  Layers,
  FileCode,
  X,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberDocumentDetail } from '@/lib/api/types';

export default function MemberDocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const docId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [doc, setDoc] = useState<MemberDocumentDetail | null>(null);

  // Replace modal
  const [replaceModalOpen, setReplaceModalOpen] = useState(false);
  const [replaceFile, setReplaceFile] = useState<File | null>(null);
  const [replaceReason, setReplaceReason] = useState('');
  const [replacing, setReplacing] = useState(false);
  const [replaceError, setReplaceError] = useState<string | null>(null);

  const isEn = lang === 'en';

  const loadDetail = async () => {
    if (!docId || isNaN(docId)) return;
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getDocumentDetail(docId);
      setDoc(data);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to load document details' : 'ডকুমেন্ট তথ্য লোড করা যায়নি'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [docId]);

  const handleReplaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replaceFile) {
      setReplaceError(isEn ? 'Please select a replacement file' : 'অনুগ্রহ করে নতুন ফাইল নির্বাচন করুন');
      return;
    }
    try {
      setReplacing(true);
      setReplaceError(null);
      await membersApi.replaceDocument(docId, replaceFile, replaceReason || undefined);
      setReplaceModalOpen(false);
      setReplaceFile(null);
      setReplaceReason('');
      await loadDetail();
    } catch (err: any) {
      setReplaceError(err?.message || (isEn ? 'Replacement failed' : 'ফাইল প্রতিস্থাপন ব্যর্থ হয়েছে'));
    } finally {
      setReplacing(false);
    }
  };

  const isPdf = doc?.filename.toLowerCase().endsWith('.pdf');
  const isRejected = (doc?.status || '').toUpperCase() === 'REJECTED';

  return (
    <MemberLayout
      title={doc?.title || (isEn ? 'Document Details' : 'ডকুমেন্ট বিবরণ')}
      lang={lang}
      onLangChange={setLang}
      activeTab="documents"
    >
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/member/documents"
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-emerald-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            {isEn ? 'Back to All Documents' : 'সকল ডকুমেন্টে ফিরে যান'}
          </Link>

          <div className="flex items-center gap-2">
            {doc && (
              <a
                href={doc.download_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-sm transition-colors"
              >
                <Download className="w-4 h-4" />
                {isEn ? 'Download Original' : 'মূল ফাইল ডাউনলোড'}
              </a>
            )}

            {(isRejected || doc?.status === 'PENDING') && (
              <button
                onClick={() => {
                  setReplaceFile(null);
                  setReplaceReason('');
                  setReplaceError(null);
                  setReplaceModalOpen(true);
                }}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-300 text-xs font-semibold transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                {isEn ? 'Replace Document' : 'ডকুমেন্ট প্রতিস্থাপন'}
              </button>
            )}
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
              {isEn ? 'Loading document details...' : 'ডকুমেন্ট তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        ) : !doc ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">
              {isEn ? 'Document not found' : 'ডকুমেন্ট পাওয়া যায়নি'}
            </h3>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Document Viewer */}
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-emerald-700" />
                    <span className="font-bold text-slate-800 text-sm">
                      {isEn ? 'Live Document Preview' : 'ডকুমেন্ট প্রিভিউ'}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500">
                    {doc.filename}
                  </span>
                </div>

                <div className="p-4 bg-slate-100 min-h-[500px] flex items-center justify-center">
                  {isPdf ? (
                    <iframe
                      src={doc.preview_url}
                      className="w-full h-[600px] rounded-lg border border-slate-300 bg-white"
                      title={doc.title}
                    />
                  ) : (
                    <div className="max-w-full max-h-[600px] overflow-auto flex items-center justify-center p-2 bg-white rounded-lg border border-slate-200 shadow-inner">
                      <img
                        src={doc.preview_url}
                        alt={doc.title}
                        className="max-h-[550px] object-contain rounded"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Version History */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                  <History className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-base">
                    {isEn ? 'Immutable Version History' : 'সংস্করণ ইতিহাস (Version History)'}
                  </h3>
                </div>

                {doc.versions?.length === 0 ? (
                  <p className="text-xs text-slate-500">
                    {isEn ? 'No previous versions recorded.' : 'পূর্বের কোনো সংস্করণ নেই।'}
                  </p>
                ) : (
                  <div className="space-y-3">
                    {doc.versions.map((ver) => (
                      <div
                        key={ver.id}
                        className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 rounded font-bold bg-blue-100 text-blue-800">
                            v{ver.version_number}
                          </span>
                          <div>
                            <p className="font-semibold text-slate-800">{ver.filename}</p>
                            <p className="text-slate-500">
                              {new Date(ver.created_at).toLocaleString(isEn ? 'en-GB' : 'bn-BD')} • {(ver.file_size / 1024).toFixed(1)} KB
                            </p>
                            {ver.replacement_reason && (
                              <p className="text-slate-600 mt-1 italic">
                                "{ver.replacement_reason}"
                              </p>
                            )}
                          </div>
                        </div>

                        <a
                          href={ver.download_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold"
                        >
                          {isEn ? 'Download v' + ver.version_number : 'ডাউনলোড v' + ver.version_number}
                        </a>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right 1 Col: Metadata & Verification Timeline */}
            <div className="space-y-6">
              {/* Document Overview Card */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
                <h3 className="font-bold text-slate-900 text-base pb-2 border-b border-slate-100">
                  {isEn ? 'Document Information' : 'ডকুমেন্ট তথ্যাবলী'}
                </h3>

                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-slate-500 block">{isEn ? 'Title' : 'শিরোনাম'}</span>
                    <span className="font-bold text-slate-900 text-sm">{doc.title}</span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">{isEn ? 'Document Type' : 'ডকুমেন্টের ধরণ'}</span>
                    <span className="font-medium text-slate-800">{doc.document_type}</span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">{isEn ? 'Current Status' : 'বর্তমান স্থিতি'}</span>
                    <div className="mt-1">
                      {isRejected ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-50 text-red-700 border border-red-200 inline-block">
                          ✕ {isEn ? 'Rejected' : 'প্রত্যাখ্যাত'}
                        </span>
                      ) : (doc.status || '').toUpperCase() === 'VERIFIED' ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 inline-block">
                          ✓ {isEn ? 'Verified' : 'যাচাইকৃত'}
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 inline-block">
                          🟡 {isEn ? 'Under Review' : 'পর্যালোচনাধীন'}
                        </span>
                      )}
                    </div>
                  </div>

                  <div>
                    <span className="text-slate-500 block">{isEn ? 'Current Version' : 'বর্তমান সংস্করণ'}</span>
                    <span className="font-semibold text-slate-800">Version {doc.version}</span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">{isEn ? 'File Size' : 'ফাইলের আকার'}</span>
                    <span className="font-medium text-slate-800">{doc.file_size_formatted}</span>
                  </div>

                  <div>
                    <span className="text-slate-500 block">{isEn ? 'Uploaded At' : 'আপলোডের সময়'}</span>
                    <span className="font-medium text-slate-800">
                      {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleString(isEn ? 'en-GB' : 'bn-BD') : 'N/A'}
                    </span>
                  </div>

                  {doc.verified_at && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900">
                      <span className="font-bold block">{isEn ? 'Verified At:' : 'যাচাই সম্পন্ন:'}</span>
                      <span>{new Date(doc.verified_at).toLocaleString(isEn ? 'en-GB' : 'bn-BD')}</span>
                    </div>
                  )}

                  {isRejected && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-900 space-y-1">
                      <span className="font-bold block flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-red-700" />
                        {isEn ? 'Rejection Reason:' : 'প্রত্যাখ্যানের কারণ:'}
                      </span>
                      <p>{doc.reviewer_note || (isEn ? 'Document rejected during administrative review.' : 'প্রশাসনিক পর্যালোচনায় ডকুমেন্টটি প্রত্যাখ্যাত হয়েছে।')}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Verification Audit Timeline */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-100">
                  <ShieldCheck className="w-5 h-5 text-emerald-700" />
                  <h3 className="font-bold text-slate-900 text-sm">
                    {isEn ? 'Audit & Verification Trail' : 'যাচাইকরণ লগ ও অডিট'}
                  </h3>
                </div>

                {doc.verification_history?.length === 0 ? (
                  <p className="text-xs text-slate-500">
                    {isEn ? 'No verification events recorded yet.' : 'এখনও কোনো যাচাইকরণ রেকর্ড নেই।'}
                  </p>
                ) : (
                  <div className="space-y-4 text-xs">
                    {doc.verification_history.map((evt, idx) => (
                      <div key={evt.id || idx} className="relative pl-5 border-l-2 border-emerald-200 pb-3 last:pb-0">
                        <div className="absolute -left-[5px] top-0 w-2 h-2 rounded-full bg-emerald-600" />
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-800">{evt.action}</span>
                          <span className="text-[10px] text-slate-400">
                            {new Date(evt.created_at).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD')}
                          </span>
                        </div>
                        <p className="text-slate-500 text-[11px] mt-0.5">
                          {isEn ? 'By:' : 'কর্তৃক:'} {evt.actor_name} ({evt.actor_role})
                        </p>
                        {evt.notes && (
                          <p className="text-slate-700 bg-slate-50 p-2 rounded mt-1 border border-slate-100">
                            {evt.notes}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Replace Modal */}
        {replaceModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
              <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-5 h-5 text-emerald-400" />
                  <h3 className="font-bold text-lg">
                    {isEn ? 'Replace Document' : 'ডকুমেন্ট প্রতিস্থাপন'}
                  </h3>
                </div>
                <button
                  onClick={() => setReplaceModalOpen(false)}
                  className="p-1 rounded hover:bg-slate-800 text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleReplaceSubmit} className="p-6 space-y-4">
                {replaceError && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800">
                    {replaceError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    {isEn ? 'New File' : 'নতুন ফাইল'} *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,image/png,image/jpeg,image/webp"
                    onChange={(e) => setReplaceFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer"
                    required
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    {isEn
                      ? 'Replaces the document and records a new immutable version.'
                      : 'ফাইলটি প্রতিস্থাপনের সাথে সাথে নতুন অপরিবর্তনীয় সংস্করণ তৈরি হবে।'}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    {isEn ? 'Replacement Reason / Note (Optional)' : 'প্রতিস্থাপনের কারণ / নোট (ঐচ্ছিক)'}
                  </label>
                  <textarea
                    rows={2}
                    value={replaceReason}
                    onChange={(e) => setReplaceReason(e.target.value)}
                    placeholder={isEn ? 'e.g., Clearer scan uploaded' : 'যেমন: স্পষ্ট কপি প্রদান করা হলো'}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                  />
                </div>

                <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setReplaceModalOpen(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    {isEn ? 'Cancel' : 'বাতিল'}
                  </button>
                  <button
                    type="submit"
                    disabled={replacing}
                    className="px-5 py-2 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    {replacing && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    {isEn ? 'Confirm Replacement' : 'প্রতিস্থাপন নিশ্চিত করুন'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
