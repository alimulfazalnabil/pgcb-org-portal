'use client';

import { useEffect, useState, FormEvent, ChangeEvent } from 'react';
import Link from 'next/link';
import {
  api,
  API_BASE_URL,
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
  LayoutDashboard,
  Sparkles,
  Bookmark,
  Lock,
  LogOut,
  Send,
  Clock,
  CheckCircle2,
  XCircle,
  Eye,
  FileCheck,
  Briefcase,
  Phone,
  HeartHandshake,
} from 'lucide-react';

type PortalTab =
  | 'dashboard'
  | 'profile'
  | 'membership'
  | 'application'
  | 'payments'
  | 'documents'
  | 'digital-id'
  | 'certificates'
  | 'events'
  | 'notices'
  | 'notifications'
  | 'ai-assistant'
  | 'settings';

export default function MemberPortal() {
  const [activeTab, setActiveTab] = useState<PortalTab>('dashboard');
  const [me, setMe] = useState<any>(null);
  const [dashboard, setDashboard] = useState<MemberDashboardData | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [application, setApplication] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [updates, setUpdates] = useState<any[]>([]);
  const [registrations, setRegistrations] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [renewalOptions, setRenewalOptions] = useState<RenewalOptionItem[]>([]);
  const [renewals, setRenewals] = useState<any[]>([]);
  const [certificates, setCertificates] = useState<CertificateWalletItem[]>([]);
  const [notifPrefs, setNotifPrefs] = useState<NotificationPreferences | null>(null);
  const [changeRequests, setChangeRequests] = useState<any[]>([]);
  const [memberSettings, setMemberSettings] = useState<any>(null);
  const [loginHistory, setLoginHistory] = useState<{ sessions: any[]; security_events: any[] }>({
    sessions: [],
    security_events: [],
  });

  // Renewal multi-step state
  const [selectedPlan, setSelectedPlan] = useState<string>('RENEWAL_1YR');
  const [renewalProvider, setRenewalProvider] = useState<string>('SSLCOMMERZ');
  const [renewalStep, setRenewalStep] = useState<1 | 2 | 3>(1);
  const [lastRenewalTx, setLastRenewalTx] = useState<any>(null);
  const [renewing, setRenewing] = useState(false);

  // Sensitive field verification request state
  const [changeField, setChangeField] = useState<string>('name_bn');
  const [changeValue, setChangeValue] = useState<string>('');
  const [changeReason, setChangeReason] = useState<string>('');
  const [submittingChange, setSubmittingChange] = useState(false);

  // Updates filter state
  const [updateFilter, setUpdateFilter] = useState<'ALL' | 'CIRCULAR' | 'NOTICE' | 'BOOKMARKED'>('ALL');

  // AI Assistant state
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiConversationId, setAiConversationId] = useState<number | null>(null);
  const [aiMessages, setAiMessages] = useState<
    Array<{
      role: 'user' | 'assistant';
      content: string;
      confidence?: string;
      intent?: string;
      sources?: any[];
      actions?: Array<{ label_bn: string; label_en: string; url: string }>;
    }>
  >([]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  function notify(text: string, type: 'success' | 'error' = 'success') {
    setStatusMessage({ text, type });
    window.setTimeout(() => setStatusMessage(null), 4500);
  }

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const tabParam = (params.get('tab') || '').toLowerCase();
      const tabMap: Record<string, PortalTab> = {
        dashboard: 'dashboard',
        profile: 'profile',
        membership: 'membership',
        renewal: 'membership',
        application: 'application',
        payments: 'payments',
        documents: 'documents',
        'digital-id': 'digital-id',
        id: 'digital-id',
        certificates: 'certificates',
        events: 'events',
        notices: 'notices',
        circulars: 'notices',
        notifications: 'notifications',
        'ai-assistant': 'ai-assistant',
        ai: 'ai-assistant',
        settings: 'settings',
      };
      if (tabParam && tabMap[tabParam]) {
        setActiveTab(tabMap[tabParam]);
      }
    }
  }, []);

  function switchTab(tab: PortalTab) {
    setActiveTab(tab);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('tab', tab);
      window.history.replaceState({}, '', url.toString());
    }
  }

  async function loadData() {
    try {
      const meData = await api.getMe();
      setMe(meData);

      const [
        dashRes,
        p,
        a,
        tlRes,
        d,
        n,
        c,
        regRes,
        pay,
        renOptRes,
        renListRes,
        certRes,
        prefRes,
        crRes,
        updRes,
        setRes,
        lhRes,
      ] = await Promise.allSettled([
        api.getMemberDashboard(),
        api.getProfile(),
        api.getMemberApplication(),
        api.getApplicationTimeline(),
        api.getMemberDocuments(),
        api.getMemberNotifications(),
        api.getCircles(),
        api.getMyEventRegistrations(),
        api.getMemberPayments(),
        api.getRenewalOptions(),
        api.getRenewals(),
        api.getMemberCertificates(),
        api.getNotificationPreferences(),
        api.getProfileChangeRequests(),
        api.getMemberUpdates(),
        api.getMemberSettings(),
        api.getMemberLoginHistory(),
      ]);

      if (dashRes.status === 'fulfilled') {
        setDashboard(dashRes.value);
        if (dashRes.value?.application) setTimeline(dashRes.value.application);
        if (dashRes.value?.circulars) setUpdates(dashRes.value.circulars);
      }
      if (p.status === 'fulfilled') setProfile(p.value);
      if (a.status === 'fulfilled') setApplication(a.value);
      if (tlRes.status === 'fulfilled') setTimeline(tlRes.value);
      if (d.status === 'fulfilled') setDocs(d.value);
      if (n.status === 'fulfilled') setNotes(n.value);
      if (c.status === 'fulfilled') setCircles(c.value);
      if (regRes.status === 'fulfilled') setRegistrations(regRes.value);
      if (pay.status === 'fulfilled') setPayments(pay.value);
      if (renOptRes.status === 'fulfilled') {
        const opts = renOptRes.value?.options || renOptRes.value?.periods || renOptRes.value?.plans || [];
        setRenewalOptions(opts);
      }
      if (renListRes.status === 'fulfilled') setRenewals(renListRes.value);
      if (certRes.status === 'fulfilled') setCertificates(certRes.value);
      if (prefRes.status === 'fulfilled') setNotifPrefs(prefRes.value);
      if (crRes.status === 'fulfilled') {
        setChangeRequests(crRes.value?.items || crRes.value?.change_requests || []);
      }
      if (updRes.status === 'fulfilled' && updRes.value?.items) {
        setUpdates(updRes.value.items);
      }
      if (setRes.status === 'fulfilled') setMemberSettings(setRes.value);
      if (lhRes.status === 'fulfilled') setLoginHistory(lhRes.value);
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
      const res = await api.updateProfile(profile);
      if (res?.pending_change_requests && res.pending_change_requests.length > 0) {
        notify(
          `প্রোফাইল সংরক্ষিত হয়েছে এবং ${res.pending_change_requests.length} টি সংবেদনশীল তথ্যের পরিবর্তনের আবেদন অনুমোদনের জন্য পাঠানো হয়েছে।`,
          'success'
        );
      } else {
        notify('প্রোফাইল তথ্য সফলভাবে সংরক্ষণ করা হয়েছে।', 'success');
      }
      loadData();
    } catch (err: any) {
      notify(err.message || 'প্রোফাইল সংরক্ষণ ব্যর্থ হয়েছে।', 'error');
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmitChangeRequest(e: FormEvent) {
    e.preventDefault();
    if (!changeValue.trim()) return;
    setSubmittingChange(true);
    try {
      await api.createProfileChangeRequest({
        field_name: changeField,
        requested_value: changeValue.trim(),
        reason: changeReason.trim() || 'Requested from Member Portal',
      });
      setChangeValue('');
      setChangeReason('');
      notify('সংবেদনশীল তথ্য পরিবর্তনের আবেদন সচিবালয়ে জমা দেওয়া হয়েছে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'আবেদন জমা দেওয়া যায়নি।', 'error');
    } finally {
      setSubmittingChange(false);
    }
  }

  async function handleSaveDraftApplication() {
    try {
      const res = await api.saveApplicationDraft();
      setApplication(res);
      notify('সদস্য আবেদন খসড়া (Draft) হিসেবে সংরক্ষিত হয়েছে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'খসড়া সংরক্ষণ ব্যর্থ হয়েছে।', 'error');
    }
  }

  async function submitApplication() {
    try {
      const res = await api.submitMemberApplication();
      setApplication(res);
      notify('আপনার সদস্য আবেদন সফলভাবে জমা দেওয়া হয়েছে। সচিবালয় পর্যালোচনার পর অবহিত করা হবে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'আবেদন জমা দেওয়া যায়নি।', 'error');
    }
  }

  async function handleCancelApplication() {
    try {
      const res = await api.cancelApplication();
      setApplication(res);
      notify('আবেদন বাতিল করা হয়েছে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'আবেদন বাতিল করা যায়নি।', 'error');
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
      loadData();
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
      const res = await api.initiateRenewal({
        period: selectedPlan,
        plan_code: selectedPlan,
        provider: renewalProvider,
      });
      setLastRenewalTx(res);
      setRenewalStep(3);
      notify(
        `সদস্যপদ নবায়ন লেনদেন তৈরি হয়েছে (Ref: ${res.transaction_id || res.transaction_ref}, পরিমাণ: ৳${res.amount})।`,
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
          item.id === notificationId
            ? { ...item, is_read: true, indicator: '○', read_at: new Date().toISOString() }
            : item
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

  async function handleUpdateSettings(patch: Record<string, any>) {
    try {
      const res = await api.updateMemberSettings(patch);
      setMemberSettings(res);
      notify('সেটিংস সফলভাবে হালনাগাদ করা হয়েছে।', 'success');
      loadData();
    } catch (err: any) {
      notify(err.message || 'সেটিংস হালনাগাদ ব্যর্থ হয়েছে।', 'error');
    }
  }

  async function handleToggleBookmark(contentType: string, contentId: number) {
    try {
      const res = await api.toggleBookmarkUpdate(contentType, contentId);
      setUpdates((prev) =>
        prev.map((u) =>
          u.content_type === contentType && u.id === contentId
            ? { ...u, is_bookmarked: res.is_bookmarked, is_read: true }
            : u
        )
      );
    } catch {}
  }

  async function handleMarkUpdateRead(contentType: string, contentId: number) {
    try {
      await api.markUpdateRead(contentType, contentId);
      setUpdates((prev) =>
        prev.map((u) =>
          u.content_type === contentType && u.id === contentId ? { ...u, is_read: true } : u
        )
      );
    } catch {}
  }

  async function handleAskAi(customPrompt?: string) {
    const q = (customPrompt ?? aiQuery).trim();
    if (!q || aiLoading) return;
    setAiQuery('');
    setAiMessages((prev) => [...prev, { role: 'user', content: q }]);
    setAiLoading(true);
    try {
      const res = await api.chatKnowledge(q, aiConversationId);
      if (res?.conversation_id) setAiConversationId(res.conversation_id);
      setAiMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer_bn || res.answer || 'উত্তর পাওয়া গেছে।',
          confidence: res.confidence,
          intent: res.intent,
          sources: res.sources || [],
          actions: res.actions || [],
        },
      ]);
    } catch (err: any) {
      setAiMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'দুঃখিত, এই মুহূর্তে এআই সহায়িকা উত্তর দিতে পারছে না। অনুগ্রহ করে আবার চেষ্টা করুন।',
        },
      ]);
    } finally {
      setAiLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await api.logout();
      window.location.href = '/login';
    } catch {
      window.location.href = '/login';
    }
  }

  if (loading) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-4xl mx-auto px-4 text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent mb-4"></div>
          <p className="text-secondary font-medium">সদস্য পোর্টাল লোড হচ্ছে...</p>
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
  const membershipCard = dashboard?.membership || dashboard?.hero_card || {};
  const effectiveStatus = (membershipCard?.status || profile?.status || me.membership_status || 'PENDING').toUpperCase();
  const memberIdStr = membershipCard?.membership_id || membershipCard?.member_id || profile?.membership_id || 'PGCB-PENDING';
  const circleNameBn = membershipCard?.circle_bn || membershipCard?.circle_name_bn || profile?.circle_bn || 'নির্ধারিত হয়নি';
  const validUntilStr = membershipCard?.valid_until_formatted || profile?.valid_until_formatted || 'N/A';
  const profileCompletionPct =
    dashboard?.profile_completion ?? profile?.profile_completion ?? 60;
  const completionDetails =
    dashboard?.profile_completion_details || profile?.profile_completion_details || null;
  const isVerifiedMember = effectiveStatus === 'ACTIVE';

  const navItems: Array<{ id: PortalTab; labelBn: string; labelEn: string; icon: any; badge?: number | string }> = [
    { id: 'dashboard', labelBn: 'ড্যাশবোর্ড', labelEn: 'Dashboard', icon: LayoutDashboard },
    { id: 'profile', labelBn: 'আমার প্রোফাইল', labelEn: 'My Profile', icon: User, badge: `${profileCompletionPct}%` },
    { id: 'membership', labelBn: 'সদস্যপদ ও নবায়ন', labelEn: 'Membership', icon: RefreshCw },
    { id: 'application', labelBn: 'আবেদন ট্র্যাকার', labelEn: 'Application', icon: FileCheck },
    { id: 'payments', labelBn: 'পেমেন্ট ও রশিদ', labelEn: 'Payments', icon: CreditCard, badge: payments.length || undefined },
    { id: 'documents', labelBn: 'ডকুমেন্ট সেন্টার', labelEn: 'Documents', icon: FileText, badge: docs.length || undefined },
    { id: 'digital-id', labelBn: 'ডিজিটাল আইডি', labelEn: 'Digital ID', icon: IdCard },
    { id: 'certificates', labelBn: 'সনদ ওয়ালেট', labelEn: 'Certificates', icon: Award, badge: certificates.length || undefined },
    { id: 'events', labelBn: 'ইভেন্ট নিবন্ধন', labelEn: 'Events', icon: Calendar },
    { id: 'notices', labelBn: 'সার্কুলার ও নোটিশ', labelEn: 'Notices', icon: Bookmark },
    { id: 'notifications', labelBn: 'বিজ্ঞপ্তি কেন্দ্র', labelEn: 'Notifications', icon: Bell, badge: unreadNotes.length || undefined },
    { id: 'ai-assistant', labelBn: 'এআই সহায়িকা', labelEn: 'AI Assistant', icon: Sparkles },
    { id: 'settings', labelBn: 'সেটিংস ও নিরাপত্তা', labelEn: 'Settings', icon: Settings },
  ];

  const defaultPlans: RenewalOptionItem[] = [
    {
      code: 'RENEWAL_1YR',
      label_en: '1 Year Annual Membership Renewal',
      label_bn: '১ বছর মেয়াদী বার্ষিক নবায়ন',
      years: 1,
      fee: 2000,
      currency: 'BDT',
    },
    {
      code: 'RENEWAL_2YR',
      label_en: '2 Years Extended Membership Renewal',
      label_bn: '২ বছর মেয়াদী বর্ধিত নবায়ন',
      years: 2,
      fee: 4000,
      currency: 'BDT',
    },
    {
      code: 'LIFE',
      label_en: 'Lifetime Membership Upgrade',
      label_bn: 'আজীবন সদস্যপদ আপগ্রেড',
      years: 50,
      fee: 10000,
      currency: 'BDT',
    },
  ];
  const plansList = renewalOptions.length > 0 ? renewalOptions : defaultPlans;
  const activePlanObj =
    plansList.find((p) => (p.code || p.plan_id) === selectedPlan) || plansList[0];

  const filteredUpdates = updates.filter((u) => {
    if (updateFilter === 'ALL') return true;
    if (updateFilter === 'BOOKMARKED') return Boolean(u.is_bookmarked);
    return u.content_type === updateFilter;
  });

  return (
    <section className="min-h-screen bg-background py-6 md:py-8">
      <div className="container max-w-7xl mx-auto px-4 space-y-6">
        {/* Top Toast Alert */}
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

        {/* Top Bar Header */}
        <div className="bg-card border border-border rounded-2xl p-4 md:px-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shadow-sm">
          <div className="flex items-center gap-3.5">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-900 to-slate-900 text-amber-400 flex items-center justify-center font-extrabold text-lg shadow-sm border border-amber-500/30">
              {(profile?.name_en || me.name_en || me.name_bn || 'M').slice(0, 1).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-primary/10 text-primary">
                  PGCB MEMBER PORTAL
                </span>
                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full ${
                    effectiveStatus === 'ACTIVE'
                      ? 'bg-emerald-500/15 text-emerald-600'
                      : 'bg-amber-500/15 text-amber-600'
                  }`}
                >
                  ● {effectiveStatus}
                </span>
              </div>
              <h1 className="text-lg md:text-xl font-extrabold text-foreground mt-0.5">
                স্বাগতম, {profile?.name_bn || me.name_bn || me.name_en}
              </h1>
              <p className="text-xs text-secondary">
                সদস্য আইডি: <strong className="font-mono text-foreground">{memberIdStr}</strong> · সার্কেল:{' '}
                <strong>{circleNameBn}</strong>
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={() => switchTab('notifications')}
              className="relative inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border bg-surface hover:bg-card text-xs font-semibold text-foreground transition-all"
            >
              <Bell size={15} className="text-amber-500" />
              <span>বিজ্ঞপ্তি</span>
              {unreadNotes.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold">
                  {unreadNotes.length}
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => switchTab('ai-assistant')}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30 text-xs font-bold hover:bg-amber-500/25 transition-all"
            >
              <Sparkles size={14} /> AI সহায়িকা
            </button>
            <Link
              href="/portal/id-card"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:opacity-90 transition-all shadow-sm"
            >
              <IdCard size={15} /> Digital ID
            </Link>
          </div>
        </div>

        {/* Main Portal Shell: Sidebar + Content Area */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Sidebar Navigation */}
          <aside className="lg:col-span-3 bg-card border border-border rounded-2xl p-3 shadow-sm lg:sticky lg:top-20">
            <div className="px-3 py-2 mb-1 border-b border-border flex items-center justify-between">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-secondary">
                পোর্টাল মেনু (Navigation)
              </span>
              <span className="text-[11px] font-bold text-primary">{profileCompletionPct}% প্রোফাইল</span>
            </div>

            <nav className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => switchTab(item.id)}
                    className={`flex items-center justify-between gap-2.5 px-3 py-2.5 rounded-xl text-left text-xs font-semibold transition-all shrink-0 lg:w-full ${
                      isActive
                        ? 'bg-primary text-white shadow-sm'
                        : 'text-foreground hover:bg-surface'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon size={16} className={isActive ? 'text-white' : 'text-primary'} />
                      <div>
                        <div className="leading-tight">{item.labelBn}</div>
                        <div className={`text-[10px] ${isActive ? 'text-white/80' : 'text-secondary'}`}>
                          {item.labelEn}
                        </div>
                      </div>
                    </div>
                    {item.badge !== undefined && (
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-primary/10 text-primary'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}

              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-left text-xs font-semibold text-rose-600 hover:bg-rose-500/10 transition-all shrink-0 lg:w-full lg:mt-2 lg:border-t lg:border-border lg:pt-3"
              >
                <LogOut size={16} />
                <div>
                  <div className="leading-tight">লগআউট</div>
                  <div className="text-[10px] opacity-75">Logout</div>
                </div>
              </button>
            </nav>
          </aside>

          {/* Right Content Area */}
          <div className="lg:col-span-9 space-y-6">
            {/* ==================== 1. DASHBOARD TAB ==================== */}
            {activeTab === 'dashboard' && (
              <div className="space-y-6">
                {/* Hero Status Card */}
                <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white p-6 md:p-8 shadow-lg border border-amber-500/30">
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                    <div className="md:col-span-8 space-y-4">
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
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-white/10 text-amber-300">
                          {profile?.membership_type || membershipCard?.membership_type || 'GENERAL'} MEMBER
                        </span>
                        {membershipCard?.days_until_expiry !== null &&
                          membershipCard?.days_until_expiry !== undefined && (
                            <span className="text-xs px-2.5 py-1 rounded-full bg-white/10 text-sky-300 font-semibold">
                              {membershipCard.days_until_expiry > 0
                                ? `${membershipCard.days_until_expiry} দিন বাকি`
                                : 'মেয়াদ উত্তীর্ণ'}
                            </span>
                          )}
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-widest text-slate-400 font-semibold">
                          Official Membership ID
                        </p>
                        <div className="text-2xl md:text-3xl font-mono font-extrabold text-amber-400">
                          {memberIdStr}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 text-xs">
                        <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                          <span className="text-slate-400 block">Valid Until</span>
                          <strong className="text-white text-sm">{validUntilStr}</strong>
                        </div>
                        <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                          <span className="text-slate-400 block">Grid Circle</span>
                          <strong className="text-white text-sm">{circleNameBn}</strong>
                        </div>
                        <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                          <span className="text-slate-400 block">Designation</span>
                          <strong className="text-white text-sm">
                            {profile?.designation_bn || membershipCard?.designation_bn || 'Engineer'}
                          </strong>
                        </div>
                        <div className="bg-white/5 rounded-xl p-3 border border-white/10">
                          <span className="text-slate-400 block">Digital ID</span>
                          <strong className="text-emerald-400 text-sm">
                            {dashboard?.digital_id_available || effectiveStatus === 'ACTIVE'
                              ? 'Available ✓'
                              : 'Pending'}
                          </strong>
                        </div>
                      </div>
                    </div>

                    {/* Profile Completion Meter inside Hero */}
                    <div className="md:col-span-4 bg-white/5 border border-white/10 rounded-2xl p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-200">প্রোফাইল সম্পূর্ণতা (Profile)</span>
                        <span className="text-lg font-extrabold text-amber-400">{profileCompletionPct}%</span>
                      </div>
                      <div className="w-full h-2.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-amber-400 to-emerald-400 rounded-full transition-all"
                          style={{ width: `${Math.min(100, Math.max(10, profileCompletionPct))}%` }}
                        />
                      </div>
                      {completionDetails?.items && (
                        <div className="space-y-1 pt-1">
                          {completionDetails.items.map((it: any) => (
                            <div key={it.key} className="flex items-center justify-between text-[11px]">
                              <span className={it.completed ? 'text-emerald-300' : 'text-slate-300'}>
                                {it.completed ? '✓' : '☐'} {it.label_bn}
                              </span>
                              <span className="text-slate-400">{it.weight}%</span>
                            </div>
                          ))}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => switchTab('profile')}
                        className="w-full py-2 px-3 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-colors"
                      >
                        প্রোফাইল হালনাগাদ করুন
                      </button>
                    </div>
                  </div>
                </div>

                {/* 4 Status KPI Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <button
                    type="button"
                    onClick={() => switchTab('payments')}
                    className="bg-card border border-border rounded-2xl p-4 text-left hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-secondary font-semibold">সর্বশেষ পেমেন্ট</span>
                      <CreditCard size={16} className="text-emerald-600" />
                    </div>
                    <div className="text-lg font-extrabold text-foreground">
                      {dashboard?.payment_summary?.latest_payment?.amount_formatted ||
                        dashboard?.payment_summary?.total_paid_formatted ||
                        '৳০'}
                    </div>
                    <div className="text-[11px] text-secondary mt-0.5">
                      মোট লেনদেন: {payments.length} টি
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => switchTab('application')}
                    className="bg-card border border-border rounded-2xl p-4 text-left hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-secondary font-semibold">আবেদন স্থিতি</span>
                      <FileCheck size={16} className="text-blue-600" />
                    </div>
                    <div className="text-sm font-extrabold text-foreground truncate">
                      {timeline?.status_label_bn || effectiveStatus}
                    </div>
                    <div className="text-[11px] text-secondary mt-0.5">
                      নম্বর: {timeline?.application_no || 'N/A'}
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => switchTab('certificates')}
                    className="bg-card border border-border rounded-2xl p-4 text-left hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-secondary font-semibold">সনদ ওয়ালেট</span>
                      <Award size={16} className="text-amber-600" />
                    </div>
                    <div className="text-lg font-extrabold text-foreground">{certificates.length} টি</div>
                    <div className="text-[11px] text-secondary mt-0.5">ডিজিটাল ভেরিফায়েড সনদ</div>
                  </button>

                  <button
                    type="button"
                    onClick={() => switchTab('notifications')}
                    className="bg-card border border-border rounded-2xl p-4 text-left hover:border-primary/40 transition-all shadow-sm"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-secondary font-semibold">অপঠিত বিজ্ঞপ্তি</span>
                      <Bell size={16} className="text-rose-600" />
                    </div>
                    <div className="text-lg font-extrabold text-foreground">{unreadNotes.length} টি</div>
                    <div className="text-[11px] text-secondary mt-0.5">মোট বার্তা: {notes.length} টি</div>
                  </button>
                </div>

                {/* Application Timeline Summary on Dashboard */}
                {timeline && (
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
                      <div>
                        <h2 className="text-base font-bold text-foreground">
                          সদস্যপদ আবেদন ও সক্রিয়করণ অগ্রগতি (Application Progress)
                        </h2>
                        <p className="text-xs text-secondary">
                          আবেদন নম্বর: <strong className="font-mono">{timeline.application_no}</strong> · বর্তমান ধাপ:{' '}
                          <strong className="text-primary">{timeline.status_label_bn}</strong>
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => switchTab('application')}
                        className="text-xs font-bold text-primary hover:underline inline-flex items-center gap-1"
                      >
                        বিস্তারিত দেখুন <ArrowRight size={13} />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
                      {(timeline.stages || []).map((st: any) => {
                        const done = st.status === 'COMPLETED';
                        const active = st.status === 'IN_PROGRESS' || st.status === 'ACTION_REQUIRED';
                        return (
                          <div
                            key={st.key}
                            className={`p-3 rounded-xl border text-xs ${
                              done
                                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                                : active
                                ? 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300'
                                : 'border-border bg-surface text-secondary'
                            }`}
                          >
                            <div className="font-extrabold text-sm mb-1">{st.icon} ধাপ {st.step}</div>
                            <div className="font-bold leading-snug">{st.label_bn}</div>
                            <div className="text-[10px] opacity-75">{st.label_en}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Upcoming Events & Recent Activity Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Upcoming Events */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <div className="flex items-center gap-2">
                        <Calendar size={18} className="text-primary" />
                        <h2 className="text-base font-bold text-foreground">আসন্ন ইভেন্টসমূহ (Upcoming Events)</h2>
                      </div>
                      <button
                        type="button"
                        onClick={() => switchTab('events')}
                        className="text-xs font-bold text-primary hover:underline"
                      >
                        সব দেখুন
                      </button>
                    </div>
                    <div className="space-y-3">
                      {(dashboard?.events || []).length === 0 ? (
                        <p className="text-xs text-secondary py-4 text-center">কোনো আসন্ন ইভেন্ট নেই।</p>
                      ) : (
                        (dashboard?.events || []).slice(0, 3).map((ev: any) => (
                          <div
                            key={ev.id}
                            className="p-3.5 rounded-xl border border-border bg-surface flex items-center justify-between gap-3"
                          >
                            <div>
                              <h3 className="text-xs font-bold text-foreground">{ev.title_bn}</h3>
                              <p className="text-[11px] text-secondary mt-0.5">
                                📅 {ev.event_date_formatted || 'TBA'} · 📍 {ev.location_bn || 'PGCB'}
                              </p>
                            </div>
                            {ev.is_registered ? (
                              <span className="px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-600 text-[10px] font-bold shrink-0">
                                ✓ নিবন্ধিত
                              </span>
                            ) : (
                              <Link
                                href="/events"
                                className="px-3 py-1.5 rounded-lg bg-primary text-white text-[11px] font-bold shrink-0 hover:opacity-90"
                              >
                                Register
                              </Link>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Recent Activity */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <div className="flex items-center gap-2">
                        <Activity size={18} className="text-emerald-600" />
                        <h2 className="text-base font-bold text-foreground">সাম্প্রতিক কার্যক্রম (Recent Activity)</h2>
                      </div>
                    </div>
                    <div className="space-y-3">
                      {(dashboard?.recent_activity || []).length === 0 ? (
                        <p className="text-xs text-secondary py-4 text-center">কোনো সাম্প্রতিক কার্যক্রম নেই।</p>
                      ) : (
                        (dashboard?.recent_activity || []).slice(0, 5).map((act, idx) => (
                          <div
                            key={act.id || idx}
                            className="p-3 rounded-xl border border-border bg-surface text-xs flex items-start justify-between gap-2"
                          >
                            <div>
                              <div className="font-bold text-foreground">{act.title_bn || act.title}</div>
                              {act.subtitle_bn && (
                                <div className="text-[11px] text-secondary mt-0.5">{act.subtitle_bn}</div>
                              )}
                            </div>
                            <span className="text-[10px] text-secondary shrink-0">
                              {act.relative_time_bn || act.relative_time_en || ''}
                            </span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ==================== 2. MY PROFILE TAB ==================== */}
            {activeTab === 'profile' && (
              <div className="space-y-6">
                {/* Profile Completion & Verification Banner */}
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <h2 className="text-xl font-extrabold text-foreground">আমার প্রোফাইল (Complete Member Profile)</h2>
                      <p className="text-xs text-secondary mt-1">
                        ব্যক্তিগত, পেশাগত, যোগাযোগ এবং জরুরি যোগাযোগের তথ্য হালনাগাদ করুন।
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-xs font-bold text-secondary">প্রোফাইল সম্পূর্ণতা</div>
                        <div className="text-xl font-extrabold text-primary">{profileCompletionPct}%</div>
                      </div>
                      <label className="cursor-pointer inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary/10 text-primary text-xs font-bold hover:bg-primary/20 transition-all">
                        <Upload size={14} /> ছবি পরিবর্তন
                        <input
                          type="file"
                          accept="image/*"
                          hidden
                          onChange={(e) => uploadDoc(e, 'PHOTO')}
                        />
                      </label>
                    </div>
                  </div>

                  {isVerifiedMember && (
                    <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2.5">
                      <Lock size={16} className="shrink-0 mt-0.5 text-amber-600" />
                      <div>
                        <strong>প্রোফাইল যাচাইকরণ নীতিমালা (Profile Verification Policy):</strong> আপনার সদস্যপদ সক্রিয় (ACTIVE) থাকায়{' '}
                        <strong>মোবাইল, ইমেইল, ঠিকানা, পদবি, বিভাগ ও জরুরি যোগাযোগ</strong> তাৎক্ষণিকভাবে সম্পাদনা করা যাবে। তবে{' '}
                        <strong>নাম, জন্ম তারিখ, এনআইডি এবং সদস্য আইডি</strong> পরিবর্তন করলে তা স্বয়ংক্রিয়ভাবে যাচাইকরণের আবেদনে (Verification Request) যুক্ত হবে।
                      </div>
                    </div>
                  )}
                </div>

                {/* Complete Editable Profile Form */}
                <form onSubmit={saveProfile} className="space-y-6">
                  {/* Card 1: Personal Information */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2.5 border-b border-border pb-3">
                      <User size={18} className="text-primary" />
                      <h3 className="text-base font-bold text-foreground">
                        ১. ব্যক্তিগত তথ্য (Personal Information)
                      </h3>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          বাংলা নাম (Name Bangla) {isVerifiedMember && <span className="text-amber-600 text-[10px]">[যাচাই সাপেক্ষ]</span>}
                        </label>
                        <input
                          type="text"
                          required
                          value={profile?.name_bn ?? ''}
                          onChange={(e) => setProfile({ ...profile, name_bn: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          ইংরেজি নাম (Name English) {isVerifiedMember && <span className="text-amber-600 text-[10px]">[যাচাই সাপেক্ষ]</span>}
                        </label>
                        <input
                          type="text"
                          value={profile?.name_en ?? ''}
                          onChange={(e) => setProfile({ ...profile, name_en: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          পিতার নাম (Father&apos;s Name)
                        </label>
                        <input
                          type="text"
                          value={profile?.father_name ?? ''}
                          onChange={(e) => setProfile({ ...profile, father_name: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          মাতার নাম (Mother&apos;s Name)
                        </label>
                        <input
                          type="text"
                          value={profile?.mother_name ?? ''}
                          onChange={(e) => setProfile({ ...profile, mother_name: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          জন্ম তারিখ (Date of Birth) {isVerifiedMember && <span className="text-amber-600 text-[10px]">[যাচাই সাপেক্ষ]</span>}
                        </label>
                        <input
                          type="date"
                          value={
                            profile?.date_of_birth
                              ? String(profile.date_of_birth).slice(0, 10)
                              : ''
                          }
                          onChange={(e) => setProfile({ ...profile, date_of_birth: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          লিঙ্গ (Gender)
                        </label>
                        <select
                          value={profile?.gender ?? ''}
                          onChange={(e) => setProfile({ ...profile, gender: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        >
                          <option value="">নির্বাচন করুন</option>
                          <option value="MALE">পুরুষ (Male)</option>
                          <option value="FEMALE">নারী (Female)</option>
                          <option value="OTHER">অন্যান্য (Other)</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          রক্তের গ্রুপ (Blood Group)
                        </label>
                        <select
                          value={profile?.blood_group ?? ''}
                          onChange={(e) => setProfile({ ...profile, blood_group: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        >
                          <option value="">নির্বাচন করুন</option>
                          {['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'].map((bg) => (
                            <option key={bg} value={bg}>
                              {bg}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="sm:col-span-2">
                        <label className="block text-xs font-semibold text-foreground mb-1">
                          জাতীয় পরিচয়পত্র / পাসপোর্ট নম্বর (NID / Passport) {isVerifiedMember && <span className="text-amber-600 text-[10px]">[যাচাই সাপেক্ষ]</span>}
                        </label>
                        <input
                          type="text"
                          value={profile?.nid_number ?? ''}
                          onChange={(e) => setProfile({ ...profile, nid_number: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Professional Information */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2.5 border-b border-border pb-3">
                      <Briefcase size={18} className="text-emerald-600" />
                      <h3 className="text-base font-bold text-foreground">
                        ২. পেশাগত তথ্য (Professional Information)
                      </h3>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">পদবি (বাংলা)</label>
                        <input
                          type="text"
                          value={profile?.designation_bn ?? ''}
                          onChange={(e) => setProfile({ ...profile, designation_bn: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">Designation (English)</label>
                        <input
                          type="text"
                          value={profile?.designation_en ?? ''}
                          onChange={(e) => setProfile({ ...profile, designation_en: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">কর্মকর্তা আইডি (Employee ID)</label>
                        <input
                          type="text"
                          value={profile?.employee_id ?? ''}
                          onChange={(e) => setProfile({ ...profile, employee_id: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">প্রতিষ্ঠান (Organization)</label>
                        <input
                          type="text"
                          value={profile?.organization ?? 'Power Grid Bangladesh PLC (PGCB)'}
                          onChange={(e) => setProfile({ ...profile, organization: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">বিভাগ / দপ্তর (Department)</label>
                        <input
                          type="text"
                          value={profile?.department ?? ''}
                          onChange={(e) => setProfile({ ...profile, department: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">পেশা (Profession)</label>
                        <input
                          type="text"
                          value={profile?.profession ?? 'Diploma Engineer'}
                          onChange={(e) => setProfile({ ...profile, profession: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">শিক্ষাগত যোগ্যতা (Academic Qualification)</label>
                        <input
                          type="text"
                          placeholder="Diploma in Electrical Engineering"
                          value={profile?.academic_qualification ?? ''}
                          onChange={(e) => setProfile({ ...profile, academic_qualification: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">পেশাগত সনদ (Professional Qualification)</label>
                        <input
                          type="text"
                          placeholder="IDEB / IEB Membership"
                          value={profile?.professional_qualification ?? ''}
                          onChange={(e) => setProfile({ ...profile, professional_qualification: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">অভিজ্ঞতা (Years of Experience)</label>
                        <input
                          type="number"
                          min={0}
                          max={60}
                          value={profile?.years_of_experience ?? ''}
                          onChange={(e) =>
                            setProfile({
                              ...profile,
                              years_of_experience: e.target.value ? Number(e.target.value) : null,
                            })
                          }
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div className="sm:col-span-2">
                        <label className="block text-xs font-semibold text-foreground mb-1">ডিপ্লোমা প্রতিষ্ঠান (Diploma Institution)</label>
                        <input
                          type="text"
                          value={profile?.diploma_institution ?? ''}
                          onChange={(e) => setProfile({ ...profile, diploma_institution: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">পাসের বছর (Graduation Year)</label>
                        <input
                          type="number"
                          value={profile?.graduation_year ?? ''}
                          onChange={(e) =>
                            setProfile({
                              ...profile,
                              graduation_year: e.target.value ? Number(e.target.value) : null,
                            })
                          }
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Contact Information */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2.5 border-b border-border pb-3">
                      <Phone size={18} className="text-blue-600" />
                      <h3 className="text-base font-bold text-foreground">
                        ৩. যোগাযোগের তথ্য (Contact Information)
                      </h3>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">ইমেইল (Email)</label>
                        <input
                          type="email"
                          value={profile?.email ?? ''}
                          onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">মোবাইল নম্বর (Mobile)</label>
                        <input
                          type="text"
                          value={profile?.phone ?? ''}
                          onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">বিকল্প ফোন (Alternate Phone)</label>
                        <input
                          type="text"
                          value={profile?.alternate_phone ?? ''}
                          onChange={(e) => setProfile({ ...profile, alternate_phone: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">জেলা (District)</label>
                        <input
                          type="text"
                          value={profile?.district ?? ''}
                          onChange={(e) => setProfile({ ...profile, district: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>

                      <div className="sm:col-span-2">
                        <label className="block text-xs font-semibold text-foreground mb-1">গ্রিড সার্কেল (Grid Circle)</label>
                        <select
                          value={profile?.circle_id ?? ''}
                          onChange={(e) =>
                            setProfile({ ...profile, circle_id: e.target.value ? Number(e.target.value) : null })
                          }
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        >
                          <option value="">গ্রিড সার্কেল নির্বাচন করুন</option>
                          {circles.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name_bn} ({c.name_en})
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="sm:col-span-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-xs font-semibold text-foreground mb-1">বর্তমান ঠিকানা (Present Address)</label>
                          <textarea
                            rows={2}
                            value={profile?.current_address ?? ''}
                            onChange={(e) => setProfile({ ...profile, current_address: e.target.value })}
                            className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-foreground mb-1">স্থায়ী ঠিকানা (Permanent Address)</label>
                          <textarea
                            rows={2}
                            value={profile?.permanent_address ?? ''}
                            onChange={(e) => setProfile({ ...profile, permanent_address: e.target.value })}
                            className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Card 4: Emergency Contact */}
                  <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center gap-2.5 border-b border-border pb-3">
                      <HeartHandshake size={18} className="text-rose-600" />
                      <h3 className="text-base font-bold text-foreground">
                        ৪. জরুরি যোগাযোগ (Emergency Contact)
                      </h3>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">নাম (Name)</label>
                        <input
                          type="text"
                          value={profile?.emergency_contact_name ?? ''}
                          onChange={(e) => setProfile({ ...profile, emergency_contact_name: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">সম্পর্ক (Relationship)</label>
                        <input
                          type="text"
                          placeholder="Spouse / Brother / Parent"
                          value={profile?.emergency_contact_relationship ?? ''}
                          onChange={(e) =>
                            setProfile({ ...profile, emergency_contact_relationship: e.target.value })
                          }
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">ফোন (Phone)</label>
                        <input
                          type="text"
                          value={profile?.emergency_contact_phone ?? ''}
                          onChange={(e) => setProfile({ ...profile, emergency_contact_phone: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-foreground mb-1">ঠিকানা (Address)</label>
                        <input
                          type="text"
                          value={profile?.emergency_contact_address ?? ''}
                          onChange={(e) => setProfile({ ...profile, emergency_contact_address: e.target.value })}
                          className="w-full px-3.5 py-2 rounded-xl border border-border bg-background text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={saving}
                    className="w-full py-3 px-6 rounded-xl bg-primary text-white font-bold text-sm hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
                  >
                    {saving ? 'সংরক্ষণ হচ্ছে...' : 'সম্পূর্ণ প্রোফাইল তথ্য সংরক্ষণ করুন (Save Profile)'}
                  </button>
                </form>

                {/* Sensitive Field Change Request Section */}
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 border-b border-border pb-3">
                    <Lock size={18} className="text-amber-600" />
                    <div>
                      <h3 className="text-base font-bold text-foreground">
                        সংবেদনশীল তথ্য সংশোধনের আবেদন (Sensitive Field Verification Request)
                      </h3>
                      <p className="text-xs text-secondary">
                        নাম, জন্ম তারিখ, এনআইডি, সদস্য আইডি অথবা সনদপত্রের তথ্য সংশোধনের জন্য সুনির্দিষ্ট কারণ উল্লেখ করে আবেদন করুন।
                      </p>
                    </div>
                  </div>

                  <form onSubmit={handleSubmitChangeRequest} className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <select
                      value={changeField}
                      onChange={(e) => setChangeField(e.target.value)}
                      className="px-3.5 py-2 rounded-xl border border-border bg-background text-xs font-semibold"
                    >
                      <option value="name_bn">নাম (বাংলা) — Name Bangla</option>
                      <option value="name_en">নাম (ইংরেজি) — Name English</option>
                      <option value="date_of_birth">জন্ম তারিখ — Date of Birth</option>
                      <option value="nid_number">জাতীয় পরিচয়পত্র — NID Number</option>
                      <option value="membership_id">সদস্য আইডি — Membership ID</option>
                      <option value="certificate_info">সনদপত্রের তথ্য — Certificate Info</option>
                    </select>
                    <input
                      type="text"
                      required
                      placeholder="সংশোধিত নতুন মান লিখুন..."
                      value={changeValue}
                      onChange={(e) => setChangeValue(e.target.value)}
                      className="px-3.5 py-2 rounded-xl border border-border bg-background text-xs"
                    />
                    <input
                      type="text"
                      placeholder="সংশোধনের কারণ (ঐচ্ছিক)..."
                      value={changeReason}
                      onChange={(e) => setChangeReason(e.target.value)}
                      className="px-3.5 py-2 rounded-xl border border-border bg-background text-xs"
                    />
                    <button
                      type="submit"
                      disabled={submittingChange}
                      className="px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-colors"
                    >
                      {submittingChange ? 'জমা হচ্ছে...' : 'যাচাইকরণের আবেদন করুন'}
                    </button>
                  </form>

                  {changeRequests.length > 0 && (
                    <div className="space-y-2 pt-2">
                      <div className="text-xs font-bold text-secondary">জমাকৃত সংশোধন আবেদনসমূহ:</div>
                      {changeRequests.map((cr) => (
                        <div
                          key={cr.id}
                          className="p-3 rounded-xl border border-border bg-surface text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                        >
                          <div>
                            <strong className="text-foreground">{cr.field_label_bn || cr.field_name}:</strong>{' '}
                            <span className="line-through text-secondary mr-1">{cr.current_value || 'N/A'}</span> →{' '}
                            <strong className="text-primary">{cr.requested_value}</strong>
                            {cr.reason && <span className="text-secondary ml-2">({cr.reason})</span>}
                          </div>
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              cr.status === 'APPROVED'
                                ? 'bg-emerald-500/15 text-emerald-600'
                                : cr.status === 'REJECTED'
                                ? 'bg-rose-500/15 text-rose-600'
                                : 'bg-amber-500/15 text-amber-600'
                            }`}
                          >
                            {cr.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ==================== 3. MEMBERSHIP & RENEWAL TAB ==================== */}
            {activeTab === 'membership' && (
              <div className="space-y-6">
                {/* Membership Details Card */}
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <Shield size={20} />
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-foreground">সদস্যপদ বিবরণ (Membership Details)</h2>
                        <p className="text-xs text-secondary">আপনার প্রাতিষ্ঠানিক সদস্যপদ ও ভোটাধিকার স্থিতি</p>
                      </div>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/15 text-emerald-600">
                      ● {effectiveStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-xs">
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Membership ID</span>
                      <strong className="text-foreground font-mono text-sm">{memberIdStr}</strong>
                    </div>
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Membership Type</span>
                      <strong className="text-foreground text-sm">
                        {profile?.membership_type || 'GENERAL'}
                      </strong>
                    </div>
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Grid Circle</span>
                      <strong className="text-foreground text-sm">{circleNameBn}</strong>
                    </div>
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Issue Date</span>
                      <strong className="text-foreground text-sm">
                        {profile?.issue_date
                          ? new Date(profile.issue_date).toLocaleDateString('bn-BD')
                          : 'N/A'}
                      </strong>
                    </div>
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Expiry Date</span>
                      <strong className="text-foreground text-sm">{validUntilStr}</strong>
                    </div>
                    <div className="p-3.5 rounded-xl bg-surface border border-border">
                      <span className="text-secondary block">Voting Eligibility</span>
                      <strong className="text-emerald-600 text-sm">
                        {effectiveStatus === 'ACTIVE' ? 'Eligible ✓' : 'Not Active'}
                      </strong>
                    </div>
                  </div>
                </div>

                {/* Multi-Step Renewal Workflow */}
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600">
                        <RefreshCw size={20} />
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-foreground">
                          সদস্যপদ নবায়ন ওয়ার্কফ্লো (Membership Renewal Workflow)
                        </h2>
                        <p className="text-xs text-secondary">
                          মেয়াদ নির্বাচন → তথ্য যাচাই → পেমেন্ট → রশিদ ও নতুন মেয়াদ
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs font-bold">
                      <span className={`px-2.5 py-1 rounded-lg ${renewalStep === 1 ? 'bg-primary text-white' : 'bg-surface text-secondary'}`}>
                        ১. মেয়াদ নির্বাচন
                      </span>
                      <span>→</span>
                      <span className={`px-2.5 py-1 rounded-lg ${renewalStep === 2 ? 'bg-primary text-white' : 'bg-surface text-secondary'}`}>
                        ২. পর্যালোচনা ও পেমেন্ট
                      </span>
                      <span>→</span>
                      <span className={`px-2.5 py-1 rounded-lg ${renewalStep === 3 ? 'bg-emerald-600 text-white' : 'bg-surface text-secondary'}`}>
                        ৩. রশিদ
                      </span>
                    </div>
                  </div>

                  {renewalStep === 1 && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        {plansList.map((plan) => {
                          const pCode = plan.code || plan.plan_id || 'RENEWAL_1YR';
                          const active = selectedPlan === pCode;
                          const feeVal = plan.fee ?? plan.amount ?? plan.amount_bdt ?? 2000;
                          return (
                            <button
                              key={pCode}
                              type="button"
                              onClick={() => setSelectedPlan(pCode)}
                              className={`p-5 rounded-2xl border text-left transition-all ${
                                active
                                  ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                                  : 'border-border bg-surface hover:border-primary/40'
                              }`}
                            >
                              <div className="text-sm font-extrabold text-foreground">
                                {plan.title_bn || plan.label_bn}
                              </div>
                              <div className="text-xs text-secondary mt-0.5">
                                {plan.title_en || plan.label_en}
                              </div>
                              <div className="text-2xl font-extrabold text-primary mt-3">
                                ৳{Number(feeVal).toLocaleString()}
                              </div>
                              {plan.projected_validity_formatted && (
                                <div className="text-[11px] text-emerald-600 font-semibold mt-2">
                                  নতুন মেয়াদ: {plan.projected_validity_formatted}
                                </div>
                              )}
                            </button>
                          );
                        })}
                      </div>

                      <div className="flex justify-end">
                        <button
                          type="button"
                          onClick={() => setRenewalStep(2)}
                          className="px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90"
                        >
                          পরবর্তী ধাপ: তথ্য যাচাই করুন →
                        </button>
                      </div>
                    </div>
                  )}

                  {renewalStep === 2 && (
                    <div className="space-y-4">
                      <div className="p-4 rounded-2xl bg-surface border border-border grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                        <div>
                          <span className="text-secondary block">সদস্যের নাম ও আইডি</span>
                          <strong className="text-foreground text-sm">
                            {profile?.name_bn || me.name_bn} ({memberIdStr})
                          </strong>
                        </div>
                        <div>
                          <span className="text-secondary block">নির্বাচিত নবায়ন প্ল্যান</span>
                          <strong className="text-primary text-sm">
                            {activePlanObj?.title_bn || activePlanObj?.label_bn} (৳
                            {(activePlanObj?.fee ?? activePlanObj?.amount ?? 2000).toLocaleString()})
                          </strong>
                        </div>
                        <div>
                          <span className="text-secondary block">পেমেন্ট গেটওয়ে (Payment Method)</span>
                          <select
                            value={renewalProvider}
                            onChange={(e) => setRenewalProvider(e.target.value)}
                            className="mt-1 w-full px-3 py-1.5 rounded-lg border border-border bg-background text-xs font-bold"
                          >
                            <option value="SSLCOMMERZ">SSLCommerz (Card / Mobile Banking)</option>
                            <option value="BKASH">bKash</option>
                            <option value="NAGAD">Nagad</option>
                          </select>
                        </div>
                        <div>
                          <span className="text-secondary block">প্রস্তাবিত নতুন মেয়াদ</span>
                          <strong className="text-emerald-600 text-sm">
                            {activePlanObj?.projected_validity_formatted || 'নবায়ন সম্পন্ন হওয়ার পর যুক্ত হবে'}
                          </strong>
                        </div>
                      </div>

                      <div className="flex items-center justify-between gap-3">
                        <button
                          type="button"
                          onClick={() => setRenewalStep(1)}
                          className="px-4 py-2.5 rounded-xl border border-border bg-surface text-xs font-bold"
                        >
                          ← মেয়াদ পরিবর্তন করুন
                        </button>
                        <button
                          type="button"
                          onClick={handleInitiateRenewal}
                          disabled={renewing}
                          className="px-6 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 disabled:opacity-50"
                        >
                          {renewing ? 'লেনদেন তৈরি হচ্ছে...' : 'পেমেন্ট ও নবায়ন নিশ্চিত করুন'}
                        </button>
                      </div>
                    </div>
                  )}

                  {renewalStep === 3 && lastRenewalTx && (
                    <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-3 text-xs">
                      <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-extrabold text-sm">
                        <CheckCircle size={18} /> নবায়ন লেনদেন সফলভাবে ইনিশিয়েট হয়েছে!
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div>
                          <span className="text-secondary block">Transaction Ref</span>
                          <strong className="font-mono">{lastRenewalTx.transaction_id}</strong>
                        </div>
                        <div>
                          <span className="text-secondary block">Amount</span>
                          <strong>৳{lastRenewalTx.amount}</strong>
                        </div>
                        <div>
                          <span className="text-secondary block">Provider</span>
                          <strong>{lastRenewalTx.provider}</strong>
                        </div>
                        <div>
                          <span className="text-secondary block">Projected Expiry</span>
                          <strong>{lastRenewalTx.projected_validity_formatted || lastRenewalTx.projected_validity_date}</strong>
                        </div>
                      </div>
                      <div className="flex gap-3 pt-2">
                        <button
                          type="button"
                          onClick={() => setRenewalStep(1)}
                          className="px-4 py-2 rounded-xl bg-primary text-white font-bold"
                        >
                          সম্পন্ন
                        </button>
                        <button
                          type="button"
                          onClick={() => switchTab('payments')}
                          className="px-4 py-2 rounded-xl border border-border bg-card font-bold"
                        >
                          পেমেন্ট সেন্টারে দেখুন
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Renewal History */}
                  {renewals.length > 0 && (
                    <div className="pt-4 border-t border-border space-y-2">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
                        নবায়ন ইতিহাস (Renewal History)
                      </h3>
                      {renewals.map((r) => (
                        <div
                          key={r.id}
                          className="p-3 rounded-xl bg-surface border border-border text-xs flex items-center justify-between"
                        >
                          <div>
                            <strong className="text-foreground">
                              নতুন মেয়াদ: {r.new_validity_formatted || r.new_validity_date}
                            </strong>
                            <span className="text-secondary ml-2">({r.amount_formatted || `৳${r.amount}`})</span>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                            {r.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ==================== 4. APPLICATION TRACKER TAB ==================== */}
            {activeTab === 'application' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">
                      সদস্য আবেদন ট্র্যাকার (Application Status Timeline)
                    </h2>
                    <p className="text-xs text-secondary">
                      আবেদন নম্বর: <strong className="font-mono">{timeline?.application_no || 'PGCB-APP'}</strong>
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-primary/10 text-primary">
                    {timeline?.status_label_bn || application?.status || effectiveStatus}
                  </span>
                </div>

                {/* 6-Stage Visual Timeline */}
                <div className="space-y-3">
                  {(timeline?.stages || []).map((st: any) => {
                    const done = st.status === 'COMPLETED';
                    const active = st.status === 'IN_PROGRESS' || st.status === 'ACTION_REQUIRED';
                    return (
                      <div
                        key={st.key}
                        className={`p-4 rounded-2xl border flex items-center justify-between gap-4 ${
                          done
                            ? 'border-emerald-500/30 bg-emerald-500/5'
                            : active
                            ? 'border-amber-500/40 bg-amber-500/10'
                            : 'border-border bg-surface'
                        }`}
                      >
                        <div className="flex items-center gap-3.5">
                          <div
                            className={`h-9 w-9 rounded-xl flex items-center justify-center font-extrabold text-sm ${
                              done
                                ? 'bg-emerald-500 text-white'
                                : active
                                ? 'bg-amber-500 text-slate-950'
                                : 'bg-border text-secondary'
                            }`}
                          >
                            {st.icon}
                          </div>
                          <div>
                            <div className="text-sm font-bold text-foreground">
                              ধাপ {st.step}: {st.label_bn}
                            </div>
                            <div className="text-xs text-secondary">{st.label_en}</div>
                          </div>
                        </div>
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold ${
                            done
                              ? 'bg-emerald-500/15 text-emerald-600'
                              : active
                              ? 'bg-amber-500/20 text-amber-700'
                              : 'bg-border/60 text-secondary'
                          }`}
                        >
                          {st.status}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Required Actions & Reviewer Notes */}
                {timeline?.reviewer_notes && (
                  <div className="p-4 rounded-xl bg-surface border border-border text-xs">
                    <strong className="text-foreground block mb-1">পর্যালোচকের মন্তব্য (Reviewer Notes):</strong>
                    <p className="text-secondary">{timeline.reviewer_notes}</p>
                  </div>
                )}

                {timeline?.required_actions && timeline.required_actions.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-xs font-bold text-amber-600">প্রয়োজনীয় পদক্ষেপ (Required Actions):</div>
                    {timeline.required_actions.map((act: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-800 dark:text-amber-300 flex items-center justify-between gap-3"
                      >
                        <span>⚠ {act.message_bn}</span>
                        {act.code === 'UPLOAD_DOCUMENTS' || act.code === 'REPLACE_DOCUMENT' ? (
                          <button
                            type="button"
                            onClick={() => switchTab('documents')}
                            className="px-3 py-1 rounded-lg bg-amber-500 text-slate-950 font-bold shrink-0"
                          >
                            ডকুমেন্ট আপলোড
                          </button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}

                {effectiveStatus !== 'ACTIVE' && (
                  <div className="flex flex-wrap gap-3 pt-2">
                    <button
                      type="button"
                      onClick={handleSaveDraftApplication}
                      className="px-4 py-2.5 rounded-xl border border-border bg-surface text-xs font-bold hover:bg-card"
                    >
                      খসড়া হিসেবে সংরক্ষণ (Save Draft)
                    </button>
                    <button
                      type="button"
                      onClick={submitApplication}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700"
                    >
                      চূড়ান্ত আবেদন জমা দিন (Submit Application)
                    </button>
                    <button
                      type="button"
                      onClick={handleCancelApplication}
                      className="px-4 py-2.5 rounded-xl bg-rose-500/10 text-rose-600 text-xs font-bold hover:bg-rose-500/20"
                    >
                      আবেদন বাতিল করুন
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* ==================== 5. PAYMENTS TAB ==================== */}
            {activeTab === 'payments' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">পেমেন্ট ও রশিদ কেন্দ্র (Payment Center)</h2>
                    <p className="text-xs text-secondary">
                      সদস্যপদ ফি, নবায়ন ফি এবং ইভেন্ট নিবন্ধন লেনদেনের সম্পূর্ণ ইতিহাস ও রশিদ ডাউনলোড
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => switchTab('membership')}
                    className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold"
                  >
                    + নতুন নবায়ন পেমেন্ট
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 rounded-xl bg-surface border border-border">
                    <span className="text-secondary block">মোট পরিশোধিত (Total Paid)</span>
                    <strong className="text-xl font-extrabold text-emerald-600">
                      {dashboard?.payment_summary?.total_paid_formatted || '৳০'}
                    </strong>
                  </div>
                  <div className="p-4 rounded-xl bg-surface border border-border">
                    <span className="text-secondary block">সফল লেনদেন (Paid Transactions)</span>
                    <strong className="text-xl font-extrabold text-foreground">
                      {dashboard?.payment_summary?.paid_count ?? payments.filter((p) => p.status === 'PAID').length} টি
                    </strong>
                  </div>
                  <div className="p-4 rounded-xl bg-surface border border-border">
                    <span className="text-secondary block">অপেক্ষমাণ পেমেন্ট (Pending)</span>
                    <strong className="text-xl font-extrabold text-amber-600">
                      {dashboard?.payment_summary?.pending_count ?? payments.filter((p) => p.status === 'PENDING').length} টি
                    </strong>
                  </div>
                </div>

                <div className="space-y-3">
                  {payments.length === 0 ? (
                    <p className="text-xs text-secondary py-8 text-center">কোনো পেমেন্ট রেকর্ড পাওয়া যায়নি।</p>
                  ) : (
                    payments.map((p) => (
                      <div
                        key={p.id}
                        className="p-4 rounded-xl border border-border bg-surface text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <strong className="text-sm font-bold text-foreground">
                              {p.purpose_label || p.purpose}
                            </strong>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                                p.status === 'PAID'
                                  ? 'bg-emerald-500/15 text-emerald-600'
                                  : 'bg-amber-500/15 text-amber-600'
                              }`}
                            >
                              {p.status}
                            </span>
                          </div>
                          <div className="text-secondary font-mono text-[11px]">
                            Ref: {p.transaction_ref || p.id} · Method: {p.provider} · Receipt:{' '}
                            <strong>{p.receipt_no || `PGCB-RCP-2026-${String(p.id).padStart(6, '0')}`}</strong>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <span className="text-base font-extrabold text-emerald-600">
                            {p.amount_formatted || `৳${p.amount}`}
                          </span>
                          {p.status === 'PAID' && (
                            <a
                              href={api.getPaymentReceiptPdfUrl(p.id)}
                              target="_blank"
                              download
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:opacity-90"
                            >
                              <Download size={13} /> রশিদ (PDF)
                            </a>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* ==================== 6. DOCUMENT CENTER TAB ==================== */}
            {activeTab === 'documents' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">ডকুমেন্ট সেন্টার (Member Document Center)</h2>
                    <p className="text-xs text-secondary">
                      এনআইডি, শিক্ষাগত সনদ, পেশাগত সনদ, অভিজ্ঞতা সনদ এবং পাসপোর্ট ছবি আপলোড ও যাচাই স্ট্যাটাস
                    </p>
                  </div>
                </div>

                {uploading && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 text-xs flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-amber-600 border-t-transparent"></div>
                    নথি আপলোড ও নিরাপত্তা যাচাই হচ্ছে...
                  </div>
                )}

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  {[
                    { type: 'NID', label: 'এনআইডি / পাসপোর্ট', sub: 'NID / Passport' },
                    { type: 'ACADEMIC_CERTIFICATE', label: 'ডিপ্লোমা সনদ', sub: 'Academic Cert' },
                    { type: 'PROFESSIONAL_CERTIFICATE', label: 'পেশাগত সনদ', sub: 'Professional Cert' },
                    { type: 'EXPERIENCE_CERTIFICATE', label: 'অভিজ্ঞতা সনদ', sub: 'Experience Cert' },
                    { type: 'PHOTO', label: 'প্রোফাইল ছবি', sub: 'Profile Photo' },
                    { type: 'OTHER', label: 'অন্যান্য নথি', sub: 'Supporting Doc' },
                  ].map((docItem) => (
                    <label
                      key={docItem.type}
                      className="flex flex-col items-center justify-center p-4 rounded-xl border border-dashed border-border bg-surface hover:border-primary cursor-pointer text-center transition-all group"
                    >
                      <Upload size={18} className="text-secondary group-hover:text-primary mb-1.5" />
                      <span className="text-xs font-bold text-foreground">{docItem.label}</span>
                      <span className="text-[10px] text-secondary">{docItem.sub}</span>
                      <input
                        type="file"
                        accept={docItem.type === 'PHOTO' ? 'image/*' : 'image/*,application/pdf'}
                        hidden
                        onChange={(e) => uploadDoc(e, docItem.type)}
                      />
                    </label>
                  ))}
                </div>

                <div className="space-y-2.5">
                  {docs.length === 0 ? (
                    <p className="text-xs text-secondary text-center py-8">এখনো কোনো নথি আপলোড করা হয়নি।</p>
                  ) : (
                    docs.map((d) => (
                      <div
                        key={d.id}
                        className="p-3.5 rounded-xl border border-border bg-surface text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-bold text-[10px]">
                              {d.document_type}
                            </span>
                            <strong className="text-foreground">{d.filename}</strong>
                          </div>
                          {d.reviewer_note && (
                            <p className="text-[11px] text-rose-600 mt-1">নোট: {d.reviewer_note}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                              d.review_status === 'APPROVED' || d.review_status === 'APPROVE'
                                ? 'bg-emerald-500/15 text-emerald-600'
                                : d.review_status === 'REJECTED' || d.review_status === 'REPLACEMENT_REQUIRED'
                                ? 'bg-rose-500/15 text-rose-600'
                                : 'bg-amber-500/15 text-amber-600'
                            }`}
                          >
                            {d.review_status}
                          </span>
                          <a
                            href={`${API_BASE_URL}/api/v1/member/documents/${d.id}/download`}
                            target="_blank"
                            className="px-2.5 py-1 rounded-lg border border-border bg-card text-foreground font-semibold hover:bg-surface inline-flex items-center gap-1"
                          >
                            <Download size={12} /> Download
                          </a>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* ==================== 7. DIGITAL ID TAB ==================== */}
            {activeTab === 'digital-id' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">ডিজিটাল পরিচয়পত্র (Official Digital ID Card)</h2>
                    <p className="text-xs text-secondary">
                      কিউআর কোড ভেরিফায়েড প্রাতিষ্ঠানিক ডিজিটাল আইডি কার্ড (PNG ও প্রিন্ট-রেডি PDF)
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={api.getDigitalCardUrl()}
                      target="_blank"
                      download
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary text-white text-xs font-bold"
                    >
                      <Download size={14} /> Download PNG
                    </a>
                    <a
                      href={api.getDigitalCardPdfUrl()}
                      target="_blank"
                      download
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-border bg-surface text-foreground text-xs font-bold"
                    >
                      <Download size={14} /> Download PDF
                    </a>
                    <Link
                      href="/portal/id-card"
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold"
                    >
                      <Eye size={14} /> Full Screen View
                    </Link>
                  </div>
                </div>

                {/* Live Digital ID Visual Preview */}
                <div className="max-w-lg mx-auto rounded-3xl bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 text-white p-6 shadow-xl border border-amber-500/40 space-y-4">
                  <div className="flex items-center justify-between border-b border-white/15 pb-3">
                    <div>
                      <div className="text-[10px] uppercase tracking-widest text-amber-400 font-extrabold">
                        PGCB DIPLOMA ENGINEERS ASSOCIATION
                      </div>
                      <div className="text-sm font-bold">প্রাতিষ্ঠানিক সদস্য পরিচয়পত্র (Digital Member ID)</div>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500 text-white">
                      {effectiveStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-4 items-center">
                    <div className="col-span-2 space-y-1.5 text-xs">
                      <div>
                        <span className="text-slate-400 block text-[10px]">Name</span>
                        <strong className="text-base font-extrabold text-white">
                          {profile?.name_bn || me.name_bn}
                        </strong>
                        <div className="text-slate-300 text-[11px]">{profile?.name_en || me.name_en}</div>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px]">Designation & Circle</span>
                        <strong className="text-white">{profile?.designation_bn || 'প্রকৌশলী'}</strong> ·{' '}
                        <span className="text-amber-300">{circleNameBn}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <div>
                          <span className="text-slate-400 block text-[10px]">Member ID</span>
                          <strong className="font-mono text-amber-400">{memberIdStr}</strong>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px]">Valid Until</span>
                          <strong className="text-white">{validUntilStr}</strong>
                        </div>
                      </div>
                    </div>
                    <div className="col-span-1 flex flex-col items-center justify-center bg-white/10 rounded-2xl p-3 border border-white/15 text-center">
                      <IdCard size={36} className="text-amber-400 mb-1" />
                      <span className="text-[10px] font-bold text-slate-200">QR Verified</span>
                      <Link
                        href={`/verify?member=${encodeURIComponent(memberIdStr)}`}
                        className="text-[10px] text-amber-300 underline mt-1"
                      >
                        পাবলিক যাচাই লিংক
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ==================== 8. CERTIFICATES TAB ==================== */}
            {activeTab === 'certificates' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-6">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">সনদপত্র ওয়ালেট (Member Certificates)</h2>
                    <p className="text-xs text-secondary">
                      সদস্যপদ সনদ, ইভেন্ট অংশগ্রহণ সনদ, প্রশিক্ষণ এবং কমিটি সনদসমূহ
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-700">
                    {certificates.length} টি সনদ
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {certificates.length === 0 ? (
                    <p className="text-xs text-secondary col-span-2 py-8 text-center">
                      আপনার ওয়ালেটে এখনো কোনো ইস্যুকৃত সনদ নেই।
                    </p>
                  ) : (
                    certificates.map((cert) => (
                      <div
                        key={cert.id}
                        className="p-5 rounded-2xl border border-border bg-surface space-y-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <span className="text-[10px] font-extrabold uppercase tracking-wider text-primary">
                              {cert.certificate_type}
                            </span>
                            <h3 className="text-sm font-bold text-foreground mt-0.5">
                              {cert.title_bn || cert.title_en}
                            </h3>
                            <p className="text-xs font-mono text-secondary mt-0.5">
                              ID: {cert.certificate_no}
                            </p>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600">
                            {cert.status}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-2 pt-2">
                          <a
                            href={api.getCertificatePngUrl(cert.certificate_no)}
                            target="_blank"
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-semibold"
                          >
                            <ExternalLink size={12} /> View PNG
                          </a>
                          <a
                            href={api.getCertificatePdfUrl(cert.certificate_no)}
                            target="_blank"
                            download
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border bg-card text-foreground text-xs font-semibold"
                          >
                            <Download size={12} /> Download PDF
                          </a>
                          <Link
                            href={`/verify?certificate=${encodeURIComponent(cert.certificate_no)}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-700 text-xs font-semibold"
                          >
                            Verify Link
                          </Link>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* ==================== 9. EVENTS TAB ==================== */}
            {activeTab === 'events' && (
              <div className="space-y-6">
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-4">
                    <div>
                      <h2 className="text-lg font-bold text-foreground">আমার ইভেন্ট নিবন্ধন ও টিকিট (My Events)</h2>
                      <p className="text-xs text-secondary">নিবন্ধিত ইভেন্ট টিকিট, উপস্থিতি স্ট্যাটাস ও আসন্ন ইভেন্টসমূহ</p>
                    </div>
                    <Link
                      href="/events"
                      className="px-3.5 py-2 rounded-xl bg-primary text-white text-xs font-bold"
                    >
                      সকল ইভেন্ট দেখুন
                    </Link>
                  </div>

                  <div className="space-y-3">
                    {registrations.length === 0 ? (
                      <p className="text-xs text-secondary py-6 text-center">আপনি এখনো কোনো ইভেন্টে নিবন্ধন করেননি।</p>
                    ) : (
                      registrations.map((r) => (
                        <div
                          key={r.id}
                          className="p-4 rounded-xl border border-border bg-surface text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                        >
                          <div>
                            <strong className="text-sm font-bold text-foreground">
                              টিকিট কোড: {r.ticket_code}
                            </strong>
                            <div className="text-secondary mt-0.5">
                              নিবন্ধন: {r.registration_status} · উপস্থিতি: {r.attendance_status} · পেমেন্ট:{' '}
                              {r.payment_status}
                            </div>
                          </div>
                          <Link
                            href={`/events/ticket/${encodeURIComponent(r.ticket_token || r.ticket_code)}`}
                            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary text-white font-bold text-xs"
                          >
                            টিকিট ও QR দেখুন <ArrowRight size={13} />
                          </Link>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ==================== 10. CIRCULARS & NOTICES TAB ==================== */}
            {activeTab === 'notices' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">
                      দাপ্তরিক সার্কুলার ও নোটিশ ফীড (Member Updates Feed)
                    </h2>
                    <p className="text-xs text-secondary">
                      সদস্যদের জন্য প্রকাশিত সার্কুলার ও নোটিশ পড়ুন, বুকমার্ক করুন এবং পিডিএফ ডাউনলোড করুন
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {(['ALL', 'CIRCULAR', 'NOTICE', 'BOOKMARKED'] as const).map((flt) => (
                      <button
                        key={flt}
                        type="button"
                        onClick={() => setUpdateFilter(flt)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold ${
                          updateFilter === flt
                            ? 'bg-primary text-white'
                            : 'bg-surface text-secondary border border-border'
                        }`}
                      >
                        {flt === 'ALL'
                          ? 'সব'
                          : flt === 'CIRCULAR'
                          ? 'সার্কুলার'
                          : flt === 'NOTICE'
                          ? 'নোটিশ'
                          : '★ বুকমার্ক'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  {filteredUpdates.length === 0 ? (
                    <p className="text-xs text-secondary py-8 text-center">কোনো সার্কুলার বা নোটিশ পাওয়া যায়নি।</p>
                  ) : (
                    filteredUpdates.map((item) => (
                      <div
                        key={`${item.content_type}-${item.id}`}
                        onClick={() => !item.is_read && handleMarkUpdateRead(item.content_type, item.id)}
                        className={`p-4 rounded-xl border text-xs space-y-2 transition-all ${
                          item.is_read ? 'border-border bg-surface' : 'border-primary/40 bg-primary/5'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-extrabold text-[10px]">
                                {item.content_type}
                              </span>
                              {item.reference_no && (
                                <span className="text-[11px] font-mono text-secondary">
                                  স্মারক: {item.reference_no}
                                </span>
                              )}
                              {!item.is_read && (
                                <span className="text-[10px] font-bold text-emerald-600">● নতুন</span>
                              )}
                            </div>
                            <h3 className="text-sm font-bold text-foreground">{item.title_bn}</h3>
                            {item.summary_bn && (
                              <p className="text-secondary mt-1 line-clamp-2">{item.summary_bn}</p>
                            )}
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggleBookmark(item.content_type, item.id);
                              }}
                              className={`p-2 rounded-lg border ${
                                item.is_bookmarked
                                  ? 'bg-amber-500/15 border-amber-500/40 text-amber-600'
                                  : 'bg-card border-border text-secondary'
                              }`}
                              title="Bookmark"
                            >
                              <Bookmark size={14} />
                            </button>
                            {item.attachment_url && (
                              <a
                                href={item.attachment_url}
                                target="_blank"
                                className="px-3 py-1.5 rounded-lg bg-primary text-white font-bold inline-flex items-center gap-1"
                              >
                                <Download size={12} /> PDF
                              </a>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* ==================== 11. NOTIFICATIONS TAB ==================== */}
            {activeTab === 'notifications' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div className="flex items-center gap-2.5">
                    <Bell size={20} className="text-amber-500" />
                    <div>
                      <h2 className="text-lg font-bold text-foreground">বিজ্ঞপ্তি কেন্দ্র (Member Notifications)</h2>
                      <p className="text-xs text-secondary">
                        সদস্যপদ অনুমোদন, পেমেন্ট রশিদ, নবায়ন রিমাইন্ডার এবং সনদ ইস্যু বার্তা
                      </p>
                    </div>
                  </div>
                  {unreadNotes.length > 0 && (
                    <button
                      type="button"
                      onClick={handleMarkAllRead}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary/10 text-primary text-xs font-bold"
                    >
                      <CheckCheck size={14} /> সব পঠিত হিসেবে চিহ্নিত করুন
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  {notes.length === 0 ? (
                    <p className="text-xs text-secondary py-8 text-center">কোনো বিজ্ঞপ্তি নেই।</p>
                  ) : (
                    notes.map((n) => {
                      const isUnread = !n.read_at && !n.is_read;
                      return (
                        <div
                          key={n.id}
                          onClick={() => isUnread && handleMarkRead(n.id)}
                          className={`p-4 rounded-xl border text-xs space-y-1 cursor-pointer transition-all ${
                            isUnread ? 'border-primary/40 bg-primary/5' : 'border-border bg-surface'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <strong className="text-sm font-bold text-foreground flex items-center gap-2">
                              <span className={isUnread ? 'text-primary' : 'text-secondary'}>
                                {isUnread ? '●' : '○'}
                              </span>
                              {n.title_bn}
                            </strong>
                            <span className="text-[11px] text-secondary">
                              {n.relative_time_bn || n.relative_time || ''}
                            </span>
                          </div>
                          <p className="text-secondary pl-4">{n.body_bn}</p>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            )}

            {/* ==================== 12. AI ASSISTANT TAB ==================== */}
            {activeTab === 'ai-assistant' && (
              <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-600">
                      <Sparkles size={20} />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-foreground">
                        পিজিসিবি সদস্য এআই সহায়িকা (Member Portal AI Assistant)
                      </h2>
                      <p className="text-xs text-secondary">
                        আপনার সদস্যপদ, মেয়াদ, পেমেন্ট রশিদ, সনদপত্র ও দাপ্তরিক সার্কুলার সম্পর্কে তাৎক্ষণিক প্রশ্ন করুন
                      </p>
                    </div>
                  </div>
                </div>

                {/* Suggested Member Prompts */}
                <div className="flex flex-wrap gap-2">
                  {[
                    'আমার সদস্যপদের মেয়াদ কবে শেষ?',
                    'আমার সর্বশেষ পেমেন্ট রশিদ ও স্ট্যাটাস কী?',
                    'আমার ডিজিটাল আইডি ও সনদপত্র কোথায় পাব?',
                    'সদস্যপদ নবায়ন ফি কত টাকা?',
                  ].map((promptText) => (
                    <button
                      key={promptText}
                      type="button"
                      onClick={() => handleAskAi(promptText)}
                      className="px-3 py-1.5 rounded-xl border border-border bg-surface hover:border-primary text-xs font-semibold text-foreground transition-all"
                    >
                      ✨ {promptText}
                    </button>
                  ))}
                </div>

                {/* Conversation Thread */}
                <div className="space-y-3 max-h-96 overflow-y-auto p-4 rounded-2xl bg-surface border border-border">
                  {aiMessages.length === 0 ? (
                    <div className="text-center py-8 text-xs text-secondary space-y-2">
                      <Sparkles size={28} className="mx-auto text-amber-500" />
                      <p>
                        প্রিয় <strong>{profile?.name_bn || me.name_bn}</strong>, আপনার সদস্যপদ বা পিজিসিবি সংক্রান্ত যেকোনো প্রশ্ন নিচে লিখুন।
                      </p>
                    </div>
                  ) : (
                    aiMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`p-3.5 rounded-2xl text-xs space-y-2 ${
                          msg.role === 'user'
                            ? 'bg-primary text-white ml-auto max-w-[85%]'
                            : 'bg-card border border-border text-foreground mr-auto max-w-[92%]'
                        }`}
                      >
                        <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>
                        {msg.actions && msg.actions.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-1">
                            {msg.actions.map((act, idx) => (
                              <Link
                                key={idx}
                                href={act.url}
                                className="px-2.5 py-1 rounded-lg bg-primary/10 text-primary font-bold text-[11px]"
                              >
                                {act.label_bn || act.label_en} →
                              </Link>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                  {aiLoading && (
                    <div className="text-xs text-secondary italic">এআই সহায়িকা আপনার তথ্য যাচাই করছে...</div>
                  )}
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleAskAi();
                  }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    placeholder="বাংলা বা ইংরেজিতে আপনার প্রশ্ন লিখুন..."
                    value={aiQuery}
                    onChange={(e) => setAiQuery(e.target.value)}
                    className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-background text-sm"
                  />
                  <button
                    type="submit"
                    disabled={aiLoading}
                    className="px-5 py-2.5 rounded-xl bg-primary text-white font-bold text-xs inline-flex items-center gap-1.5"
                  >
                    <Send size={14} /> পাঠান
                  </button>
                </form>
              </div>
            )}

            {/* ==================== 13. SETTINGS & SECURITY TAB ==================== */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-5">
                  <div className="flex items-center justify-between border-b border-border pb-4">
                    <div>
                      <h2 className="text-lg font-bold text-foreground">
                        অ্যাকাউন্ট সেটিংস, গোপনীয়তা ও নিরাপত্তা (Settings & Security)
                      </h2>
                      <p className="text-xs text-secondary">
                        বিজ্ঞপ্তি পছন্দসমূহ, ডিরেক্টরি গোপনীয়তা, ভাষা এবং লগইন সেশন নিয়ন্ত্রণ করুন
                      </p>
                    </div>
                    <Link
                      href="/portal/security"
                      className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold"
                    >
                      পাসওয়ার্ড ও ২-ফ্যাক্টর নিরাপত্তা
                    </Link>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Notification Channels */}
                    <div className="p-4 rounded-2xl bg-surface border border-border space-y-3 text-xs">
                      <h3 className="font-bold text-sm text-foreground">বিজ্ঞপ্তি চ্যানেল (Notification Preferences)</h3>
                      {[
                        { key: 'email_enabled' as const, label: 'ইমেইল বিজ্ঞপ্তি (Email Alerts)' },
                        { key: 'sms_enabled' as const, label: 'এসএমএস অ্যালার্ট (SMS Alerts)' },
                        { key: 'in_app_enabled' as const, label: 'ইন-অ্যাপ পোর্টাল বিজ্ঞপ্তি (In-App)' },
                      ].map((item) => (
                        <label key={item.key} className="flex items-center justify-between cursor-pointer py-1">
                          <span className="text-secondary font-medium">{item.label}</span>
                          <input
                            type="checkbox"
                            checked={Boolean(notifPrefs?.[item.key] ?? true)}
                            onChange={() => handleToggleNotifPref(item.key)}
                            className="h-4 w-4 rounded border-border"
                          />
                        </label>
                      ))}
                    </div>

                    {/* Privacy Controls */}
                    <div className="p-4 rounded-2xl bg-surface border border-border space-y-3 text-xs">
                      <h3 className="font-bold text-sm text-foreground">ডিরেক্টরি ও গোপনীয়তা (Privacy Controls)</h3>
                      <label className="flex items-center justify-between cursor-pointer py-1">
                        <span className="text-secondary font-medium">পাবলিক সদস্য ডিরেক্টরিতে প্রোফাইল প্রদর্শন</span>
                        <input
                          type="checkbox"
                          checked={Boolean(memberSettings?.directory_visibility ?? true)}
                          onChange={(e) => handleUpdateSettings({ directory_visibility: e.target.checked })}
                          className="h-4 w-4 rounded border-border"
                        />
                      </label>
                      <label className="flex items-center justify-between cursor-pointer py-1">
                        <span className="text-secondary font-medium">ডিরেক্টরিতে মোবাইল ও ইমেইল প্রদর্শন</span>
                        <input
                          type="checkbox"
                          checked={Boolean(memberSettings?.contact_visibility ?? false)}
                          onChange={(e) => handleUpdateSettings({ contact_visibility: e.target.checked })}
                          className="h-4 w-4 rounded border-border"
                        />
                      </label>
                      <div className="flex items-center justify-between py-1">
                        <span className="text-secondary font-medium">পোর্টালের ভাষা (Preferred Language)</span>
                        <select
                          value={memberSettings?.preferred_language || 'bn'}
                          onChange={(e) => handleUpdateSettings({ preferred_language: e.target.value })}
                          className="px-2.5 py-1 rounded-lg border border-border bg-card text-xs font-bold"
                        >
                          <option value="bn">বাংলা (Bangla)</option>
                          <option value="en">English</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  {/* Login & Security History */}
                  <div className="pt-4 border-t border-border space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-secondary">
                      সাম্প্রতিক নিরাপত্তা ও লগইন ইতিহাস (Login & Security History)
                    </h3>
                    <div className="space-y-2">
                      {(loginHistory.security_events || []).slice(0, 6).map((ev: any) => (
                        <div
                          key={ev.id}
                          className="p-3 rounded-xl bg-surface border border-border text-xs flex items-center justify-between"
                        >
                          <div>
                            <strong className="text-foreground">{ev.action}</strong>
                            <span className="text-secondary ml-2">({ev.entity_type})</span>
                          </div>
                          <span className="text-[11px] font-mono text-secondary">IP: {ev.ip_address}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
