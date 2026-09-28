'use client';

import { useEffect, useState, FormEvent } from 'react';
import Link from 'next/link';
import { api, NewsItem } from '@/lib/api';
import {
  Newspaper,
  Plus,
  Send,
  CheckCircle2,
  Globe,
  Archive,
  Trash2,
  ArrowLeft,
  Star,
} from 'lucide-react';

export default function AdminNewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const [form, setForm] = useState({
    title_bn: '',
    title_en: '',
    summary_bn: '',
    body_bn: '',
    category: 'ORGANIZATIONAL',
    tags: '',
    is_featured: false,
  });

  async function loadNews() {
    setLoading(true);
    try {
      const data = await api.adminListNews(statusFilter ? { status: statusFilter } : undefined);
      setItems(data);
    } catch (err) {
      console.error('Failed to load admin news', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadNews();
  }, [statusFilter]);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    try {
      await api.adminCreateNews({
        title_bn: form.title_bn,
        title_en: form.title_en || form.title_bn,
        summary_bn: form.summary_bn,
        body_bn: form.body_bn,
        category: form.category,
        tags: form.tags
          ? form.tags
              .split(',')
              .map((t) => t.trim())
              .filter(Boolean)
          : [],
        is_featured: form.is_featured,
        workflow_status: 'DRAFT',
      });
      setForm({
        title_bn: '',
        title_en: '',
        summary_bn: '',
        body_bn: '',
        category: 'ORGANIZATIONAL',
        tags: '',
        is_featured: false,
      });
      setMessage('সংবাদ খসড়া (DRAFT) সফলভাবে তৈরি হয়েছে।');
      loadNews();
    } catch (err: any) {
      setMessage(err.message || 'সংবাদ তৈরি ব্যর্থ হয়েছে।');
    }
  }

  async function handleTransition(newsId: number, status: string) {
    try {
      await api.adminTransitionWorkflow('news', newsId, status, `Transitioned to ${status}`);
      setMessage(`সংবাদের অবস্থা ${status}-এ পরিবর্তিত হয়েছে।`);
      loadNews();
    } catch (err: any) {
      setMessage(err.message || 'ওয়ার্কফ্লো পরিবর্তন ব্যর্থ হয়েছে।');
    }
  }

  async function handleDelete(newsId: number) {
    try {
      await api.adminDeleteNews(newsId);
      setMessage('সংবাদটি মুছে ফেলা হয়েছে।');
      loadNews();
    } catch (err: any) {
      setMessage(err.message || 'মুছে ফেলা যায়নি।');
    }
  }

  return (
    <section className="section py-10 min-h-screen bg-background">
      <div className="container max-w-6xl mx-auto px-4 space-y-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-5 border-b border-border">
          <div>
            <Link
              href="/admin"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary mb-2"
            >
              <ArrowLeft size={14} /> অ্যাডমিন ড্যাশবোর্ডে ফিরুন
            </Link>
            <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
              <Newspaper size={24} className="text-primary" /> সংবাদ ও প্রেস বিজ্ঞপ্তি ব্যবস্থাপনা (CMS)
            </h1>
            <p className="text-xs text-secondary mt-1">
              Draft → Review → Approved → Published → Archived মাল্টি-রোল প্রকাশনা ওয়ার্কফ্লো
            </p>
          </div>
        </div>

        {message && (
          <div className="p-3.5 rounded-xl bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Create Form */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm h-fit">
            <h2 className="text-base font-bold text-foreground mb-4 flex items-center gap-2">
              <Plus size={18} className="text-primary" /> নতুন সংবাদ তৈরি করুন
            </h2>
            <form onSubmit={handleCreate} className="space-y-3.5 text-xs">
              <div>
                <label className="block font-semibold text-foreground mb-1">শিরোনাম (বাংলা) *</label>
                <input
                  type="text"
                  required
                  value={form.title_bn}
                  onChange={(e) => setForm({ ...form, title_bn: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                />
              </div>
              <div>
                <label className="block font-semibold text-foreground mb-1">Title (English)</label>
                <input
                  type="text"
                  value={form.title_en}
                  onChange={(e) => setForm({ ...form, title_en: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                />
              </div>
              <div>
                <label className="block font-semibold text-foreground mb-1">ক্যাটাগরি</label>
                <select
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                >
                  <option value="ORGANIZATIONAL">সাংগঠনিক (ORGANIZATIONAL)</option>
                  <option value="PRESS_RELEASE">প্রেস বিজ্ঞপ্তি (PRESS_RELEASE)</option>
                  <option value="WELFARE">সদস্য কল্যাণ (WELFARE)</option>
                  <option value="GRID_OPERATIONS">গ্রিড কার্যক্রম (GRID_OPERATIONS)</option>
                  <option value="EVENT">ইভেন্ট (EVENT)</option>
                </select>
              </div>
              <div>
                <label className="block font-semibold text-foreground mb-1">সংক্ষিপ্ত সারসংক্ষেপ</label>
                <textarea
                  rows={2}
                  value={form.summary_bn}
                  onChange={(e) => setForm({ ...form, summary_bn: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                />
              </div>
              <div>
                <label className="block font-semibold text-foreground mb-1">বিস্তারিত বিবরণ (বাংলা) *</label>
                <textarea
                  rows={4}
                  required
                  value={form.body_bn}
                  onChange={(e) => setForm({ ...form, body_bn: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                />
              </div>
              <div>
                <label className="block font-semibold text-foreground mb-1">ট্যাগসমূহ (কমা দ্বারা পৃথক)</label>
                <input
                  type="text"
                  placeholder="PGCB, AGM, Grid"
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-background"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.is_featured}
                  onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
                />
                <span className="font-semibold text-foreground">প্রধান সংবাদ (Featured News)</span>
              </label>
              <button
                type="submit"
                className="w-full py-2.5 px-4 rounded-xl bg-primary text-white font-bold hover:opacity-90 transition-all"
              >
                খসড়া হিসেবে সংরক্ষণ করুন
              </button>
            </form>
          </div>

          {/* News List & Workflow Controls */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex flex-wrap gap-2">
              {['', 'DRAFT', 'REVIEW', 'APPROVED', 'PUBLISHED', 'ARCHIVED'].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setStatusFilter(st)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    statusFilter === st
                      ? 'bg-primary text-white'
                      : 'bg-card border border-border text-secondary'
                  }`}
                >
                  {st || 'সকল স্ট্যাটাস'}
                </button>
              ))}
            </div>

            {loading ? (
              <p className="text-xs text-secondary py-8 text-center">লোড হচ্ছে...</p>
            ) : items.length === 0 ? (
              <div className="bg-card border border-border rounded-2xl p-8 text-center text-xs text-secondary">
                কোনো সংবাদ আইটেম পাওয়া যায়নি।
              </div>
            ) : (
              <div className="space-y-3">
                {items.map((item) => (
                  <div
                    key={item.id}
                    className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-3"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">
                            {item.workflow_status}
                          </span>
                          <span className="text-[11px] text-secondary">{item.category}</span>
                          {item.is_featured && (
                            <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-amber-600">
                              <Star size={11} /> Featured
                            </span>
                          )}
                        </div>
                        <h3 className="text-sm font-bold text-foreground">{item.title_bn}</h3>
                        <p className="text-[11px] text-secondary font-mono">/{item.slug}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDelete(item.id)}
                        className="p-1.5 rounded-lg text-rose-600 hover:bg-rose-500/10"
                        title="মুছে ফেলুন"
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-border text-xs">
                      <button
                        type="button"
                        onClick={() => handleTransition(item.id, 'REVIEW')}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-700 font-semibold"
                      >
                        <Send size={12} /> Review
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTransition(item.id, 'APPROVED')}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-500/10 text-blue-700 font-semibold"
                      >
                        <CheckCircle2 size={12} /> Approve
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTransition(item.id, 'PUBLISHED')}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-700 font-semibold"
                      >
                        <Globe size={12} /> Publish
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTransition(item.id, 'ARCHIVED')}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-surface border border-border text-secondary font-semibold"
                      >
                        <Archive size={12} /> Archive
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
