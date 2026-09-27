'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api, DocumentItem } from '@/lib/api';
import {
  FileText,
  Upload,
  Plus,
  Trash2,
  Download,
  CheckCircle,
  AlertCircle,
  FileCode,
} from 'lucide-react';

export default function AdminDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadBusy, setUploadBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [formData, setFormData] = useState({
    title_bn: '',
    title_en: '',
    category: 'SERVICE_RULES',
    description_bn: '',
    version: '1.0',
  });

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await api.getDocuments({ limit: 50 });
      setDocuments(data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleCreateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setMessage({ text: 'অনুগ্রহ করে একটি ফাইল নির্বাচন করুন।', type: 'error' });
      return;
    }

    setUploadBusy(true);
    try {
      // Step 1: Upload file to persistent disk
      const uploaded = await api.uploadDocumentFile(uploadFile);

      // Step 2: Create document record
      await api.createDocument({
        ...formData,
        file_path: uploaded.file_path,
        file_size: uploaded.file_size,
        content_type: uploaded.content_type,
      });

      setMessage({ text: 'নথি সফলভাবে আপলোড ও সংরক্ষিত হয়েছে।', type: 'success' });
      setUploadModalOpen(false);
      setUploadFile(null);
      setFormData({
        title_bn: '',
        title_en: '',
        category: 'SERVICE_RULES',
        description_bn: '',
        version: '1.0',
      });
      fetchDocuments();
    } catch (err: any) {
      setMessage({ text: err.message || 'নথি সংরক্ষণ করা সম্ভব হয়নি।', type: 'error' });
    } finally {
      setUploadBusy(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('আপনি কি নিশ্চিত যে এই নথিটি মুছে ফেলতে চান?')) return;
    try {
      await api.deleteDocument(id);
      setMessage({ text: 'নথি সফলভাবে মুছে ফেলা হয়েছে।', type: 'success' });
      fetchDocuments();
    } catch (err: any) {
      setMessage({ text: err.message || 'মুছে ফেলা সম্ভব হয়নি।', type: 'error' });
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '০ KB';
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <>
      <AdminHeader
        title="প্রাতিষ্ঠানিক ডকুমেন্ট ও প্রকাশনা লাইব্রেরি (Documents Desk)"
        subtitle="অফিসিয়াল সার্ভিস রুলস, নীতিমালার গ্যাজেট, আবেদন ফরম এবং কারিগরি হ্যান্ডবুক প্রকাশনা ব্যবস্থাপনা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Status Toast */}
        {message && (
          <div
            className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between border ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-700'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">
              ✕
            </button>
          </div>
        )}

        {/* Toolbar */}
        <div className="flex justify-between items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <FileText size={18} className="text-primary" />
            <span>সংরক্ষিত প্রাতিষ্ঠানিক নথিপত্র ({documents.length}টি)</span>
          </div>

          <button
            onClick={() => setUploadModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Upload size={14} /> নতুন নথি আপলোড করুন
          </button>
        </div>

        {/* Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">নথির শিরোনাম (Document Title)</th>
                  <th className="p-4">ক্যাটাগরি</th>
                  <th className="p-4">সংস্করণ</th>
                  <th className="p-4">ফাইলের আকার</th>
                  <th className="p-4">মোট ডাউনলোড</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      নথি লোড হচ্ছে...
                    </td>
                  </tr>
                ) : documents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      কোনো নথি পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-bold text-foreground">
                        <div className="flex items-center gap-2">
                          <FileCode size={16} className="text-primary shrink-0" />
                          <span className="line-clamp-1">{doc.title_bn}</span>
                        </div>
                        {doc.title_en && <div className="text-[11px] font-normal text-secondary line-clamp-1 pl-6">{doc.title_en}</div>}
                      </td>
                      <td className="p-4 text-secondary">{doc.category}</td>
                      <td className="p-4 font-mono text-[11px] text-foreground">v{doc.version || '1.0'}</td>
                      <td className="p-4 font-mono text-[11px] text-secondary">{formatFileSize(doc.file_size)}</td>
                      <td className="p-4 font-bold text-foreground">
                        <span className="px-2 py-0.5 rounded-full bg-surface border border-border text-[11px]">
                          {doc.download_count} বার
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <a
                          href={api.getDocumentDownloadUrl(doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded-lg border border-border bg-surface hover:bg-card text-primary inline-flex items-center"
                          title="ডাউনলোড করুন"
                        >
                          <Download size={13} />
                        </a>
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50"
                          title="মুছে ফেলুন"
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Upload Document Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
            <div className="p-5 border-b border-border flex items-center justify-between bg-surface/50">
              <h3 className="text-sm font-bold text-foreground">নতুন অফিসিয়াল নথি আপলোড</h3>
              <button onClick={() => setUploadModalOpen(false)} className="text-secondary text-sm">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDocument} className="p-6 space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">নথির শিরোনাম (বাংলা) *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: পাওয়ার গ্রিড ইঞ্জিনিয়ার্স আচরণ ও শৃঙ্খলা বিধিমালা..."
                  value={formData.title_bn}
                  onChange={(e) => setFormData({ ...formData, title_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-secondary">শিরোনাম (ইংরেজি - ঐচ্ছিক)</label>
                <input
                  type="text"
                  placeholder="Document Title in English..."
                  value={formData.title_en}
                  onChange={(e) => setFormData({ ...formData, title_en: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="font-semibold text-foreground">ক্যাটাগরি</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                  >
                    <option value="SERVICE_RULES">সার্ভিস রুলস (Service Rules)</option>
                    <option value="FORMS">আবেদন ও সার্ভিস ফরম (Forms)</option>
                    <option value="TECHNICAL">কারিগরি নির্দেশিকা (Technical Guide)</option>
                    <option value="WELFARE">কল্যাণ তহবিল ট্রাস্ট (Welfare Trust)</option>
                    <option value="GAZETTE">সরকারি গ্যাজেট ও স্মারক (Gazette)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">সংস্করণ (Version)</label>
                  <input
                    type="text"
                    placeholder="1.0"
                    value={formData.version}
                    onChange={(e) => setFormData({ ...formData, version: e.target.value })}
                    className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">সংক্ষিপ্ত বিবরণ</label>
                <textarea
                  rows={2}
                  placeholder="নথিটির উদ্দেশ্য বা সারসংক্ষেপ..."
                  value={formData.description_bn}
                  onChange={(e) => setFormData({ ...formData, description_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary leading-relaxed"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">ফাইল নির্বাচন করুন (PDF, DOCX, XLSX - Max 25MB) *</label>
                <input
                  required
                  type="file"
                  accept=".pdf,.docx,.xlsx,.png,.jpg"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full p-2 rounded-xl border border-border bg-surface text-xs text-secondary file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:opacity-90 cursor-pointer"
                />
              </div>

              <div className="p-4 border-t border-border flex justify-end gap-2.5 bg-surface/50 -mx-6 -mb-6 mt-4">
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
                >
                  বাতিল
                </button>
                <button
                  type="submit"
                  disabled={uploadBusy || !uploadFile}
                  className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm flex items-center gap-1.5"
                >
                  {uploadBusy ? 'আপলোড হচ্ছে...' : 'আপলোড ও প্রকাশ করুন'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
