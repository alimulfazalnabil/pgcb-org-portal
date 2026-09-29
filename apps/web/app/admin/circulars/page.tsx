'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api, CircularItem } from '@/lib/api';
import { Bookmark, Plus, Sparkles } from 'lucide-react';

export default function AdminCircularsPage() {
  const [circulars, setCirculars] = useState<CircularItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiPreview, setAiPreview] = useState<string | null>(null);
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

  const handleRunAIAssist = async (
    actionType: 'IMPROVE_BN' | 'TRANSLATE_EN' | 'SUMMARY' | 'SEO' | 'SMS'
  ) => {
    if (!formData.title_bn.trim() && !formData.summary_bn.trim()) {
      setAiPreview('অনুগ্রহ করে প্রথমে শিরোনাম বা বিষয়বস্তু লিখুন।');
      return;
    }
    setAiBusy(true);
    try {
      const res = await fetch('/backend/api/v1/admin/ai/content-assist', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title_bn: formData.title_bn,
          title_en: formData.title_en,
          content_bn: formData.summary_bn || formData.title_bn,
          entity_type: 'CIRCULAR',
        }),
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      const s = data.suggestions || {};
      if (actionType === 'IMPROVE_BN') {
        const improved = s.improved_wording?.content_bn || formData.summary_bn;
        setFormData((prev) => ({ ...prev, summary_bn: improved }));
        setAiPreview(`উন্নত বাংলা খসড়া প্রয়োগ করা হয়েছে: ${improved}`);
      } else if (actionType === 'TRANSLATE_EN') {
        const translatedTitle = s.improved_wording?.title_en || formData.title_en;
        const translatedBody = s.translation?.bn_to_en || '';
        setFormData((prev) => ({ ...prev, title_en: translatedTitle }));
        setAiPreview(`English Translation: ${translatedBody}`);
      } else if (actionType === 'SUMMARY') {
        const sumBn = s.summary?.summary_bn || formData.summary_bn;
        setFormData((prev) => ({ ...prev, summary_bn: sumBn }));
        setAiPreview(`সারাংশ তৈরি হয়েছে: ${sumBn}`);
      } else if (actionType === 'SEO') {
        setAiPreview(
          `SEO Title: ${s.seo_metadata?.meta_title} | Slug: ${s.seo_metadata?.suggested_slug} | Desc: ${s.seo_metadata?.meta_description}`
        );
      } else if (actionType === 'SMS') {
        setAiPreview(
          `SMS Notification Draft: ${s.notification_draft?.sms_bn || s.notification_draft?.body_bn}`
        );
      }
    } catch {
      setAiPreview('এআই কনটেন্ট অ্যাসিস্ট্যান্ট এই মুহূর্তে সাড়া দিচ্ছে না।');
    } finally {
      setAiBusy(false);
    }
  };

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
      setAiPreview(null);
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
            onClick={() => {
              setAiPreview(null);
              setCreateModal(true);
            }}
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
            <h3 className="text-sm font-bold text-foreground">নতুন অফিস আদেশ বা সার্কুলার (Circular Editor)</h3>
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
                <label className="font-semibold text-secondary">Title (English - Optional)</label>
                <input
                  type="text"
                  placeholder="Circular title in English..."
                  value={formData.title_en}
                  onChange={(e) => setFormData({ ...formData, title_en: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">সারসংক্ষেপ / মূল বিষয়বস্তু (Content)</label>
                <textarea
                  rows={3}
                  placeholder="সার্কুলারের মূল বিষয়বস্তুর সংক্ষিপ্ত রূপ..."
                  value={formData.summary_bn}
                  onChange={(e) => setFormData({ ...formData, summary_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>

              {/* AI Content Assistant Panel */}
              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-primary flex items-center gap-1.5 text-[11px]">
                    <Sparkles size={13} />
                    <span>AI Assistant (এআই সম্পাদকীয় সহায়তা)</span>
                  </span>
                  {aiBusy && <span className="text-[10px] text-secondary animate-pulse">প্রক্রিয়াকরণ হচ্ছে...</span>}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => handleRunAIAssist('IMPROVE_BN')}
                    className="px-2.5 py-1 rounded-lg bg-card border border-border hover:border-primary text-foreground font-semibold text-[11px] transition"
                  >
                    Improve Bangla
                  </button>
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => handleRunAIAssist('TRANSLATE_EN')}
                    className="px-2.5 py-1 rounded-lg bg-card border border-border hover:border-primary text-foreground font-semibold text-[11px] transition"
                  >
                    Translate English
                  </button>
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => handleRunAIAssist('SUMMARY')}
                    className="px-2.5 py-1 rounded-lg bg-card border border-border hover:border-primary text-foreground font-semibold text-[11px] transition"
                  >
                    Generate Summary
                  </button>
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => handleRunAIAssist('SEO')}
                    className="px-2.5 py-1 rounded-lg bg-card border border-border hover:border-primary text-foreground font-semibold text-[11px] transition"
                  >
                    SEO Description
                  </button>
                  <button
                    type="button"
                    disabled={aiBusy}
                    onClick={() => handleRunAIAssist('SMS')}
                    className="px-2.5 py-1 rounded-lg bg-card border border-border hover:border-primary text-foreground font-semibold text-[11px] transition"
                  >
                    SMS Notification
                  </button>
                </div>
                {aiPreview && (
                  <div className="p-2 rounded-lg bg-card border border-border text-[11px] text-secondary leading-relaxed">
                    {aiPreview}
                  </div>
                )}
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
