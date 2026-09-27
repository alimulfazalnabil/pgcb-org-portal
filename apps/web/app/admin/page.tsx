'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import {
  Users,
  UserCheck,
  Calendar,
  FileText,
  Bell,
  ArrowUpRight,
  ShieldCheck,
  Activity,
  Layers,
  ChevronRight,
  Award,
} from 'lucide-react';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [statData, reportData] = await Promise.all([
          api.getAdminStats().catch(() => ({})),
          api.getAdminReports().catch(() => null),
        ]);
        setStats(statData);
        setReport(reportData);
      } catch (err) {
        console.error('Failed to load admin stats', err);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  const kpiCards = [
    {
      title: 'মোট সক্রিয় সদস্য (Active Members)',
      value: stats?.total_members ?? 0,
      icon: Users,
      color: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
      href: '/admin/members',
    },
    {
      title: 'অপেক্ষমাণ আবেদন (Pending Applications)',
      value: stats?.pending_applications ?? 0,
      icon: UserCheck,
      color: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
      href: '/admin/applications',
    },
    {
      title: 'নিবন্ধিত সার্কুলার ও নোটিশ',
      value: (stats?.total_circulars ?? 0) + (stats?.total_notices ?? 0),
      icon: Bell,
      color: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
      href: '/admin/notices',
    },
    {
      title: 'আসন্ন প্রাতিষ্ঠানিক ইভেন্ট',
      value: stats?.total_events ?? 0,
      icon: Calendar,
      color: 'bg-purple-500/10 text-purple-600 border-purple-500/20',
      href: '/admin/events',
    },
  ];

  const quickActions = [
    {
      title: 'সদস্য আবেদন পর্যালোচনা (Applications)',
      description: 'নতুন প্রকৌশলীদের আবেদন ও সংযুক্তি যাচাই করে অনুমোদন বা প্রত্যাখ্যান করুন।',
      icon: UserCheck,
      href: '/admin/applications',
      badge: `${stats?.pending_applications || 0}টি অপেক্ষমাণ`,
    },
    {
      title: 'জরুরি নোটিশ প্রকাশ (Post Notice)',
      description: 'মারকুই ব্যানার ও শীর্ষ নোটিশ বোর্ডে তাৎক্ষণিক বিজ্ঞপ্তি জারি করুন।',
      icon: Bell,
      href: '/admin/notices',
    },
    {
      title: 'ইভেন্ট টিকিট কিউআর স্ক্যান (Check-in Desk)',
      description: 'সম্মেলন ও কর্মশালার দিন অংশগ্রহণকারীদের টিকিট যাচাই ও উপস্থিতি রেকর্ড করুন।',
      icon: Calendar,
      href: '/admin/attendance',
    },
    {
      title: 'সার্টিফিকেট প্রদান ও ট্র্যাকিং (Certificates)',
      description: 'অংশগ্রহণকারী ও সদস্যদের প্রাতিষ্ঠানিক সনদপত্র প্রস্তুত ও বিতরণ করুন।',
      icon: Award,
      href: '/admin/certificates',
    },
  ];

  return (
    <>
      <AdminHeader
        title="সচিবালয় নিয়ন্ত্রণ প্যানেল (Administrative Overview)"
        subtitle="সদস্যপদ, নোটিশ, ইভেন্ট ও সাংগঠনিক কার্যক্রমের কেন্দ্রীয় নিয়ন্ত্রণ ব্যবস্থা"
      />

      <div className="p-6 md:p-8 space-y-8 max-w-7xl">
        {/* KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiCards.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <Link
                key={idx}
                href={kpi.href}
                className="bg-card border border-border hover:border-primary/40 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-secondary">{kpi.title}</span>
                  <div className={`p-2 rounded-xl border ${kpi.color}`}>
                    <Icon size={18} />
                  </div>
                </div>
                <div className="mt-4 flex items-baseline justify-between">
                  <span className="text-2xl font-extrabold text-foreground">
                    {loading ? '...' : kpi.value}
                  </span>
                  <span className="text-xs font-semibold text-primary opacity-0 group-hover:opacity-100 transition-opacity flex items-center">
                    দেখুন <ArrowUpRight size={14} />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Quick Operations Section */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-primary" />
            <h2 className="text-base font-bold text-foreground">দ্রুত প্রশাসনিক কার্যাবলী (Quick Actions)</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickActions.map((action, idx) => {
              const Icon = action.icon;
              return (
                <Link
                  key={idx}
                  href={action.href}
                  className="bg-card border border-border hover:border-primary/40 p-5 rounded-2xl shadow-sm hover:shadow-md transition-all flex items-start justify-between group"
                >
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-xl bg-primary/10 text-primary mt-1">
                      <Icon size={20} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                          {action.title}
                        </h3>
                        {action.badge && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/20">
                            {action.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-secondary mt-1 max-w-sm leading-relaxed">
                        {action.description}
                      </p>
                    </div>
                  </div>
                  <ChevronRight size={18} className="text-secondary group-hover:text-primary group-hover:translate-x-0.5 transition-all mt-3" />
                </Link>
              );
            })}
          </div>
        </div>

        {/* Operational Health Banner */}
        <div className="bg-surface/60 border border-border rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
              <ShieldCheck size={20} />
            </div>
            <div>
              <div className="text-xs font-bold text-foreground">সিস্টেম স্ট্যাটাস: স্বাভাবিক (Operational & Secure)</div>
              <div className="text-[11px] text-secondary mt-0.5">
                অডিট ট্রেইল সক্রিয় • ডাটাবেস ও স্টোরেজ সিঙ্ক্রোনাইজড • RBAC পারমিশন এনফোর্সড
              </div>
            </div>
          </div>
          <Link
            href="/admin/audit"
            className="px-4 py-2 rounded-xl text-xs font-semibold border border-border bg-card hover:bg-surface text-foreground transition-all shrink-0"
          >
            অডিট লগ পরিদর্শন করুন
          </Link>
        </div>
      </div>
    </>
  );
}
