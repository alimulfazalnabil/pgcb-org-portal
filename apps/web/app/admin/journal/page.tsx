'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { BookOpen, Plus, Trash2, ExternalLink } from 'lucide-react';

export default function AdminJournalPage() {
  const [journals, setJournals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    slug: '',
    title_bn: '',
    title_en: '',
    abstract_bn: '',
    authors_bn: '',
    volume: 'Vol-2026',
    issue: 'Issue-1',
    pdf_url: '',
    is_published: true,
  });

  const fetchJournals = async () => {
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/admin/journals');
      const data = res.ok ? await res.json() : [];
      setJournals(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJournals();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const slug =
        form.slug.trim() ||
        `journal-${Date.now()}`;
      const res = await fetch('/backend/api/v1/admin/journals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, slug }),
      });
      if (res.ok) {
        setShowModal(false);
        setForm({
          slug: '',
          title_bn: '',
          title_en: '',
          abstract_bn: '',
          authors_bn: '',
          volume: 'Vol-2026',
          issue: 'Issue-1',
          pdf_url: '',
          is_published: true,
        });
        fetchJournals();
      }
    } finally {
      setBusy(false);
    }
  };

  const handleArchive = async (id: number) => {
    await fetch(`/backend/api/v1/admin/journals/${id}`, { method: 'DELETE' });
    fetchJournals();
  };

  return (
    <>
      <AdminHeader
        title="কারিগরি জার্নাল ও গবেষণা প্রকাশনা (Journal Desk)"
        subtitle="পাওয়ার গ্রিড প্রকৌশল জার্নাল, গবেষণাপত্র ও কারিগরি প্রবন্ধ প্রকাশনা ব্যবস্থাপনা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        <div className="bg-card border border-border rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <BookOpen size={18} className="text-primary" />
            <span>প্রকাশিত ও খসড়া জার্নাল তালিকা ({journals.length}টি)</span>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center gap-1.5"
          >
            <Plus size={14} /> নতুন জার্নাল প্রবন্ধ যোগ করুন
          </button>
        </div>

        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px]">
              <tr>
                <th className="p-4">শিরোনাম (Title)</th>
                <th className="p-4">লেখক / গবেষক</th>
                <th className="p-4">ভলিউম ও সংখ্যা</th>
                <th className="p-4">স্ট্যাটাস</th>
                <th className="p-4 text-right">পদক্ষেপ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-secondary">
                    জার্নাল তালিকা লোড হচ্ছে...
                  </td>
                </tr>
              ) : journals.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-secondary">
                    কোনো জার্নাল প্রবন্ধ পাওয়া যায়নি।
                  </td>
                </tr>
              ) : (
                journals.map((j) => (
                  <tr key={j.id} className="hover:bg-surface/40">
                    <td className="p-4">
                      <div className="font-bold text-foreground">{j.title_bn}</div>
                      {j.title_en && <div className="text-[11px] text-secondary">{j.title_en}</div>}
                    </td>
                    <td className="p-4 text-secondary">{j.authors_bn || 'কেন্দ্রীয় কারিগরি প্যানেল'}</td>
                    <td className="p-4 font-mono text-[11px] text-secondary">
                      {j.volume || 'Vol-1'} / {j.issue || 'Issue-1'}
                    </td>
                    <td className="p-4">
                      <StatusBadge status={j.is_published ? 'PUBLISHED' : 'DRAFT'} />
                    </td>
                    <td className="p-4 text-right space-x-2">
                      {j.pdf_url && (
                        <a
                          href={j.pdf_url}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded-lg border border-border text-primary font-semibold text-[11px] inline-flex items-center gap-1"
                        >
                          <ExternalLink size={12} /> PDF
                        </a>
                      )}
                      {j.is_published && (
                        <button
                          onClick={() => handleArchive(j.id)}
                          className="px-2.5 py-1 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 font-semibold text-[11px] inline-flex items-center gap-1"
                        >
                          <Trash2 size={12} /> আর্কাইভ
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <form
            onSubmit={handleCreate}
            className="bg-card border border-border w-full max-w-lg rounded-2xl shadow-2xl p-6 space-y-4"
          >
            <h3 className="text-sm font-bold text-foreground">নতুন জার্নাল প্রবন্ধ প্রকাশ করুন</h3>
            <div className="space-y-3">
              <input
                type="text"
                required
                placeholder="প্রবন্ধের শিরোনাম (বাংলায়) *"
                value={form.title_bn}
                onChange={(e) => setForm({ ...form, title_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="প্রবন্ধের শিরোনাম (ইংরেজিতে)"
                value={form.title_en}
                onChange={(e) => setForm({ ...form, title_en: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="লেখকবৃন্দ (Authors)"
                value={form.authors_bn}
                onChange={(e) => setForm({ ...form, authors_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="ভলিউম (যেমন: Vol-2026)"
                  value={form.volume}
                  onChange={(e) => setForm({ ...form, volume: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
                />
                <input
                  type="text"
                  placeholder="ইস্যু (যেমন: Issue-1)"
                  value={form.issue}
                  onChange={(e) => setForm({ ...form, issue: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
                />
              </div>
              <textarea
                rows={3}
                required
                placeholder="সারসংক্ষেপ (Abstract) *"
                value={form.abstract_bn}
                onChange={(e) => setForm({ ...form, abstract_bn: e.target.value })}
                className="w-full p-3 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="PDF ডকুমেন্ট লিংক (ঐচ্ছিক)"
                value={form.pdf_url}
                onChange={(e) => setForm({ ...form, pdf_url: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 rounded-xl border border-border text-xs font-semibold"
              >
                বাতিল
              </button>
              <button
                type="submit"
                disabled={busy}
                className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold"
              >
                {busy ? 'সংরক্ষণ হচ্ছে...' : 'প্রকাশ করুন'}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
