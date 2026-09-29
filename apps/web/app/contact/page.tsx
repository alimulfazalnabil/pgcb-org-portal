'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useLanguage } from '@/lib/i18n';

export default function ContactPage() {
  const { language, t } = useLanguage();
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    message: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; ticket_no?: string; error?: string } | null>(null);

  useEffect(() => {
    api
      .getSettings()
      .then((res) => setSettings(res || {}))
      .catch(() => setSettings({}));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setResult(null);
    try {
      const res = await api.submitContact({
        name: form.name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        subject: form.subject.trim(),
        message: form.message.trim(),
      });
      setResult({ ok: true, ticket_no: res.ticket_no || `PGCB-TKT-${res.message_id}` });
      setForm({ name: '', email: '', phone: '', subject: '', message: '' });
    } catch (err: any) {
      setResult({
        ok: false,
        error:
          err?.message ||
          t(
            'বার্তা পাঠানো সম্ভব হয়নি। অনুগ্রহ করে তথ্য যাচাই করে পুনরায় চেষ্টা করুন।',
            'Unable to send message. Please verify your details and try again.'
          ),
      });
    } finally {
      setSubmitting(false);
    }
  }

  const addressDisplay =
    language === 'en'
      ? settings.contact_address_en || 'PGCB Bhaban, Avenue-3, Jahurul Islam City, Aftabnagar, Badda, Dhaka-1212'
      : settings.contact_address_bn || 'পিজিসিবি ভবন, এভিনিউ-৩, জহুরুল ইসলাম সিটি, আফতাবনগর, বাড্ডা, ঢাকা-১২১২';
  const contactEmail = settings.contact_email || 'info@pgcb.org.bd';
  const contactPhone = settings.contact_phone || '+880-2-55046731';
  const officeHoursDisplay =
    language === 'en'
      ? settings.office_hours_en || 'Sunday – Thursday, 9:00 AM – 5:00 PM'
      : settings.office_hours_bn || 'রবিবার – বৃহস্পতিবার, সকাল ৯:০০ – বিকাল ৫:০০';

  return (
    <div className="bg-slate-50 min-h-screen py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-6 sm:p-10 text-white shadow-xl mb-10">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
            CENTRAL SECRETARIAT • CONTACT & SUPPORT
          </span>
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
            {t('যোগাযোগ ও দাপ্তরিক সহায়তা কেন্দ্র', 'Contact & Official Support Center')}
          </h1>
          <p className="text-slate-300 text-sm sm:text-base max-w-2xl">
            {t(
              'সদস্যপদ নিবন্ধন, ডিজিটাল আইডি কার্ড যাচাইকরণ, বার্ষিক নবায়ন বা সাংগঠনিক যেকোনো বিষয়ে কেন্দ্রীয় দপ্তরের সাথে যোগাযোগ করুন।',
              'Contact the Central Secretariat regarding membership registration, digital ID card verification, annual renewal, or any organizational inquiry.'
            )}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Office Info */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-sm">
              <h2 className="text-xl font-extrabold text-slate-900 mb-6">
                {t('কেন্দ্রীয় দপ্তর', 'Central Office')}
              </h2>

              <dl className="space-y-5 text-sm">
                <div>
                  <dt className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                    {t('প্রধান কার্যালয়ের ঠিকানা', 'Head Office Address')}
                  </dt>
                  <dd className="font-semibold text-slate-800 leading-relaxed">{addressDisplay}</dd>
                </div>

                <div>
                  <dt className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                    {t('অফিসিয়াল ইমেইল', 'Official Email')}
                  </dt>
                  <dd className="font-mono font-bold text-slate-800">{contactEmail}</dd>
                </div>

                <div>
                  <dt className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                    {t('টেলিফোন ও হেল্পডেস্ক', 'Telephone & Helpdesk')}
                  </dt>
                  <dd className="font-mono font-bold text-slate-800">{contactPhone}</dd>
                </div>

                <div>
                  <dt className="text-xs font-extrabold uppercase tracking-wider text-primary mb-1">
                    {t('দাপ্তরিক সময়সূচি', 'Office Hours')}
                  </dt>
                  <dd className="font-semibold text-slate-700">{officeHoursDisplay}</dd>
                </div>
              </dl>
            </div>

            <div className="bg-emerald-950 text-white rounded-2xl p-6 shadow-sm">
              <h3 className="text-base font-extrabold text-emerald-300 mb-2">
                {t('জরুরি সদস্যপদ সহায়তা', 'Priority Membership Support')}
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {t(
                  'আবেদন ট্র্যাকিং বা ডিজিটাল আইডি কার্ড যাচাইয়ের জন্য আপনার মেম্বারশিপ আইডি (যেমন: ',
                  'For application tracking or digital ID card verification, please mention your Membership ID (e.g., '
                )}
                <code className="text-emerald-300">PGD-2026-0001</code>
                {t(') অথবা এমপ্লয়ি আইডি উল্লেখ করুন।', ') or Employee ID.')}
              </p>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-10 shadow-sm space-y-6"
            >
              <div>
                <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 mb-1">
                  {t('বার্তা বা অনুসন্ধান পাঠান', 'Send a Message or Inquiry')}
                </h2>
                <p className="text-sm text-slate-500">
                  {t(
                    'আপনার বার্তা সরাসরি কেন্দ্রীয় সচিবালয়ের সাপোর্ট টিকেট সিস্টেমে সংরক্ষিত হবে।',
                    'Your message will be logged directly in the Central Secretariat support ticket system.'
                  )}
                </p>
              </div>

              {result?.ok && (
                <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900">
                  <div className="font-extrabold text-base mb-1">
                    {t('আপনার বার্তা সফলভাবে গৃহীত হয়েছে!', 'Your message has been received!')}
                  </div>
                  <p className="text-sm">
                    {t('অনুসন্ধান রেফারেন্স টিকেট নম্বর:', 'Inquiry Reference Ticket Number:')}{' '}
                    <span className="font-mono font-extrabold px-2 py-0.5 rounded bg-white border border-emerald-300">
                      {result.ticket_no}
                    </span>
                  </p>
                </div>
              )}

              {result && !result.ok && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm font-bold">
                  {result.error}
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                    {t('আপনার পূর্ণ নাম *', 'Your Full Name *')}
                  </label>
                  <input
                    type="text"
                    required
                    minLength={2}
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder={t('যেমন: প্রকৌ. মোঃ সাইফুল ইসলাম', 'e.g., Engr. Md. Saiful Islam')}
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                    {t('ইমেইল ঠিকানা *', 'Email Address *')}
                  </label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="name@pgcb.org.bd"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                    {t('মোবাইল নম্বর (ঐচ্ছিক)', 'Mobile Number (Optional)')}
                  </label>
                  <input
                    type="tel"
                    value={form.phone}
                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    placeholder="017XXXXXXXX"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
                  />
                </div>

                <div>
                  <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                    {t('বিষয় *', 'Subject *')}
                  </label>
                  <input
                    type="text"
                    required
                    minLength={3}
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    placeholder={t('সদস্যপদ / ডিজিটাল আইডি / সাধারণ জিজ্ঞাসা', 'Membership / Digital ID / General Inquiry')}
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-extrabold uppercase tracking-wider text-slate-700 mb-2">
                  {t('বিস্তারিত বার্তা *', 'Detailed Message *')}
                </label>
                <textarea
                  rows={5}
                  required
                  minLength={10}
                  value={form.message}
                  onChange={(e) => setForm({ ...form, message: e.target.value })}
                  placeholder={t(
                    'আপনার জিজ্ঞাসা বা মতামত বিস্তারিত লিখুন (কমপক্ষে ১০ অক্ষর)...',
                    'Write your inquiry or feedback in detail (minimum 10 characters)...'
                  )}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-primary outline-none text-sm font-medium"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-primary hover:bg-emerald-800 disabled:opacity-60 text-white text-sm font-extrabold shadow-md transition-all"
              >
                {submitting ? t('বার্তা পাঠানো হচ্ছে...', 'Sending message...') : t('বার্তা জমা দিন', 'Submit Message')}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
