'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { api, Notice } from '@/lib/api';
import {
  Bell,
  Plus,
  Pin,
  Trash2,
  Edit,
  Sparkles,
} from 'lucide-react';

export default function AdminNoticesPage() {
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingNotice, setEditingNotice] = useState<Notice | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formBusy, setFormBusy] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiPreview, setAiPreview] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [formData, setFormData] = useState({
    title_bn: '',
    title_en: '',
    content_bn: '',
    content_en: '',
    category: 'GENERAL',
    priority: 'NORMAL' as 'NORMAL' | 'HIGH' | 'URGENT',
    is_pinned: false,
    is_published: true,
    attachment_url: '',
  });

  const fetchNotices = async () => {
    setLoading(true);
    try {
      const data = await api.getNotices({ limit: 50 });
      setNotices(data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotices();
  }, []);

  const handleRunAIAssist = async (
    actionType: 'IMPROVE_BN' | 'TRANSLATE_EN' | 'SUMMARY' | 'SEO' | 'SMS'
  ) => {
    if (!formData.title_bn.trim() && !formData.content_bn.trim()) {
      setAiPreview('অনুগ্রহ করে প্রথমে শিরোনাম বা বিবরণ লিখুন।');
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
          content_bn: formData.content_bn || formData.title_bn,
          content_en: formData.content_en,
          entity_type: 'NOTICE',
        }),
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      const s = data.suggestions || {};
      if (actionType === 'IMPROVE_BN') {
        const improved = s.improved_wording?.content_bn || formData.content_bn;
        setFormData((prev) => ({ ...prev, content_bn: improved }));
        setAiPreview(`উন্নত বাংলা খসড়া প্রয়োগ করা হয়েছে।`);
      } else if (actionType === 'TRANSLATE_EN') {
        const translatedTitle = s.improved_wording?.title_en || formData.title_en;
        const translatedBody = s.translation?.bn_to_en || '';
        setFormData((prev) => ({
          ...prev,
          title_en: translatedTitle,
          content_en: translatedBody,
        }));
        setAiPreview(`ইংরেজি অনুবাদ প্রস্তুত হয়েছে: ${translatedBody}`);
      } else if (actionType === 'SUMMARY') {
        setAiPreview(`সারাংশ (Summary): ${s.summary?.summary_bn}`);
      } else if (actionType === 'SEO') {
        setAiPreview(
          `SEO Title: ${s.seo_metadata?.meta_title} | Slug: ${s.seo_metadata?.suggested_slug}`
        );
      } else if (actionType === 'SMS') {
        setAiPreview(
          `SMS Notification: ${s.notification_draft?.sms_bn || s.notification_draft?.body_bn}`
        );
      }
    } catch {
      setAiPreview('এআই কনটেন্ট অ্যাসিস্ট্যান্ট এই মুহূর্তে সাড়া দিচ্ছে না।');
    } finally {
      setAiBusy(false);
    }
  };

  const openCreateModal = () => {
    setEditingNotice(null);
    setAiPreview(null);
    setFormData({
      title_bn: '',
      title_en: '',
      content_bn: '',
      content_en: '',
      category: 'GENERAL',
      priority: 'NORMAL',
      is_pinned: false,
      is_published: true,
      attachment_url: '',
    });
    setIsModalOpen(true);
  };

  const openEditModal = (n: Notice) => {
    setEditingNotice(n);
    setAiPreview(null);
    setFormData({
      title_bn: n.title_bn,
      title_en: n.title_en || '',
      content_bn: n.content_bn,
      content_en: n.content_en || '',
      category: n.category,
      priority: n.priority,
      is_pinned: n.is_pinned,
      is_published: n.is_published,
      attachment_url: n.attachment_url || '',
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormBusy(true);
    try {
      if (editingNotice) {
        await api.updateNotice(editingNotice.id, formData);
        setMessage({ text: 'নোটিশ সফলভাবে হালনাগাদ করা হয়েছে।', type: 'success' });
      } else {
        await api.createNotice(formData);
        setMessage({ text: 'নতুন নোটিশ সফলভাবে প্রকাশিত হয়েছে।', type: 'success' });
      }
      setIsModalOpen(false);
      fetchNotices();
    } catch (err: any) {
      setMessage({ text: err.message || 'নোটিশ সংরক্ষণ করা যায়নি।', type: 'error' });
    } finally {
      setFormBusy(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('আপনি কি নিশ্চিত যে এই নোটিশটি মুছে ফেলতে চান?')) return;
    try {
      await api.deleteNotice(id);
      setMessage({ text: 'নোটিশ মুছে ফেলা হয়েছে।', type: 'success' });
      fetchNotices();
    } catch (err: any) {
      setMessage({ text: err.message || 'মুছে ফেলা সম্ভব হয়নি।', type: 'error' });
    }
  };

  return (
    <>
      <AdminHeader
        title="নোটিশ ও জরুরি বিজ্ঞপ্তি নিয়ন্ত্রণ (Notices & Announcements)"
        subtitle="ওয়েবসাইটের নোটিশ বোর্ড, জরুরি মারকুই ব্যানার এবং প্রাতিষ্ঠানিক ঘোষণা ব্যবস্থাপনা"
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
            <Bell size={18} className="text-primary" />
            <span>প্রকাশিত নোটিশের তালিকা ({notices.length}টি)</span>
          </div>

          <button
            onClick={openCreateModal}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <Plus size={14} /> নতুন নোটিশ প্রকাশ করুন
          </button>
        </div>

        {/* Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">শিরোনাম (Title)</th>
                  <th className="p-4">ক্যাটাগরি</th>
                  <th className="p-4">গুরুত্ব (Priority)</th>
                  <th className="p-4">পিন স্ট্যাটাস</th>
                  <th className="p-4">প্রকাশের তারিখ</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      নোটিশ লোড হচ্ছে...
                    </td>
                  </tr>
                ) : notices.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      কোনো নোটিশ পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  notices.map((n) => (
                    <tr key={n.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-bold text-foreground">
                        <div className="flex items-center gap-1.5">
                          {n.is_pinned && <Pin size={12} className="text-amber-500 fill-amber-500 shrink-0" />}
                          <span className="line-clamp-1">{n.title_bn}</span>
                        </div>
                        {n.title_en && <div className="text-[11px] font-normal text-secondary line-clamp-1">{n.title_en}</div>}
                      </td>
                      <td className="p-4 text-secondary">{n.category}</td>
                      <td className="p-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            n.priority === 'URGENT'
                              ? 'bg-rose-500/10 text-rose-600 border border-rose-500/20 animate-pulse'
                              : n.priority === 'HIGH'
                              ? 'bg-amber-500/10 text-amber-600 border border-amber-500/20'
                              : 'bg-surface text-secondary border border-border'
                          }`}
                        >
                          {n.priority}
                        </span>
                      </td>
                      <td className="p-4 text-secondary">
                        {n.is_pinned ? (
                          <span className="text-amber-600 font-semibold flex items-center gap-1 text-[11px]">
                            <Pin size={11} className="fill-amber-500" /> পিন করা
                          </span>
                        ) : (
                          'সাধারণ'
                        )}
                      </td>
                      <td className="p-4 font-mono text-[11px] text-secondary">
                        {n.published_at?.slice(0, 10) || n.created_at?.slice(0, 10)}
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => openEditModal(n)}
                          className="p-1.5 rounded-lg border border-border bg-surface hover:bg-card text-foreground"
                          title="সম্পাদনা করুন"
                        >
                          <Edit size={13} />
                        </button>
                        <button
                          onClick={() => handleDelete(n.id)}
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

      {/* Notice Edit/Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-2xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between bg-surface/50">
              <h3 className="text-sm font-bold text-foreground">
                {editingNotice ? 'নোটিশ সম্পাদনা করুন' : 'নতুন প্রাতিষ্ঠানিক নোটিশ প্রকাশ করুন'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-secondary text-sm">
                ✕
              </button>
            </div>

            <form onSubmit={handleSave} className="p-6 overflow-y-auto space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">শিরোনাম (বাংলা) *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: জরুরি সাবস্টেশন সংস্কার ও নিরাপত্তা সংক্রান্ত বিজ্ঞপ্তি..."
                  value={formData.title_bn}
                  onChange={(e) => setFormData({ ...formData, title_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-secondary">শিরোনাম (ইংরেজি - ঐচ্ছিক)</label>
                <input
                  type="text"
                  placeholder="Title in English..."
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
                    <option value="GENERAL">সাধারণ বিজ্ঞপ্তি (General)</option>
                    <option value="URGENT">জরুরি বিজ্ঞপ্তি (Urgent)</option>
                    <option value="ELECTION">নির্বাচন ও কাউন্সিল (Election)</option>
                    <option value="WELFARE">কল্যাণ তহবিল (Welfare)</option>
                    <option value="MEETING">সভা ও অধিবেশন (Meeting)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-semibold text-foreground">গুরুত্ব স্তর (Priority)</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                    className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary"
                  >
                    <option value="NORMAL">NORMAL (স্বাভাবিক)</option>
                    <option value="HIGH">HIGH (উচ্চ অগ্রাধিকার)</option>
                    <option value="URGENT">URGENT (জরুরি — হেডারে মারকুই ব্যানার সক্রিয় করবে)</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">বিজ্ঞপ্তির পূর্ণ বিবরণ (বাংলা) *</label>
                <textarea
                  required
                  rows={4}
                  placeholder="বিজ্ঞপ্তির বিস্তারিত বিবরণ লিখুন..."
                  value={formData.content_bn}
                  onChange={(e) => setFormData({ ...formData, content_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground text-xs focus:outline-none focus:border-primary leading-relaxed"
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

              <div className="flex items-center gap-6 pt-2">
                <label className="flex items-center gap-2 cursor-pointer font-semibold text-foreground">
                  <input
                    type="checkbox"
                    checked={formData.is_pinned}
                    onChange={(e) => setFormData({ ...formData, is_pinned: e.target.checked })}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span>শীর্ষে পিন করে রাখুন (Pin to top)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer font-semibold text-foreground">
                  <input
                    type="checkbox"
                    checked={formData.is_published}
                    onChange={(e) => setFormData({ ...formData, is_published: e.target.checked })}
                    className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                  />
                  <span>তাত্ক্ষণিক প্রকাশ করুন (Publish immediately)</span>
                </label>
              </div>

              <div className="p-4 border-t border-border flex justify-end gap-2.5 bg-surface/50 -mx-6 -mb-6 mt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
                >
                  বাতিল
                </button>
                <button
                  type="submit"
                  disabled={formBusy}
                  className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
                >
                  {formBusy ? 'সংরক্ষণ হচ্ছে...' : editingNotice ? 'হালনাগাদ সম্পন্ন করুন' : 'নোটিশ প্রকাশ করুন'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
