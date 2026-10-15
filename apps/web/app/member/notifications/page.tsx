'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Bell,
  CheckCircle2,
  Clock,
  Settings,
  ArrowRight,
  ExternalLink,
  ShieldAlert,
  CreditCard,
  Calendar,
  Award,
  Sparkles,
  RefreshCw,
  CheckCheck,
  AlertCircle,
  Inbox,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberNotificationItem, MemberNotificationsResponse } from '@/lib/api/types';

export default function MemberNotificationsPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [markingAll, setMarkingAll] = useState(false);
  const [statusFilter, setStatusFilter] = useState<'all' | 'unread'>('all');
  const [data, setData] = useState<MemberNotificationsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isEn = lang === 'en';

  const loadNotifications = async (status = statusFilter) => {
    try {
      setLoading(true);
      setError(null);
      const res = await membersApi.getMemberNotifications({ status });
      setData(res);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load notifications. Please try again.'
            : 'বিজ্ঞপ্তি লোড করতে সমস্যা হয়েছে। দয়া করে পুনঃচেষ্টা করুন।')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications(statusFilter);
  }, [statusFilter]);

  const handleMarkAsRead = async (id: number) => {
    try {
      await membersApi.markNotificationRead(id);
      setData((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          unread_count: Math.max(0, prev.unread_count - 1),
          items: prev.items.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n)),
        };
      });
    } catch {
      // ignore
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setMarkingAll(true);
      await membersApi.markAllNotificationsRead();
      setData((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          unread_count: 0,
          items: prev.items.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() })),
        };
      });
    } catch {
      // ignore
    } finally {
      setMarkingAll(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'EVENTS':
      case 'EVENT_REMINDER':
      case 'EVENT_REGISTRATION':
        return <Calendar className="w-5 h-5 text-blue-600" />;
      case 'MEMBERSHIP':
      case 'MEMBERSHIP_RENEWAL':
        return <ShieldAlert className="w-5 h-5 text-emerald-600" />;
      case 'PAYMENTS':
      case 'PAYMENT':
        return <CreditCard className="w-5 h-5 text-indigo-600" />;
      case 'CERTIFICATES':
      case 'CERTIFICATE':
        return <Award className="w-5 h-5 text-amber-600" />;
      default:
        return <Bell className="w-5 h-5 text-slate-600" />;
    }
  };

  const items = data?.items || [];
  const unreadCount = data?.unread_count || 0;

  return (
    <MemberLayout
      title={isEn ? 'Notifications & Alerts' : 'বিজ্ঞপ্তি ও অ্যালার্ট'}
      lang={lang}
      onLangChange={setLang}
      activeTab="notifications"
    >
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900">
                {isEn ? 'Notifications & Alerts' : 'বিজ্ঞপ্তি ও অ্যালার্ট'}
              </h1>
              {unreadCount > 0 && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-600 text-white">
                  {unreadCount} {isEn ? 'new' : 'নতুন'}
                </span>
              )}
            </div>
            <p className="text-slate-500 text-sm">
              {isEn
                ? 'Institutional updates, event passes, renewal reminders, and official notices.'
                : 'প্রাতিষ্ঠানিক নোটিশ, ইভেন্ট পাস, সদস্যপদ নবায়ন রিমাইন্ডার ও জরুরি বার্তা।'}
            </p>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                disabled={markingAll}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-800 transition-colors"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>{markingAll ? (isEn ? 'Updating...' : 'হালনাগাদ...') : (isEn ? 'Mark All Read' : 'সব পঠিত হিসেবে চিহ্নিত')}</span>
              </button>
            )}

            <Link
              href="/member/notification-settings"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white transition-colors"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>{isEn ? 'Settings' : 'সেটিংস'}</span>
            </Link>
          </div>
        </div>

        {/* Tab Filter */}
        <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
              statusFilter === 'all'
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {isEn ? 'All Notifications' : 'সকল বিজ্ঞপ্তি'}
            <span className="ml-2 opacity-75">({data?.total_count || 0})</span>
          </button>
          <button
            onClick={() => setStatusFilter('unread')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
              statusFilter === 'unread'
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {isEn ? 'Unread Only' : 'অপঠিত বার্তা'}
            <span className="ml-2 opacity-75">({unreadCount})</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2 text-sm">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 animate-pulse flex gap-4">
                <div className="w-10 h-10 rounded-xl bg-slate-200 shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-1/4" />
                  <div className="h-5 bg-slate-200 rounded w-3/4" />
                  <div className="h-4 bg-slate-100 rounded w-full" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && items.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <Inbox className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-900">
              {statusFilter === 'unread'
                ? isEn
                  ? 'No unread notifications'
                  : 'কোনো অপঠিত বিজ্ঞপ্তি নেই'
                : isEn
                ? 'Notification inbox is empty'
                : 'বিজ্ঞপ্তি বক্স সম্পূর্ণ খালি'}
            </h3>
            <p className="text-slate-500 text-xs max-w-sm mx-auto">
              {isEn
                ? 'You are all caught up! When you register for events, make payments, or receive certificates, notifications will appear here.'
                : 'সব বিজ্ঞপ্তি পঠিত হয়েছে। ইভেন্ট নিবন্ধন, পেমেন্ট ও নতুন সনদের নোটিফিকেশন এখানে প্রদর্শিত হবে।'}
            </p>
          </div>
        )}

        {/* Notifications Feed */}
        {!loading && items.length > 0 && (
          <div className="space-y-3">
            {items.map((notification) => {
              const isUrgent = notification.priority === 'URGENT' || notification.priority === 'HIGH';
              const isUnread = !notification.is_read;

              return (
                <div
                  key={notification.id}
                  className={`rounded-2xl p-5 border transition-all flex flex-col sm:flex-row items-start gap-4 ${
                    isUnread
                      ? 'bg-blue-50/40 border-blue-200/80 shadow-sm'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {/* Icon */}
                  <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 ${
                    isUnread ? 'bg-blue-100' : 'bg-slate-100'
                  }`}>
                    {getTypeIcon(notification.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 space-y-1.5 w-full">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {notification.type}
                        </span>
                        {isUrgent && (
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-500 text-white">
                            {notification.priority}
                          </span>
                        )}
                        {isUnread && (
                          <span className="w-2 h-2 rounded-full bg-blue-600" />
                        )}
                      </div>

                      <div className="text-[11px] text-slate-400 font-medium">
                        {isEn ? notification.relative_time_en : notification.relative_time_bn}
                      </div>
                    </div>

                    <h3 className="text-base font-bold text-slate-900 leading-snug">
                      {isEn ? notification.title_en : notification.title_bn}
                    </h3>

                    <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
                      {isEn ? notification.body_en : notification.body_bn}
                    </p>

                    {/* Actionable Link Button */}
                    <div className="pt-2 flex items-center justify-between gap-3">
                      {notification.action?.route ? (
                        <Link
                          href={notification.action.route}
                          onClick={() => isUnread && handleMarkAsRead(notification.id)}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-blue-700 hover:text-blue-900 hover:underline"
                        >
                          <span>
                            {isEn
                              ? notification.action.label || 'View Details'
                              : notification.action.label_bn || 'বিস্তারিত দেখুন'}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      ) : (
                        <div />
                      )}

                      {isUnread && (
                        <button
                          onClick={() => handleMarkAsRead(notification.id)}
                          className="text-[11px] text-slate-500 hover:text-slate-800 font-semibold"
                        >
                          {isEn ? 'Mark as read' : 'পঠিত হিসেবে চিহ্নিত'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
