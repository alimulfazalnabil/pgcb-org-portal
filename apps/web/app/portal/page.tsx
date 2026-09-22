'use client';

import { useEffect, useState, FormEvent, ChangeEvent } from 'react';
import Link from 'next/link';
import { api, ApiError, CircleItem } from '@/lib/api';
import {
  User,
  Shield,
  CreditCard,
  Bell,
  FileText,
  Upload,
  Calendar,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  ExternalLink,
  Download,
  Building,
  Briefcase,
  IdCard,
} from 'lucide-react';

export default function MemberPortal() {
  const [me, setMe] = useState<any>(null);
  const [profile, setProfile] = useState<any>(null);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [application, setApplication] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  function notify(text: string, type: 'success' | 'error' = 'success') {
    setStatusMessage({ text, type });
    window.setTimeout(() => setStatusMessage(null), 4000);
  }

  async function loadData() {
    try {
      const meData = await api.getMe();
      setMe(meData);

      const [p, a, d, n, c, regRes, pay] = await Promise.allSettled([
        api.getProfile(),
        api.getMemberApplication(),
        api.getMemberDocuments(),
        api.getMemberNotifications(),
        api.getCircles(),
        api.getMyEventRegistrations(),
        api.getMemberPayments(),
      ]);

      if (p.status === 'fulfilled') setProfile(p.value);
      if (a.status === 'fulfilled') setApplication(a.value);
      if (d.status === 'fulfilled') setDocs(d.value);
      if (n.status === 'fulfilled') setNotes(n.value);
      if (c.status === 'fulfilled') setCircles(c.value);
      if (regRes.status === 'fulfilled') setRegistrations(regRes.value);
      if (pay.status === 'fulfilled') setPayments(pay.value);
    } catch (err: any) {
      console.error('Portal load failed', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    if (!profile) return;
    setSaving(true);
    try {
      await api.updateProfile(profile);
      notify('প্রোফাইল তথ্য সফলভাবে সংরক্ষণ করা হয়েছে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'প্রোফাইল সংরক্ষণ ব্যর্থ হয়েছে।', 'error');
    } finally {
      setSaving(false);
    }
  }

  async function submitApplication() {
    try {
      const res = await api.submitMemberApplication();
      setApplication(res);
      notify('আপনার সদস্য আবেদন সফলভাবে জমা দেওয়া হয়েছে। সচিবালয় পর্যালোচনার পর অবহিত করা হবে।', 'success');
    } catch (err: any) {
      notify(err.message || 'আবেদন জমা দেওয়া যায়নি।', 'error');
    }
  }

  async function uploadDoc(e: ChangeEvent<HTMLInputElement>, type: string) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const newDoc = await api.uploadMemberDocument(type, file);
      setDocs((prev) => [newDoc, ...prev]);
      notify(`${type} নথি সফলভাবে আপলোড হয়েছে।`, 'success');
    } catch (err: any) {
      notify(err.message || 'আপলোড ব্যর্থ হয়েছে। সঠিক ফরম্যাট ও সাইজ যাচাই করুন।', 'error');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  }

  if (loading) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-4xl mx-auto px-4 text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent mb-4"></div>
          <p className="text-secondary font-medium">সদস্য তথ্য লোড হচ্ছে...</p>
        </div>
      </section>
    );
  }

  if (!me) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-md mx-auto px-4">
          <div className="bg-card border border-border rounded-2xl p-8 text-center shadow-lg">
            <Shield className="mx-auto text-primary mb-4" size={48} />
            <h1 className="text-2xl font-bold text-foreground mb-2">সদস্য পোর্টাল প্রবেশাধিকার</h1>
            <p className="text-secondary text-sm mb-6">
              সদস্য পোর্টালে প্রবেশ করতে আপনার প্রাতিষ্ঠানিক অ্যাকাউন্ট দিয়ে লগইন করুন।
            </p>
            <Link
              href="/login"
              className="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl bg-primary text-white font-semibold text-sm hover:opacity-90 transition-all shadow-sm"
            >
              লগইন করুন
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const unreadNotes = notes.filter((n) => !n.read_at);

  return (
    <section className="section py-10 min-h-screen bg-background">
      <div className="container max-w-6xl mx-auto px-4 space-y-8">
        {/* Top Notification Toast */}
        {statusMessage && (
          <div
            className={`p-4 rounded-xl text-sm flex items-center gap-3 border shadow-sm ${
              statusMessage.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-700 dark:text-rose-400'
            }`}
          >
            {statusMessage.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
            <span className="font-medium">{statusMessage.text}</span>
          </div>
        )}

        {/* Header Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-border">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary mb-2">
              <IdCard size={14} /> PGCB MEMBER DASHBOARD
            </span>
            <h1 className="text-3xl font-extrabold text-foreground">স্বাগতম, {me.name_bn || me.name_en}</h1>
            <p className="text-secondary text-sm mt-1">
              সদস্যতা স্ট্যাটাস, ডিজিটাল পরিচয়পত্র, প্রোফাইল ও প্রাতিষ্ঠানিক কার্যাবলী পরিচালনা করুন।
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/portal/security"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border bg-card hover:bg-surface text-foreground text-sm font-semibold transition-all shadow-sm"
            >
              <Shield size={16} /> সেশন ও নিরাপত্তা
            </Link>
          </div>
        </div>

        {/* Quick KPI Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              MEMBERSHIP ID
            </span>
            <div className="text-xl font-extrabold text-foreground mt-1">
              {me.membership_id || 'প্রক্রিয়াধীন'}
            </div>
            <div className="mt-2">
              <span
                className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  me.membership_status === 'ACTIVE'
                    ? 'bg-emerald-500/10 text-emerald-600'
                    : 'bg-amber-500/10 text-amber-600'
                }`}
              >
                {me.membership_status || 'PENDING'}
              </span>
            </div>
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
              GRID CIRCLE
            </span>
            <div className="text-xl font-extrabold text-foreground mt-1 truncate">
              {me.circle_bn || 'নির্ধারিত হয়নি'}
            </div>
            <p className="text-xs text-secondary mt-2 truncate">
              {me.designation_bn || 'পদবি নির্ধারিত হয়নি'}
            </p>
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400">
              DIGITAL ID CARD
            </span>
            <div className="text-lg font-bold text-foreground mt-1">
              {me.membership_status === 'ACTIVE' ? 'সক্রিয় ও প্রস্তুত' : 'অনুমোদনের পর লভ্য'}
            </div>
            {me.membership_status === 'ACTIVE' && (
              <div className="flex gap-2 mt-2">
                <a
                  href={api.getDigitalCardUrl()}
                  target="_blank"
                  download
                  className="px-2.5 py-1 text-xs font-bold rounded-lg bg-primary text-white hover:opacity-90 transition-all"
                >
                  PNG
                </a>
                <a
                  href={api.getDigitalCardPdfUrl()}
                  target="_blank"
                  download
                  className="px-2.5 py-1 text-xs font-bold rounded-lg border border-border bg-surface hover:bg-border/50 text-foreground transition-all"
                >
                  PDF
                </a>
              </div>
            )}
          </div>

          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm">
            <span className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
              NOTIFICATIONS
            </span>
            <div className="text-xl font-extrabold text-foreground mt-1">
              {unreadNotes.length} টি অপঠিত
            </div>
            <p className="text-xs text-secondary mt-2">মোট {notes.length} টি বার্তা</p>
          </div>
        </div>

        {/* Digital ID Card Preview (If Active) */}
        {me.membership_status === 'ACTIVE' && (
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 pb-4 border-b border-border">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
                  DIGITAL CREDENTIAL
                </span>
                <h2 className="text-xl font-bold text-foreground">অফিসিয়াল ডিজিটাল পরিচয়পত্র (ID Card)</h2>
                <p className="text-xs text-secondary">
                  যাচাইযোগ্য কিউআর কোডসহ আপনার অফিসিয়াল সদস্য পরিচয়পত্র
                </p>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={api.getDigitalCardUrl()}
                  target="_blank"
                  download
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl bg-primary text-white hover:opacity-90 transition-all shadow-sm"
                >
                  <Download size={14} /> ডাউনলোড PNG
                </a>
                <a
                  href={api.getDigitalCardPdfUrl()}
                  target="_blank"
                  download
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl border border-border bg-surface hover:bg-border/50 text-foreground transition-all"
                >
                  <Download size={14} /> মুদ্রণযোগ্য PDF
                </a>
              </div>
            </div>

            <div className="flex justify-center p-4 bg-surface/50 rounded-xl border border-border">
              <div className="max-w-md w-full rounded-xl overflow-hidden border-2 border-amber-500/40 shadow-md">
                <img
                  src={api.getDigitalCardUrl()}
                  alt="Digital Member ID Card"
                  className="w-full h-auto object-contain block"
                />
              </div>
            </div>
          </div>
        )}

        {/* Profile & Application / Documents Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Profile Form */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
              <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-600">
                <User size={20} />
              </div>
              <div>
                <h2 className="text-lg font-bold text-foreground">সদস্য প্রোফাইল তথ্য</h2>
                <p className="text-xs text-secondary">আপনার পেশাগত ও ব্যক্তিগত তথ্য হালনাগাদ রাখুন</p>
              </div>
            </div>

            <form onSubmit={saveProfile} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">
                    বাংলা নাম <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={profile?.name_bn ?? ''}
                    onChange={(e) => setProfile({ ...profile, name_bn: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">English Name</label>
                  <input
                    type="text"
                    value={profile?.name_en ?? ''}
                    onChange={(e) => setProfile({ ...profile, name_en: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">মোবাইল নম্বর</label>
                  <input
                    type="text"
                    value={profile?.phone ?? ''}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">কর্মকর্তা / কর্মচারী আইডি</label>
                  <input
                    type="text"
                    value={profile?.employee_id ?? ''}
                    onChange={(e) => setProfile({ ...profile, employee_id: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">পদবি (বাংলা)</label>
                  <input
                    type="text"
                    value={profile?.designation_bn ?? ''}
                    onChange={(e) => setProfile({ ...profile, designation_bn: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">Designation (English)</label>
                  <input
                    type="text"
                    value={profile?.designation_en ?? ''}
                    onChange={(e) => setProfile({ ...profile, designation_en: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">ডিপ্লোমা প্রতিষ্ঠান</label>
                  <input
                    type="text"
                    value={profile?.diploma_institution ?? ''}
                    onChange={(e) => setProfile({ ...profile, diploma_institution: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">পাসের বছর</label>
                  <input
                    type="number"
                    value={profile?.graduation_year ?? ''}
                    onChange={(e) => setProfile({ ...profile, graduation_year: e.target.value ? Number(e.target.value) : null })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">জাতীয় পরিচয়পত্র (NID) নম্বর</label>
                  <input
                    type="text"
                    value={profile?.nid_number ?? ''}
                    onChange={(e) => setProfile({ ...profile, nid_number: e.target.value })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">গ্রিড সার্কেল</label>
                  <select
                    value={profile?.circle_id ?? ''}
                    onChange={(e) => setProfile({ ...profile, circle_id: e.target.value ? Number(e.target.value) : null })}
                    className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  >
                    <option value="">গ্রিড সার্কেল নির্বাচন করুন</option>
                    {circles.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name_bn} ({c.name_en})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground mb-1">বর্তমান ঠিকানা</label>
                <textarea
                  rows={2}
                  value={profile?.current_address ?? ''}
                  onChange={(e) => setProfile({ ...profile, current_address: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-foreground mb-1">স্থায়ী ঠিকানা</label>
                <textarea
                  rows={2}
                  value={profile?.permanent_address ?? ''}
                  onChange={(e) => setProfile({ ...profile, permanent_address: e.target.value })}
                  className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 px-4 rounded-xl bg-primary text-white font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
              >
                {saving ? 'সংরক্ষণ হচ্ছে...' : 'প্রোফাইল তথ্য সংরক্ষণ করুন'}
              </button>
            </form>
          </div>

          {/* Application & Documents */}
          <div className="space-y-8">
            {/* Membership Application Box */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between gap-3 mb-4 pb-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600">
                    <FileText size={20} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-foreground">সদস্য আবেদন স্থিতি</h2>
                    <p className="text-xs text-secondary">আবেদনের পর্যালোচনা অবস্থা</p>
                  </div>
                </div>

                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    application?.status === 'ACTIVE'
                      ? 'bg-emerald-500/10 text-emerald-600'
                      : application?.status === 'SUBMITTED'
                      ? 'bg-blue-500/10 text-blue-600'
                      : 'bg-amber-500/10 text-amber-600'
                  }`}
                >
                  {application?.status || 'PENDING'}
                </span>
              </div>

              <p className="text-xs text-secondary mb-4 leading-relaxed">
                প্রোফাইল তথ্য ও প্রয়োজনীয় নথিপত্র (জাতীয় পরিচয়পত্র, ডিপ্লোমা সনদ, ছবি) আপলোড করার পর আপনার সদস্য আবেদন পর্যালোচনা ও অনুমোদনের জন্য সচিবালয়ে জমা দিন।
              </p>

              <button
                onClick={submitApplication}
                disabled={['SUBMITTED', 'UNDER_REVIEW', 'ACTIVE'].includes(application?.status)}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-sm"
              >
                {application?.status === 'ACTIVE'
                  ? 'সদস্যপদ অনুমোদিত'
                  : application?.status === 'SUBMITTED'
                  ? 'পর্যালোচনার অপেক্ষায় আছে'
                  : 'আবেদন জমা দিন'}
              </button>
            </div>

            {/* Document Uploads */}
            <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600">
                  <Upload size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">প্রয়োজনীয় নথিপত্র</h2>
                  <p className="text-xs text-secondary">PDF অথবা ইমেজ ফরম্যাট (সর্বোচ্চ ১০ এমবি)</p>
                </div>
              </div>

              {uploading && (
                <div className="mb-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 text-xs flex items-center gap-2">
                  <div className="animate-spin rounded-full h-3.5 w-3.5 border-2 border-amber-600 border-t-transparent"></div>
                  নথি আপলোড ও যাচাই হচ্ছে...
                </div>
              )}

              <div className="grid grid-cols-3 gap-3 mb-6">
                {[
                  { type: 'NID', label: 'জাতীয় পরিচয়পত্র' },
                  { type: 'CERTIFICATE', label: 'ডিপ্লোমা সনদ' },
                  { type: 'PHOTO', label: 'পাসপোর্ট ছবি' },
                ].map((docItem) => (
                  <label
                    key={docItem.type}
                    className="flex flex-col items-center justify-center p-3 rounded-xl border border-dashed border-border bg-surface/50 hover:bg-surface cursor-pointer text-center transition-all group"
                  >
                    <Upload size={18} className="text-secondary group-hover:text-primary mb-1 transition-colors" />
                    <span className="text-xs font-semibold text-foreground">{docItem.label}</span>
                    <span className="text-[10px] text-secondary mt-0.5">আপলোড</span>
                    <input
                      type="file"
                      accept={docItem.type === 'PHOTO' ? 'image/*' : 'image/*,application/pdf'}
                      hidden
                      onChange={(e) => uploadDoc(e, docItem.type)}
                    />
                  </label>
                ))}
              </div>

              <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
                {docs.length === 0 ? (
                  <p className="text-xs text-secondary text-center py-4">এখনো কোনো নথি আপলোড করা হয়নি।</p>
                ) : (
                  docs.map((d) => (
                    <div
                      key={d.id}
                      className="p-3 rounded-xl border border-border bg-surface text-xs flex items-center justify-between gap-2"
                    >
                      <div className="truncate">
                        <span className="font-bold text-foreground mr-2">[{d.document_type}]</span>
                        <span className="text-secondary truncate">{d.filename}</span>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 ${
                          d.review_status === 'APPROVED'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : d.review_status === 'REJECTED'
                            ? 'bg-rose-500/10 text-rose-600'
                            : 'bg-amber-500/10 text-amber-600'
                        }`}
                      >
                        {d.review_status}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Events, Payments & Notifications */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Events */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
              <Calendar size={18} className="text-primary" />
              <h2 className="text-base font-bold text-foreground">আমার ইভেন্ট নিবন্ধন</h2>
            </div>
            <div className="space-y-3">
              {registrations.length === 0 ? (
                <p className="text-xs text-secondary py-4 text-center">কোনো ইভেন্ট নিবন্ধন নেই।</p>
              ) : (
                registrations.map((r) => (
                  <div key={r.id} className="p-3 rounded-xl border border-border bg-surface text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <strong className="text-foreground">টিকিট: {r.ticket_code}</strong>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">
                        {r.registration_status}
                      </span>
                    </div>
                    <div className="text-[11px] text-secondary">
                      উপস্থিতি: {r.attendance_status} · পেমেন্ট: {r.payment_status}
                    </div>
                    <Link
                      href={`/events/ticket/${encodeURIComponent(r.ticket_token || r.ticket_code)}`}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline"
                    >
                      টিকিট বিস্তারিত দেখুন <ArrowRight size={12} />
                    </Link>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Payments */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
              <CreditCard size={18} className="text-emerald-600" />
              <h2 className="text-base font-bold text-foreground">পেমেন্ট ইতিহাস</h2>
            </div>
            <div className="space-y-3">
              {payments.length === 0 ? (
                <p className="text-xs text-secondary py-4 text-center">কোনো পেমেন্ট রেকর্ড পাওয়া যায়নি।</p>
              ) : (
                payments.slice(0, 5).map((p) => (
                  <div key={p.id} className="p-3 rounded-xl border border-border bg-surface text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <strong className="text-foreground">{p.purpose}</strong>
                      <span className="font-bold text-emerald-600">
                        {p.amount} {p.currency}
                      </span>
                    </div>
                    <div className="text-[11px] text-secondary flex items-center justify-between">
                      <span>{p.provider}</span>
                      <span
                        className={`font-semibold ${
                          p.status === 'PAID' ? 'text-emerald-600' : 'text-amber-600'
                        }`}
                      >
                        {p.status}
                      </span>
                    </div>
                    {p.transaction_ref && (
                      <div className="text-[10px] text-secondary font-mono truncate">
                        Ref: {p.transaction_ref}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Notifications */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
              <Bell size={18} className="text-amber-600" />
              <h2 className="text-base font-bold text-foreground">সাম্প্রতিক বার্তা</h2>
            </div>
            <div className="space-y-3">
              {notes.length === 0 ? (
                <p className="text-xs text-secondary py-4 text-center">কোনো নতুন বার্তা নেই।</p>
              ) : (
                notes.slice(0, 5).map((n) => (
                  <div key={n.id} className="p-3 rounded-xl border border-border bg-surface text-xs space-y-1">
                    <strong className="text-foreground block">{n.title_bn}</strong>
                    <p className="text-secondary text-[11px] line-clamp-2">{n.body_bn}</p>
                    <small className="text-[10px] text-secondary block font-mono">
                      {new Date(n.created_at).toLocaleString('bn-BD')}
                    </small>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
