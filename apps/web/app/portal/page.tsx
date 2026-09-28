'use client';

import { useEffect, useState, FormEvent, ChangeEvent } from 'react';
import Link from 'next/link';
import {
  api,
  CircleItem,
  MemberDashboardData,
  RenewalOptionItem,
  CertificateWalletItem,
  NotificationPreferences,
} from '@/lib/api';
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
  ArrowRight,
  Download,
  IdCard,
  Award,
  RefreshCw,
  CheckCheck,
  Settings,
  ExternalLink,
  Activity,
} from 'lucide-react';

export default function MemberPortal() {
  const [me, setMe] = useState<any>(null);
  const [dashboard, setDashboard] = useState<MemberDashboardData | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [application, setApplication] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [renewalOptions, setRenewalOptions] = useState<RenewalOptionItem[]>([]);
  const [renewals, setRenewals] = useState<any[]>([]);
  const [certificates, setCertificates] = useState<CertificateWalletItem[]>([]);
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences | null>(null);

  const [selectedPlan, setSelectedPlan] = useState<string>('RENEWAL_1YR');
  const [renewing, setRenewing] = useState(false);
  const [showNotifSettings, setShowNotifSettings] = useState(false);

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

      const [
        dashRes,
        p,
        a,
        d,
        n,
        c,
        regRes,
        pay,
        renOptRes,
        renListRes,
        certRes,
        prefRes,
      ] = await Promise.allSettled([
        api.getMemberDashboard(),
        api.getProfile(),
        api.getMemberApplication(),
        api.getMemberDocuments(),
        api.getMemberNotifications(),
        api.getCircles(),
        api.getMyEventRegistrations(),
        api.getMemberPayments(),
        api.getRenewalOptions(),
        api.getRenewals(),
        api.getMemberCertificates(),
        api.getNotificationPreferences(),
      ]);

      if (dashRes.status === 'fulfilled') setDashboard(dashRes.value);
      if (p.status === 'fulfilled') setProfile(p.value);
      if (a.status === 'fulfilled') setApplication(a.value);
      if (d.status === 'fulfilled') setDocs(d.value);
      if (n.status === 'fulfilled') setNotes(n.value);
      if (c.status === 'fulfilled') setCircles(c.value);
      if (regRes.status === 'fulfilled') setRegistrations(regRes.value);
      if (pay.status === 'fulfilled') setPayments(pay.value);
      if (renOptRes.status === 'fulfilled') setRenewalOptions(renOptRes.value.plans || []);
      if (renListRes.status === 'fulfilled') setRenewals(renListRes.value);
      if (certRes.status === 'fulfilled') setCertificates(certRes.value);
      if (prefRes.status === 'fulfilled') setNotifPrefs(prefRes.value);
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

  async function handleInitiateRenewal() {
    setRenewing(true);
    try {
      const res = await api.initiateRenewal(selectedPlan, 'SSLCOMMERZ');
      notify(
        `সদস্যপদ নবায়ন লেনদেন তৈরি হয়েছে (Ref: ${res.transaction_ref}, পরিমাণ: ৳${res.amount})।`,
        'success'
      );
      loadData();
    } catch (err: any) {
      notify(err.message || 'নবায়ন প্রক্রিয়া শুরু করা যায়নি।', 'error');
    } finally {
      setRenewing(false);
    }
  }

  async function handleMarkRead(notificationId: number) {
    try {
      await api.markNotificationRead(notificationId);
      setNotes((prev) =>
        prev.map((item) =>
          item.id === notificationId ? { ...item, is_read: true, indicator: '○', read_at: new Date().toISOString() } : item
        )
      );
    } catch {}
  }

  async function handleMarkAllRead() {
    try {
      await api.markAllNotificationsRead();
      setNotes((prev) =>
        prev.map((item) => ({ ...item, is_read: true, indicator: '○', read_at: new Date().toISOString() }))
      );
      notify('সকল বার্তা পঠিত হিসেবে চিহ্নিত করা হয়েছে।', 'success');
    } catch {}
  }

  async function handleToggleNotifPref(key: keyof NotificationPreferences) {
    if (!notifPrefs) return;
    const next = { ...notifPrefs, [key]: !notifPrefs[key] };
    setNotifPrefs(next);
    try {
      await api.updateNotificationPreferences(next);
      notify('বিজ্ঞপ্তি পছন্দসমূহ হালনাগাদ করা হয়েছে।', 'success');
    } catch {}
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

  const unreadNotes = notes.filter((n) => !n.read_at && !n.is_read);
  const membershipCard = dashboard?.membership;
  const effectiveStatus = membershipCard?.status || me.membership_status || 'PENDING';

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

        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-6 border-b border-border">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary mb-2">
              <IdCard size={14} /> PGCB MEMBER PORTAL 2.0
            </span>
            <h1 className="text-3xl font-extrabold text-foreground">
              {dashboard?.greeting || `স্বাগতম, ${me.name_bn || me.name_en}`}
            </h1>
            <p className="text-secondary text-sm mt-1">
              সদস্যতা স্ট্যাটাস, ডিজিটাল পরিচয়পত্র, সনদ ওয়ালেট, নবায়ন এবং প্রাতিষ্ঠানিক সেবা পরিচালনা করুন।
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/portal/id-card"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-sm font-semibold hover:opacity-90 transition-all shadow-sm"
            >
              <IdCard size={16} /> ডিজিটাল আইডি কার্ড
            </Link>
            <Link
              href="/portal/security"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-border bg-card hover:bg-surface text-foreground text-sm font-semibold transition-all shadow-sm"
            >
              <Shield size={16} /> সেশন ও নিরাপত্তা
            </Link>
          </div>
        </div>

        {/* Hero Membership Status Card (Sprint 2 Spec) */}
        <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white p-6 md:p-8 shadow-lg border border-amber-500/30">
          <div className="flex flex-col md:flex-row justify-between gap-6">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2.5">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold uppercase tracking-wider ${
                    effectiveStatus === 'ACTIVE'
                      ? 'bg-emerald-500 text-white'
                      : effectiveStatus === 'EXPIRING_SOON'
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-rose-500 text-white'
                  }`}
                >
                  ● {effectiveStatus}
                </span>
                {membershipCard?.days_remaining !== null && membershipCard?.days_remaining !== undefined && (
                  <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 text-amber-300 font-semibold">
                    {membershipCard.days_remaining > 0
                      ? `${membershipCard.days_remaining} দিন বাকি`
                      : 'মেয়াদ উত্তীর্ণ'}
                  </span>
                )}
              </div>

              <div>
                <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold">Membership ID</p>
                <div className="text-2xl md:text-3xl font-mono font-extrabold text-amber-400">
                  {membershipCard?.member_id || me.membership_id || 'PGD-PENDING'}
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2 text-xs">
                <div>
                  <span className="text-slate-400 block">Valid Until</span>
                  <strong className="text-white text-sm">
                    {membershipCard?.valid_until_formatted || 'Lifetime / N/A'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block">Grid Circle</span>
                  <strong className="text-white text-sm">
                    {membershipCard?.circle_name_bn || me.circle_bn || 'নির্ধারিত হয়নি'}
                  </strong>
                </div>
                <div>
                  <span className="text-slate-400 block">Designation</span>
                  <strong className="text-white text-sm">
                    {membershipCard?.designation_bn || me.designation_bn || 'Engineer'}
                  </strong>
                </div>
              </div>
            </div>

            <div className="flex flex-col justify-between items-start md:items-end gap-3">
              <div className="flex flex-wrap gap-2">
                <Link
                  href="/portal/id-card"
                  className="px-4 py-2.5 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-colors"
                >
                  Digital ID Card দেখুন
                </Link>
                <a
                  href="#renewal-section"
                  className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs transition-colors"
                >
                  সদস্যপদ নবায়ন করুন
                </a>
              </div>
              <div className="text-[11px] text-slate-300">
                সনদ ওয়ালেট: <strong>{certificates.length}</strong> · অপঠিত বার্তা:{' '}
                <strong>{unreadNotes.length}</strong>
              </div>
            </div>
          </div>
        </div>

        {/* 6 Quick Action Tiles */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Digital ID', sub: 'পরিচয়পত্র', href: '/portal/id-card', icon: IdCard, color: 'text-blue-600 bg-blue-500/10' },
            { label: 'Renew', sub: 'সদস্যপদ নবায়ন', href: '#renewal-section', icon: RefreshCw, color: 'text-emerald-600 bg-emerald-500/10' },
            { label: 'Certificates', sub: `${certificates.length} টি সনদ`, href: '#certificate-wallet', icon: Award, color: 'text-amber-600 bg-amber-500/10' },
            { label: 'Documents', sub: 'সংরক্ষিত নথি', href: '/documents', icon: FileText, color: 'text-purple-600 bg-purple-500/10' },
            { label: 'Payments', sub: 'রশিদ ও লেনদেন', href: '#payments-section', icon: CreditCard, color: 'text-teal-600 bg-teal-500/10' },
            { label: 'Events', sub: 'ইভেন্ট ও নিবন্ধন', href: '/events', icon: Calendar, color: 'text-rose-600 bg-rose-500/10' },
          ].map((tile) => {
            const Icon = tile.icon;
            return (
              <a
                key={tile.label}
                href={tile.href}
                className="bg-card border border-border hover:border-primary/40 rounded-2xl p-4 flex flex-col items-start gap-2 shadow-sm hover:shadow transition-all"
              >
                <div className={`p-2.5 rounded-xl ${tile.color}`}>
                  <Icon size={18} />
                </div>
                <div>
                  <div className="text-sm font-bold text-foreground">{tile.label}</div>
                  <div className="text-[11px] text-secondary">{tile.sub}</div>
                </div>
              </a>
            );
          })}
        </div>

        {/* Membership Renewal & Certificate Wallet Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Membership Renewal Workflow */}
          <div id="renewal-section" className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600">
                  <RefreshCw size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">সদস্যপদ নবায়ন (Membership Renewal)</h2>
                  <p className="text-xs text-secondary">১ বছর, ২ বছর অথবা আজীবন সদস্যপদ নবায়ন করুন</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {(renewalOptions.length > 0
                ? renewalOptions
                : [
                    { code: 'RENEWAL_1YR', label_en: '1 Year Renewal', label_bn: '১ বছর মেয়াদী নবায়ন', years: 1, fee: 2000, currency: 'BDT' },
                    { code: 'RENEWAL_2YR', label_en: '2 Year Renewal', label_bn: '২ বছর মেয়াদী নবায়ন', years: 2, fee: 4000, currency: 'BDT' },
                    { code: 'LIFE', label_en: 'Lifetime Membership', label_bn: 'আজীবন সদস্যপদ', years: 50, fee: 10000, currency: 'BDT' },
                  ]
              ).map((plan) => {
                const active = selectedPlan === plan.code;
                return (
                  <button
                    key={plan.code}
                    type="button"
                    onClick={() => setSelectedPlan(plan.code)}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      active
                        ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                        : 'border-border bg-surface hover:border-primary/40'
                    }`}
                  >
                    <div className="text-xs font-bold text-foreground">{plan.label_bn}</div>
                    <div className="text-[11px] text-secondary">{plan.label_en}</div>
                    <div className="text-lg font-extrabold text-primary mt-2">৳{plan.fee.toLocaleString()}</div>
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={handleInitiateRenewal}
              disabled={renewing}
              className="w-full py-2.5 px-4 rounded-xl bg-primary text-white text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
            >
              {renewing ? 'নবায়ন প্রক্রিয়া শুরু হচ্ছে...' : 'নবায়ন ও পেমেন্ট শুরু করুন'}
            </button>

            {renewals.length > 0 && (
              <div className="pt-3 border-t border-border space-y-2">
                <span className="text-xs font-bold text-secondary uppercase">সাম্প্রতিক নবায়ন রেকর্ড</span>
                {renewals.slice(0, 3).map((r) => (
                  <div
                    key={r.id}
                    className="p-2.5 rounded-xl bg-surface border border-border text-xs flex items-center justify-between"
                  >
                    <div>
                      <strong className="text-foreground">{r.plan_code}</strong>
                      <span className="text-secondary ml-2">({r.years} yr)</span>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        r.status === 'COMPLETED'
                          ? 'bg-emerald-500/10 text-emerald-600'
                          : 'bg-amber-500/10 text-amber-600'
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Certificate Wallet */}
          <div id="certificate-wallet" className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600">
                  <Award size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">সনদ ওয়ালেট (Certificate Wallet)</h2>
                  <p className="text-xs text-secondary">সদস্যপদ সনদ ও প্রশিক্ষণ/ইভেন্ট সনদসমূহ</p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-700">
                {certificates.length} টি সনদ
              </span>
            </div>

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {certificates.length === 0 ? (
                <p className="text-xs text-secondary text-center py-8">
                  আপনার ওয়ালেটে এখনো কোনো ইস্যুকৃত সনদ নেই।
                </p>
              ) : (
                certificates.map((cert) => (
                  <div
                    key={cert.id}
                    className="p-4 rounded-xl border border-border bg-surface space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                          {cert.certificate_type}
                        </span>
                        <h3 className="text-sm font-bold text-foreground">
                          {cert.title_bn || cert.title_en}
                        </h3>
                        <p className="text-[11px] font-mono text-secondary">
                          No: {cert.certificate_no}
                        </p>
                      </div>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          cert.status === 'ACTIVE'
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : 'bg-rose-500/10 text-rose-600'
                        }`}
                      >
                        {cert.status}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <a
                        href={api.getCertificatePngUrl(cert.certificate_no)}
                        target="_blank"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary text-white text-[11px] font-semibold hover:opacity-90"
                      >
                        <ExternalLink size={12} /> View
                      </a>
                      <a
                        href={api.getCertificatePdfUrl(cert.certificate_no)}
                        target="_blank"
                        download
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border bg-card text-foreground text-[11px] font-semibold hover:bg-border/40"
                      >
                        <Download size={12} /> Download PDF
                      </a>
                      <Link
                        href={`/verify?certificate=${encodeURIComponent(cert.certificate_no)}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-700 text-[11px] font-semibold"
                      >
                        Verify
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

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
                    onChange={(e) =>
                      setProfile({ ...profile, graduation_year: e.target.value ? Number(e.target.value) : null })
                    }
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
                    onChange={(e) =>
                      setProfile({ ...profile, circle_id: e.target.value ? Number(e.target.value) : null })
                    }
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

        {/* Events, Payments & Notification Center */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Events & Recent Activity */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
            <div>
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
                <Calendar size={18} className="text-primary" />
                <h2 className="text-base font-bold text-foreground">আমার ইভেন্ট নিবন্ধন</h2>
              </div>
              <div className="space-y-3">
                {registrations.length === 0 ? (
                  <p className="text-xs text-secondary py-3 text-center">কোনো ইভেন্ট নিবন্ধন নেই।</p>
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

            {dashboard?.recent_activity && dashboard.recent_activity.length > 0 && (
              <div className="pt-4 border-t border-border">
                <div className="flex items-center gap-2 mb-3">
                  <Activity size={16} className="text-secondary" />
                  <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">সাম্প্রতিক কার্যক্রম</h3>
                </div>
                <div className="space-y-2">
                  {dashboard.recent_activity.slice(0, 4).map((act, idx) => (
                    <div key={idx} className="text-xs flex items-start justify-between gap-2 py-1">
                      <span className="text-foreground font-medium">{act.title_bn || act.title}</span>
                      <span className="text-[10px] text-secondary shrink-0">{act.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Payment History with Receipt PDF */}
          <div id="payments-section" className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-border">
              <CreditCard size={18} className="text-emerald-600" />
              <h2 className="text-base font-bold text-foreground">পেমেন্ট ও রশিদ ইতিহাস</h2>
            </div>
            <div className="space-y-3">
              {payments.length === 0 ? (
                <p className="text-xs text-secondary py-4 text-center">কোনো পেমেন্ট রেকর্ড পাওয়া যায়নি।</p>
              ) : (
                payments.slice(0, 6).map((p) => (
                  <div key={p.id} className="p-3 rounded-xl border border-border bg-surface text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <strong className="text-foreground">{p.purpose_label || p.purpose}</strong>
                      <span className="font-bold text-emerald-600">
                        {p.amount_formatted || `${p.amount} ${p.currency}`}
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
                    <div className="flex items-center justify-between pt-1">
                      {p.transaction_ref && (
                        <span className="text-[10px] text-secondary font-mono truncate max-w-[140px]">
                          {p.transaction_ref}
                        </span>
                      )}
                      {p.status === 'PAID' && (
                        <a
                          href={api.getPaymentReceiptPdfUrl(p.id)}
                          target="_blank"
                          download
                          className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline"
                        >
                          <Download size={12} /> রশিদ (PDF)
                        </a>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Notification Center */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Bell size={18} className="text-amber-600" />
                <h2 className="text-base font-bold text-foreground">বিজ্ঞপ্তি কেন্দ্র</h2>
              </div>
              <div className="flex items-center gap-2">
                {unreadNotes.length > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAllRead}
                    title="সকল বার্তা পঠিত করুন"
                    className="text-[11px] font-semibold text-primary hover:underline inline-flex items-center gap-1"
                  >
                    <CheckCheck size={13} /> সব পঠিত
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setShowNotifSettings(!showNotifSettings)}
                  title="বিজ্ঞপ্তি পছন্দসমূহ"
                  className="p-1 rounded-lg hover:bg-surface text-secondary"
                >
                  <Settings size={15} />
                </button>
              </div>
            </div>

            {showNotifSettings && notifPrefs && (
              <div className="mb-4 p-3 rounded-xl bg-surface border border-border space-y-2 text-xs">
                <div className="font-bold text-foreground">বিজ্ঞপ্তি চ্যানেল পছন্দসমূহ</div>
                {[
                  { key: 'email_enabled' as const, label: 'ইমেইল বিজ্ঞপ্তি (Email)' },
                  { key: 'sms_enabled' as const, label: 'এসএমএস অ্যালার্ট (SMS)' },
                  { key: 'push_enabled' as const, label: 'পুশ নোটিফিকেশন (PWA Push)' },
                ].map((item) => (
                  <label key={item.key} className="flex items-center justify-between cursor-pointer">
                    <span className="text-secondary">{item.label}</span>
                    <input
                      type="checkbox"
                      checked={Boolean(notifPrefs[item.key])}
                      onChange={() => handleToggleNotifPref(item.key)}
                      className="rounded border-border"
                    />
                  </label>
                ))}
              </div>
            )}

            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {notes.length === 0 ? (
                <p className="text-xs text-secondary py-4 text-center">কোনো নতুন বার্তা নেই।</p>
              ) : (
                notes.slice(0, 8).map((n) => {
                  const isUnread = !n.read_at && !n.is_read;
                  return (
                    <div
                      key={n.id}
                      onClick={() => isUnread && handleMarkRead(n.id)}
                      className={`p-3 rounded-xl border text-xs space-y-1 cursor-pointer transition-colors ${
                        isUnread
                          ? 'border-primary/40 bg-primary/5'
                          : 'border-border bg-surface'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <strong className="text-foreground flex items-center gap-1.5">
                          <span className={isUnread ? 'text-primary font-extrabold' : 'text-secondary'}>
                            {n.indicator || (isUnread ? '●' : '○')}
                          </span>
                          {n.title_bn}
                        </strong>
                        <span className="text-[10px] text-secondary shrink-0">
                          {n.relative_time || new Date(n.created_at).toLocaleDateString('bn-BD')}
                        </span>
                      </div>
                      <p className="text-secondary text-[11px] line-clamp-2 pl-3.5">{n.body_bn}</p>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
