'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api, CircularItem } from '@/lib/api';
import { Bookmark, Plus, Trash2, Calendar, FileText } from 'lucide-react';

export default function AdminCircularsPage() {
  const [circulars, setCirculars] = useState<CircularItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [formData, setFormData] = useState({
    title_bn: '',
    title_en: '',
    reference_no: '',
    category: 'CIRCULAR',
    summary_bn: '',
    document_url: '',
    priority: 100,
    is_published: true,
  });

  const fetchCirculars = async () => {
    setLoading(true);
    try {
      const data = await api.getCirculars({ limit: 50 });
      setCirculars(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCirculars();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const res = await fetch('/backend/api/v1/admin/circulars', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('সার্কুলার তৈরি করা সম্ভব হয়নি।');
      setMessage({ text: 'সার্কুলার সফলভাবে সংরক্ষিত হয়েছে।', type: 'success' });
      setCreateModal(false);
      fetchCirculars();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="সার্কুলার ও অফিস আদেশ (Official Circulars)"
        subtitle="সাংগঠনিক নীতিমালা, নির্বাহী সার্কুলার এবং সাধারণ নির্দেশনা ব্যবস্থাপনা"
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
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">✕</button>
          </div>
        )}

        <div className="flex justify-between items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <Bookmark size={18} className="text-primary" />
            <span>প্রকাশিত সার্কুলারের তালিকা ({circulars.length}টি)</span>
          </div>

          <button
            onClick={() => setCreateModal(true)}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Plus size={14} /> নতুন সার্কুলার যোগ করুন
          </button>
        </div>

        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">স্মারক নং (Reference)</th>
                  <th className="p-4">শিরোনাম (Title)</th>
                  <th className="p-4">ক্যাটাগরি</th>
                  <th className="p-4">প্রকাশের তারিখ</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">সার্কুলার লোড হচ্ছে...</td></tr>
                ) : circulars.length === 0 ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">কোনো সার্কুলার পাওয়া যায়নি।</td></tr>
                ) : (
                  circulars.map((c) => (
                    <tr key={c.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-mono font-bold text-foreground">{c.reference_no || 'N/A'}</td>
                      <td className="p-4 font-bold text-foreground">{c.title_bn}</td>
                      <td className="p-4 text-secondary">{c.category}</td>
                      <td className="p-4 font-mono text-[11px] text-secondary">{c.published_at?.slice(0, 10) || 'খসড়া'}</td>
                      <td className="p-4 text-right">
                        <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 font-semibold text-[11px]">
                          সক্রিয়
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {createModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-xl rounded-2xl shadow-2xl p-6 space-y-4 text-xs">
            <h3 className="text-sm font-bold text-foreground">নতুন অফিস আদেশ বা সার্কুলার</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="font-semibold text-foreground">স্মারক নম্বর *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: PGDA/2026/085"
                  value={formData.reference_no}
                  onChange={(e) => setFormData({ ...formData, reference_no: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground font-mono focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">শিরোনাম (বাংলা) *</label>
                <input
                  required
                  type="text"
                  placeholder="সার্কুলারের বিষয় বা শিরোনাম..."
                  value={formData.title_bn}
                  onChange={(e) => setFormData({ ...formData, title_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">সারসংক্ষেপ</label>
                <textarea
                  rows={3}
                  placeholder="সার্কুলারের মূল বিষয়বস্তুর সংক্ষিপ্ত রূপ..."
                  value={formData.summary_bn}
                  onChange={(e) => setFormData({ ...formData, summary_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface"
                >
                  বাতিল
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-5 py-2 rounded-xl bg-primary text-white font-bold disabled:opacity-50"
                >
                  {busy ? 'সংরক্ষণ হচ্ছে...' : 'প্রকাশ করুন'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
