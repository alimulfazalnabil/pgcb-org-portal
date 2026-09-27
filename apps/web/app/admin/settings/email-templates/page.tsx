'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { Mail, Save, CheckCircle2 } from 'lucide-react';

interface EmailTemplateItem {
  key: string;
  name_bn: string;
  name_en: string;
  subject_bn: string;
  subject_en: string;
  body_bn: string;
  body_en: string;
  placeholders: string[];
  updated_at?: string | null;
}

export default function AdminEmailTemplatesPage() {
  const [templates, setTemplates] = useState<EmailTemplateItem[]>([]);
  const [selectedKey, setSelectedKey] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/backend/api/v1/admin/email-templates');
        if (res.ok) {
          const data = await res.json();
          const items: EmailTemplateItem[] = data.items || [];
          setTemplates(items);
          if (items.length > 0) setSelectedKey(items[0].key);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const current = templates.find((t) => t.key === selectedKey) || null;

  const updateCurrent = (field: keyof EmailTemplateItem, val: string) => {
    setTemplates((prev) =>
      prev.map((item) => (item.key === selectedKey ? { ...item, [field]: val } : item))
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!current) return;
    setSaving(true);
    setStatusMsg(null);
    try {
      const res = await fetch(`/backend/api/v1/admin/email-templates/${current.key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject_bn: current.subject_bn,
          subject_en: current.subject_en,
          body_bn: current.body_bn,
          body_en: current.body_en,
        }),
      });
      if (!res.ok) throw new Error('টেমপ্লেট সংরক্ষণ ব্যর্থ হয়েছে।');
      setStatusMsg('ইমেইল টেমপ্লেট সফলভাবে সংরক্ষিত হয়েছে।');
    } catch (err: any) {
      setStatusMsg(err.message || 'সংরক্ষণ ব্যর্থ হয়েছে।');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="প্রাতিষ্ঠানিক ইমেইল টেমপ্লেট (Institutional Email Templates)"
        subtitle="সদস্যপদ, পেমেন্ট রসিদ, ইভেন্ট পাস, সনদপত্র ও নিরাপত্তা নোটিফিকেশনের ১২টি অফিশিয়াল টেমপ্লেট"
      />
      <div className="p-6 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-6xl">
        <div className="bg-card border border-border rounded-2xl p-4 space-y-2">
          <div className="text-xs font-bold text-foreground pb-2 border-b border-border flex items-center gap-2">
            <Mail size={15} className="text-primary" />
            <span>টেমপ্লেট তালিকা ({templates.length})</span>
          </div>
          {loading ? (
            <div className="text-xs text-secondary py-6 text-center">লোড হচ্ছে...</div>
          ) : (
            <div className="space-y-1">
              {templates.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => {
                    setSelectedKey(t.key);
                    setStatusMsg(null);
                  }}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition ${
                    t.key === selectedKey
                      ? 'bg-primary text-white font-bold'
                      : 'hover:bg-surface text-foreground'
                  }`}
                >
                  <div>{t.name_bn}</div>
                  <div className="text-[10px] opacity-75">{t.name_en}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-6">
          {current ? (
            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div>
                  <h2 className="text-sm font-bold text-foreground">{current.name_bn}</h2>
                  <p className="text-[11px] text-secondary">{current.name_en} (`{current.key}`)</p>
                </div>
                <div className="flex flex-wrap gap-1">
                  {current.placeholders.map((ph) => (
                    <span
                      key={ph}
                      className="px-2 py-0.5 rounded bg-surface border border-border font-mono text-[10px] text-secondary"
                    >
                      {`{{${ph}}}`}
                    </span>
                  ))}
                </div>
              </div>

              {statusMsg && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 flex items-center gap-2 font-semibold">
                  <CheckCircle2 size={15} />
                  <span>{statusMsg}</span>
                </div>
              )}

              <div className="space-y-1">
                <label className="font-semibold text-foreground">বিষয় (বাংলা Subject)</label>
                <input
                  type="text"
                  value={current.subject_bn}
                  onChange={(e) => updateCurrent('subject_bn', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">Subject (English)</label>
                <input
                  type="text"
                  value={current.subject_en}
                  onChange={(e) => updateCurrent('subject_en', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">বার্তা (বাংলা Body)</label>
                <textarea
                  rows={5}
                  value={current.body_bn}
                  onChange={(e) => updateCurrent('body_bn', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground leading-relaxed"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-foreground">Message Body (English)</label>
                <textarea
                  rows={5}
                  value={current.body_en}
                  onChange={(e) => updateCurrent('body_en', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground leading-relaxed"
                />
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2.5 rounded-xl bg-primary text-white font-bold flex items-center gap-1.5 hover:opacity-90 disabled:opacity-50"
                >
                  <Save size={14} />
                  <span>{saving ? 'সংরক্ষণ হচ্ছে...' : 'টেমপ্লেট সংরক্ষণ করুন'}</span>
                </button>
              </div>
            </form>
          ) : (
            <div className="text-xs text-secondary py-12 text-center">একটি টেমপ্লেট নির্বাচন করুন</div>
          )}
        </div>
      </div>
    </>
  );
}
