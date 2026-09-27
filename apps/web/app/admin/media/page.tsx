'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { Image as ImageIcon, Plus, Trash2, Upload, ExternalLink } from 'lucide-react';

export default function AdminMediaPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    title_bn: '',
    title_en: '',
    category_bn: 'সম্মেলন ও অনুষ্ঠান',
    asset_type: 'IMAGE',
    url: '',
    thumbnail_url: '',
    published: true,
  });

  const loadMedia = async () => {
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/admin/media');
      const data = res.ok ? await res.json() : [];
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedia();
  }, []);

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch('/backend/api/v1/admin/uploads/public', {
        method: 'POST',
        body: fd,
      });
      if (res.ok) {
        const data = await res.json();
        setForm((prev) => ({
          ...prev,
          url: data.url,
          thumbnail_url: data.url,
        }));
      }
    } finally {
      setBusy(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title_bn.trim() || !form.url.trim()) return;
    setBusy(true);
    try {
      const res = await fetch('/backend/api/v1/admin/media', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setShowModal(false);
        setForm({
          title_bn: '',
          title_en: '',
          category_bn: 'সম্মেলন ও অনুষ্ঠান',
          asset_type: 'IMAGE',
          url: '',
          thumbnail_url: '',
          published: true,
        });
        loadMedia();
      }
    } finally {
      setBusy(false);
    }
  };

  const handleArchive = async (id: number) => {
    await fetch(`/backend/api/v1/admin/media/${id}`, { method: 'DELETE' });
    loadMedia();
  };

  return (
    <>
      <AdminHeader
        title="মিডিয়া ও ফটো গ্যালারি ব্যবস্থাপনা (Media & Gallery)"
        subtitle="সমিতির সম্মেলন, কারিগরি পরিদর্শন ও অনুষ্ঠানের ছবি এবং ভিডিও আর্কাইভ"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        <div className="bg-card border border-border rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <ImageIcon size={18} className="text-primary" />
            <span>মিডিয়া ও গ্যালারি আইটেম ({items.length}টি)</span>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center gap-1.5"
          >
            <Plus size={14} /> নতুন ছবি / মিডিয়া যোগ করুন
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-secondary bg-card border border-border rounded-2xl">
            মিডিয়া গ্যালারি লোড হচ্ছে...
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center text-xs text-secondary bg-card border border-border rounded-2xl">
            কোনো মিডিয়া ফাইল পাওয়া যায়নি।
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {items.map((item) => (
              <div
                key={item.id}
                className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm flex flex-col justify-between"
              >
                <div className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-primary/10 text-primary">
                      {item.category_bn || item.asset_type}
                    </span>
                    <StatusBadge status={item.published ? 'PUBLISHED' : 'DRAFT'} />
                  </div>
                  <h3 className="font-bold text-sm text-foreground">{item.title_bn}</h3>
                  {item.title_en && <p className="text-xs text-secondary">{item.title_en}</p>}
                  <p className="text-[11px] font-mono text-secondary truncate">{item.url}</p>
                </div>

                <div className="px-4 py-3 bg-surface/50 border-t border-border flex items-center justify-between text-xs">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary font-bold inline-flex items-center gap-1 hover:underline"
                  >
                    <ExternalLink size={12} /> ফাইল দেখুন
                  </a>
                  {item.published && (
                    <button
                      onClick={() => handleArchive(item.id)}
                      className="text-rose-600 font-semibold inline-flex items-center gap-1 hover:underline"
                    >
                      <Trash2 size={12} /> আর্কাইভ
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <form
            onSubmit={handleCreate}
            className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4"
          >
            <h3 className="text-sm font-bold text-foreground">নতুন মিডিয়া / গ্যালারি আইটেম যোগ করুন</h3>
            <div className="space-y-3">
              <input
                type="text"
                required
                placeholder="শিরোনাম (বাংলায়) *"
                value={form.title_bn}
                onChange={(e) => setForm({ ...form, title_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="ক্যাটাগরি (যেমন: বার্ষিক সম্মেলন)"
                value={form.category_bn}
                onChange={(e) => setForm({ ...form, category_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <div className="p-3 rounded-xl border border-dashed border-border bg-surface space-y-2">
                <label className="block text-[11px] font-bold text-secondary">
                  ফাইল আপলোড করুন (JPG, PNG, WEBP, PDF, MP4)
                </label>
                <input
                  type="file"
                  onChange={handleUploadFile}
                  className="text-xs text-secondary w-full"
                />
              </div>
              <input
                type="text"
                required
                placeholder="অথবা সরাসরি মিডিয়া URL দিন *"
                value={form.url}
                onChange={(e) => setForm({ ...form, url: e.target.value, thumbnail_url: e.target.value })}
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
                {busy ? 'আপলোড হচ্ছে...' : 'সংরক্ষণ করুন'}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
