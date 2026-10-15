'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Bell,
  Mail,
  MessageSquare,
  Shield,
  Save,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  RefreshCw,
  Lock,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { NotificationCategoryInfo, NotificationSettingsResponse } from '@/lib/api/types';

export default function MemberNotificationSettingsPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [categories, setCategories] = useState<NotificationCategoryInfo[]>([]);
  const [preferences, setPreferences] = useState<Record<string, { in_app: boolean; email: boolean; sms: boolean }>>({});

  const isEn = lang === 'en';

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await membersApi.getNotificationSettings();
      setCategories(res.categories || []);
      setPreferences(res.preferences || {});
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load notification settings.'
            : 'নোটিফিকেশন সেটিংস লোড করা সম্ভব হয়নি।')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleToggle = (category: string, channel: 'in_app' | 'email' | 'sms') => {
    // Prevent disabling critical system security in-app notifications
    if (category === 'SYSTEM' && channel === 'in_app') return;

    setPreferences((prev) => {
      const current = prev[category] || { in_app: true, email: true, sms: false };
      return {
        ...prev,
        [category]: {
          ...current,
          [channel]: !current[channel],
        },
      };
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMsg(null);
      await membersApi.updateNotificationSettings(preferences);
      setSuccessMsg(
        isEn
          ? 'Notification preferences saved successfully!'
          : 'নোটিফিকেশন সেটিংস সফলভাবে সংরক্ষিত হয়েছে!'
      );
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn ? 'Failed to save settings. Please try again.' : 'সেটিংস সংরক্ষণ ব্যর্থ হয়েছে।')
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <MemberLayout
      title={isEn ? 'Notification Settings' : 'নোটিফিকেশন সেটিংস'}
      lang={lang}
      onLangChange={setLang}
      activeTab="notifications"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <Link
            href="/member/notifications"
            className="inline-flex items-center gap-1.5 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Notifications' : 'বিজ্ঞপ্তিতে ফিরুন'}</span>
          </Link>
        </div>

        {/* Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-2">
          <h1 className="text-2xl font-bold text-slate-900">
            {isEn ? 'Notification Preferences Matrix' : 'নোটিফিকেশন চ্যানেল ও অগ্রাধিকার সেটিংস'}
          </h1>
          <p className="text-slate-500 text-sm max-w-2xl leading-relaxed">
            {isEn
              ? 'Choose how and where you want to receive alerts for membership renewal, event confirmations, receipts, and institutional announcements.'
              : 'সদস্যপদ নবায়ন, ইভেন্ট উপস্থিতি, পেমেন্ট রসিদ ও জরুরি সার্কুলারের জন্য পছন্দের নোটিফিকেশন চ্যানেল নির্বাচন করুন।'}
          </p>
        </div>

        {/* Feedback Alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2 text-sm">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Loading Spinner */}
        {loading && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
            <div className="w-10 h-10 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-medium text-slate-500">
              {isEn ? 'Loading preferences...' : 'সেটিংস লোড হচ্ছে...'}
            </p>
          </div>
        )}

        {/* Preference Matrix Form */}
        {!loading && (
          <form onSubmit={handleSave} className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-600 uppercase tracking-wider">
                      <th className="py-4 px-6">{isEn ? 'Notification Category' : 'বিজ্ঞপ্তির বিভাগ'}</th>
                      <th className="py-4 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <Bell className="w-4 h-4 text-blue-600" />
                          <span>{isEn ? 'In-App' : 'ইন-অ্যাপ'}</span>
                        </div>
                      </th>
                      <th className="py-4 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <Mail className="w-4 h-4 text-indigo-600" />
                          <span>{isEn ? 'Email' : 'ইমেইল'}</span>
                        </div>
                      </th>
                      <th className="py-4 px-4 text-center">
                        <div className="flex items-center justify-center gap-1.5">
                          <MessageSquare className="w-4 h-4 text-emerald-600" />
                          <span>{isEn ? 'SMS' : 'এসএমএস'}</span>
                        </div>
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-100 text-sm">
                    {categories.map((cat) => {
                      const pref = preferences[cat.id] || { in_app: true, email: true, sms: false };
                      const isSystemLocked = cat.id === 'SYSTEM';

                      return (
                        <tr key={cat.id} className="hover:bg-slate-50/60 transition-colors">
                          <td className="py-4 px-6">
                            <div className="font-bold text-slate-900">{cat.title_bn}</div>
                            <div className="text-xs text-slate-500 mt-0.5">{cat.description_bn}</div>
                          </td>

                          {/* In-App Toggle */}
                          <td className="py-4 px-4 text-center">
                            <label className="inline-flex items-center justify-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={pref.in_app}
                                disabled={isSystemLocked}
                                onChange={() => handleToggle(cat.id, 'in_app')}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900 relative disabled:opacity-60" />
                            </label>
                            {isSystemLocked && (
                              <div className="text-[10px] text-slate-400 mt-1 flex items-center justify-center gap-1">
                                <Lock className="w-2.5 h-2.5" />
                                <span>{isEn ? 'Required' : 'বাধ্যতামূলক'}</span>
                              </div>
                            )}
                          </td>

                          {/* Email Toggle */}
                          <td className="py-4 px-4 text-center">
                            <label className="inline-flex items-center justify-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={pref.email}
                                onChange={() => handleToggle(cat.id, 'email')}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900 relative" />
                            </label>
                          </td>

                          {/* SMS Toggle */}
                          <td className="py-4 px-4 text-center">
                            <label className="inline-flex items-center justify-center cursor-pointer">
                              <input
                                type="checkbox"
                                checked={pref.sms}
                                onChange={() => handleToggle(cat.id, 'sms')}
                                className="sr-only peer"
                              />
                              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-slate-900 relative" />
                            </label>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex items-center justify-end gap-3">
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-bold shadow-md transition-all disabled:opacity-50"
              >
                {saving ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                <span>{saving ? (isEn ? 'Saving...' : 'সংরক্ষণ হচ্ছে...') : (isEn ? 'Save Preferences' : 'সেটিংস সংরক্ষণ করুন')}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </MemberLayout>
  );
}
