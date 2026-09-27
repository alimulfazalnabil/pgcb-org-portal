'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import { Settings, Save, CheckCircle, Shield, Globe, Phone, Mail, Building } from 'lucide-react';

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    async function loadSettings() {
      try {
        const data = await api.getSettings();
        setSettings(data || {});
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch('/backend/api/v1/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings }),
      });
      if (!res.ok) throw new Error('সেটিংস সংরক্ষণ ব্যর্থ হয়েছে।');
      setMessage({ text: 'প্রাতিষ্ঠানিক সেটিংস সফলভাবে সংরক্ষণ করা হয়েছে।', type: 'success' });
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const updateKey = (key: string, val: string) => {
    setSettings((prev) => ({ ...prev, [key]: val }));
  };

  return (
    <>
      <AdminHeader
        title="সিস্টেম ও প্রাতিষ্ঠানিক সেটিংস (Organization Settings)"
        subtitle="পোর্টালের ব্র্যান্ডিং, যোগাযোগের তথ্য, হেল্পলাইন ও নোটিফিকেশন কনফিগারেশন"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-4xl">
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

        <form onSubmit={handleSave} className="space-y-6 text-xs">
          {/* General Branding */}
          <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
            <div className="flex items-center gap-2.5 pb-3 border-b border-border text-foreground font-bold">
              <Building size={16} className="text-primary" />
              <span>সাধারণ পরিচিতি ও ব্র্যান্ডিং (Branding)</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">সংগঠনের পূর্ণ নাম (বাংলা)</label>
                <input
                  type="text"
                  value={settings['site_title_bn'] || 'পাওয়ার গ্রিড কোম্পানী অব বাংলাদেশ লিঃ ডিপ্লোমা-প্রকৌশল সমিতি'}
                  onChange={(e) => updateKey('site_title_bn', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary text-xs"
                />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-secondary">Organization Name (English)</label>
                <input
                  type="text"
                  value={settings['site_title_en'] || 'PGCB Diploma Engineers Association'}
                  onChange={(e) => updateKey('site_title_en', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary text-xs"
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-4">
            <div className="flex items-center gap-2.5 pb-3 border-b border-border text-foreground font-bold">
              <Phone size={16} className="text-primary" />
              <span>যোগাযোগ ও সচিবালয় তথ্য (Contact Info)</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="font-semibold text-foreground">সচিবালয় ইমেইল</label>
                <input
                  type="email"
                  value={settings['contact_email'] || 'secretariat@pgcb.org.bd'}
                  onChange={(e) => updateKey('contact_email', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary text-xs font-mono"
                />
              </div>
              <div className="space-y-1">
                <label className="font-semibold text-foreground">হেল্পলাইন / ফোন</label>
                <input
                  type="text"
                  value={settings['contact_phone'] || '+880 2-55040333'}
                  onChange={(e) => updateKey('contact_phone', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary text-xs font-mono"
                />
              </div>
              <div className="sm:col-span-2 space-y-1">
                <label className="font-semibold text-foreground">সচিবালয় কার্যালয়ের ঠিকানা</label>
                <input
                  type="text"
                  value={settings['office_address'] || 'পিজিসিআইবি ভবন, আফতাবনগর, ঢাকা-১২১২'}
                  onChange={(e) => updateKey('office_address', e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary text-xs"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm flex items-center gap-1.5"
            >
              <Save size={14} /> {saving ? 'সংরক্ষণ হচ্ছে...' : 'সেটিংস সংরক্ষণ করুন'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
