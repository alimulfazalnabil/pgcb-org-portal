'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileText,
  Upload,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  FileCheck,
  Eye,
  Download,
  RefreshCw,
  Plus,
  X,
  FileBadge,
  Sparkles,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberDocumentListItem, MemberDocumentSummary } from '@/lib/api/types';

export default function MemberDocumentsPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<MemberDocumentSummary | null>(null);
  const [activeTab, setActiveTab] = useState<'ALL' | 'VERIFIED' | 'PENDING' | 'REJECTED' | 'EXPIRED'>('ALL');

  // Upload modal state
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadType, setUploadType] = useState('NATIONAL_ID');
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Replace modal state
  const [replaceTargetDoc, setReplaceTargetDoc] = useState<MemberDocumentListItem | null>(null);
  const [replaceFile, setReplaceFile] = useState<File | null>(null);
  const [replaceReason, setReplaceReason] = useState('');
  const [replacing, setReplacing] = useState(false);
  const [replaceError, setReplaceError] = useState<string | null>(null);

  const isEn = lang === 'en';

  const loadDocuments = async (tab = activeTab) => {
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getDocumentSummary(tab);
      setSummary(data);
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to load documents' : 'ডকুমেন্ট লোড করতে সমস্যা হয়েছে'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments(activeTab);
  }, [activeTab]);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError(isEn ? 'Please select a file to upload' : 'অনুগ্রহ করে একটি ফাইল নির্বাচন করুন');
      return;
    }
    try {
      setUploading(true);
      setUploadError(null);
      await membersApi.uploadDocument(uploadFile, uploadType, uploadTitle || undefined);
      setUploadModalOpen(false);
      setUploadFile(null);
      setUploadTitle('');
      await loadDocuments(activeTab);
    } catch (err: any) {
      setUploadError(err?.message || (isEn ? 'Upload failed. Ensure valid PDF or image file.' : 'আপলোড ব্যর্থ হয়েছে। সঠিক পিডিএফ বা ইমেজ ফাইল দিন।'));
    } finally {
      setUploading(false);
    }
  };

  const handleReplaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replaceTargetDoc || !replaceFile) {
      setReplaceError(isEn ? 'Please select a replacement file' : 'অনুগ্রহ করে নতুন ফাইল নির্বাচন করুন');
      return;
    }
    try {
      setReplacing(true);
      setReplaceError(null);
      await membersApi.replaceDocument(replaceTargetDoc.id, replaceFile, replaceReason || undefined);
      setReplaceTargetDoc(null);
      setReplaceFile(null);
      setReplaceReason('');
      await loadDocuments(activeTab);
    } catch (err: any) {
      setReplaceError(err?.message || (isEn ? 'Replacement failed' : 'ফাইল প্রতিস্থাপন ব্যর্থ হয়েছে'));
    } finally {
      setReplacing(false);
    }
  };

  const getDocTypeIcon = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'NATIONAL_ID':
      case 'NID':
      case 'PASSPORT':
        return '🪪';
      case 'ACADEMIC_CERTIFICATE':
      case 'ACADEMIC':
      case 'DIPLOMA_CERTIFICATE':
        return '🎓';
      case 'EMPLOYMENT_DOCUMENT':
      case 'APPOINTMENT_LETTER':
        return '🏢';
      case 'SIGNATURE':
        return '✍️';
      default:
        return '📄';
    }
  };

  const getDocTypeLabel = (type: string) => {
    switch (type?.toUpperCase()) {
      case 'NATIONAL_ID':
      case 'NID':
        return isEn ? 'National ID / Passport' : 'জাতীয় পরিচয়পত্র / পাসপোর্ট';
      case 'ACADEMIC_CERTIFICATE':
      case 'ACADEMIC':
        return isEn ? 'Academic Certificate' : 'শিক্ষাগত সনদপত্র';
      case 'EMPLOYMENT_DOCUMENT':
      case 'APPOINTMENT_LETTER':
        return isEn ? 'Employment Document' : 'চাকরির প্রমাণপত্র';
      case 'SIGNATURE':
        return isEn ? 'Digital Signature' : 'স্বাক্ষর';
      default:
        return type;
    }
  };

  const renderStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'VERIFIED' || s === 'APPROVED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {isEn ? '✓ Verified' : '✓ যাচাইকৃত'}
        </span>
      );
    }
    if (s === 'PENDING' || s === 'UNDER_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          <Clock className="w-3.5 h-3.5" />
          {isEn ? '🟡 Under Review' : '🟡 পর্যালোচনাধীন'}
        </span>
      );
    }
    if (s === 'REJECTED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
          <XCircle className="w-3.5 h-3.5" />
          {isEn ? '✕ Rejected' : '✕ প্রত্যাখ্যাত'}
        </span>
      );
    }
    if (s === 'EXPIRED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
          <AlertTriangle className="w-3.5 h-3.5" />
          {isEn ? 'Expired' : 'মেয়াদোত্তীর্ণ'}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
        {status}
      </span>
    );
  };

  return (
    <MemberLayout
      title={isEn ? 'My Documents' : 'আমার ডকুমেন্টস'}
      lang={lang}
      onLangChange={setLang}
      activeTab="documents"
    >
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Bar */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-2 bg-emerald-50 text-emerald-700 rounded-lg">
                <FileCheck className="w-6 h-6" />
              </span>
              <div>
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {isEn ? 'MY DOCUMENTS' : 'আমার ডকুমেন্টস'}
                </h1>
                <p className="text-sm text-slate-500">
                  {isEn ? 'Manage your submitted and issued documents' : 'আপনার জমাকৃত ও অনুমোদিত ডকুমেন্টস পরিচালনা করুন'}
                </p>
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              setUploadError(null);
              setUploadFile(null);
              setUploadModalOpen(true);
            }}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-medium text-sm transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            {isEn ? 'Upload Document' : 'নতুন ডকুমেন্ট আপলোড'}
          </button>
        </div>

        {/* Tab Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 border-b border-slate-200">
          {[
            { key: 'ALL', label_en: 'All', label_bn: 'সকল', count: summary?.total_count },
            { key: 'VERIFIED', label_en: 'Verified', label_bn: 'যাচাইকৃত', count: summary?.verified_count },
            { key: 'PENDING', label_en: 'Pending', label_bn: 'অপেক্ষমাণ', count: summary?.pending_count },
            { key: 'REJECTED', label_en: 'Rejected', label_bn: 'প্রত্যাখ্যাত', count: summary?.rejected_count },
            { key: 'EXPIRED', label_en: 'Expired', label_bn: 'মেয়াদোত্তীর্ণ', count: summary?.expired_count },
          ].map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key as any)}
              className={`px-4 py-2.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap flex items-center gap-2 ${
                activeTab === t.key
                  ? 'bg-emerald-800 text-white shadow-sm'
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              <span>{isEn ? t.label_en : t.label_bn}</span>
              {typeof t.count === 'number' && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    activeTab === t.key ? 'bg-emerald-950 text-emerald-100' : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Error Notification */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Document Cards List */}
        {loading ? (
          <div className="py-20 text-center">
            <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-sm">
              {isEn ? 'Loading documents...' : 'ডকুমেন্ট লোড হচ্ছে...'}
            </p>
          </div>
        ) : summary?.documents.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">
              {isEn ? 'No documents found' : 'কোনো ডকুমেন্ট পাওয়া যায়নি'}
            </h3>
            <p className="text-sm text-slate-500 mt-1">
              {isEn
                ? 'No documents match the selected filter category.'
                : 'নির্বাচিত ফিল্টারে কোনো ডকুমেন্ট পাওয়া যায়নি।'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {summary?.documents.map((doc) => {
              const isRejected = (doc.status || '').toUpperCase() === 'REJECTED';
              return (
                <div
                  key={doc.id}
                  className={`bg-white rounded-xl border p-5 transition-shadow hover:shadow-md flex flex-col justify-between ${
                    isRejected ? 'border-red-300 bg-red-50/20' : 'border-slate-200'
                  }`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <span className="text-3xl p-2 bg-slate-50 border border-slate-100 rounded-xl">
                          {getDocTypeIcon(doc.document_type)}
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-slate-900 text-base">
                              {doc.title || getDocTypeLabel(doc.document_type)}
                            </h3>
                            {doc.version > 1 && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                                v{doc.version}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5 truncate max-w-[260px]">
                            {doc.filename} • {doc.file_size_formatted}
                          </p>
                        </div>
                      </div>
                      <div>{renderStatusBadge(doc.status)}</div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-1">
                      <div className="flex justify-between">
                        <span>{isEn ? 'Document Type:' : 'ডকুমেন্টের ধরণ:'}</span>
                        <span className="font-medium text-slate-700">{getDocTypeLabel(doc.document_type)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>{isEn ? 'Uploaded:' : 'আপলোডের তারিখ:'}</span>
                        <span className="font-medium text-slate-700">
                          {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}
                        </span>
                      </div>
                      {doc.verified_at && (
                        <div className="flex justify-between text-emerald-700">
                          <span>{isEn ? 'Verified on:' : 'যাচাই সম্পন্ন:'}</span>
                          <span className="font-medium">
                            {new Date(doc.verified_at).toLocaleDateString(isEn ? 'en-GB' : 'bn-BD', { day: 'numeric', month: 'short', year: 'numeric' })}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Rejection Alert Box */}
                    {isRejected && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 space-y-1">
                        <div className="flex items-center gap-1.5 font-bold text-red-900">
                          <AlertTriangle className="w-3.5 h-3.5 text-red-700" />
                          <span>{isEn ? 'Rejection Reason:' : 'প্রত্যাখ্যানের কারণ:'}</span>
                        </div>
                        <p>{doc.reviewer_note || (isEn ? 'Document is unreadable or incomplete. Please replace with a clear scan.' : 'ডকুমেন্টটি অস্পষ্ট বা অসম্পূর্ণ। অনুগ্রহ করে পুনরায় পরিষ্কার কপি দিন।')}</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    <Link
                      href={`/member/documents/${doc.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      {isEn ? 'View & Details' : 'বিস্তারিত দেখুন'}
                    </Link>

                    <div className="flex items-center gap-2">
                      <a
                        href={doc.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        {isEn ? 'Download' : 'ডাউনলোড'}
                      </a>

                      {(isRejected || doc.status === 'PENDING') && (
                        <button
                          onClick={() => {
                            setReplaceTargetDoc(doc);
                            setReplaceFile(null);
                            setReplaceReason('');
                            setReplaceError(null);
                          }}
                          className="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                        >
                          <RefreshCw className="w-3.5 h-3.5" />
                          {isEn ? 'Replace' : 'প্রতিস্থাপন'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Upload Modal */}
        {uploadModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
              <div className="px-6 py-4 bg-emerald-800 text-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  <h3 className="font-bold text-lg">
                    {isEn ? 'Upload Member Document' : 'নতুন ডকুমেন্ট আপলোড'}
                  </h3>
                </div>
                <button
                  onClick={() => setUploadModalOpen(false)}
                  className="p-1 rounded hover:bg-emerald-700 text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleUploadSubmit} className="p-6 space-y-4">
                {uploadError && (
                  <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800">
                    {uploadError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    {isEn ? 'Document Type' : 'ডকুমেন্টের ধরণ'} *
                  </label>
                  <select
                    value={uploadType}
                    onChange={(e) => setUploadType(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                    required
                  >
                    <option value="NATIONAL_ID">{isEn ? 'National ID / Passport' : 'জাতীয় পরিচয়পত্র / পাসপোর্ট'}</option>
                    <option value="ACADEMIC_CERTIFICATE">{isEn ? 'Academic / Diploma Certificate' : 'ডিপ্লোমা / শিক্ষাগত সনদ'}</option>
                    <option value="EMPLOYMENT_DOCUMENT">{isEn ? 'PGCB Employment / Office Order' : 'চাকরির নিয়োগপত্র / অফিস আদেশ'}</option>
                    <option value="SIGNATURE">{isEn ? 'Official Signature Scan' : 'স্বাক্ষরের স্ক্যান'}</option>
                    <option value="OTHER">{isEn ? 'Other Supporting Document' : 'অন্যান্য সহায়ক ডকুমেন্ট'}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    {isEn ? 'Document Title (Optional)' : 'ডকুমেন্টের শিরোনাম (ঐচ্ছিক)'}
                  </label>
                  <input
                    type="text"
                    value={uploadTitle}
                    onChange={(e) => setUploadTitle(e.target.value)}
                    placeholder={isEn ? 'e.g., National ID Front & Back Scan' : 'যেমন: জাতীয় পরিচয়পত্র স্ক্যান'}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    {isEn ? 'Select File' : 'ফাইল নির্বাচন করুন'} *
                  </label>
                  <input
                    type="file"
                    accept=".pdf,image/png,image/jpeg,image/webp"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer"
                    required
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    {isEn
                      ? 'Supported formats: PDF (up to 10MB), PNG, JPG, WebP (up to 5MB).'
                      : 'অনুমোদিত ফরম্যাট: পিডিএফ (সর্বোচ্চ ১০ এমবি), পিএনজি, জেপিজি (সর্বোচ্চ ৫ এমবি)।'}
                  </p>
                </div>

                <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setUploadModalOpen(false)}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    {isEn ? 'Cancel' : 'বাতিল'}
                  </button>
                  <button
                    type="submit"
                    disabled={uploading}
                    className="px-5 py-2 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50"
                  >
                    {uploading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    {isEn ? 'Upload Now' : 'আপলোড সম্পন্ন করুন'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Replace Modal */}
        {replaceTargetDoc && (
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
                  onClick={() => setReplaceTargetDoc(null)}
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

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700">
                  <p className="font-bold">{replaceTargetDoc.title || replaceTargetDoc.filename}</p>
                  <p className="text-slate-500 mt-0.5">
                    {isEn ? 'Current Version:' : 'বর্তমান সংস্করণ:'} v{replaceTargetDoc.version} • {getDocTypeLabel(replaceTargetDoc.document_type)}
                  </p>
                </div>

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
                      ? 'Replaces document and automatically increments version number.'
                      : 'ফাইলটি প্রতিস্থাপনের সাথে সাথে নতুন সংস্করণ (v2, v3...) রেকর্ড হবে।'}
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
                    placeholder={isEn ? 'e.g., Uploading clearer attested scan per reviewer comment' : 'যেমন: যাচাইকারীর অনুরোধে স্পষ্ট কপি প্রদান করা হলো'}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                  />
                </div>

                <div className="pt-3 flex items-center justify-end gap-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setReplaceTargetDoc(null)}
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
