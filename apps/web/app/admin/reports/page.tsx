'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import {
  BarChart3,
  FileDown,
  Users,
  Calendar,
  CreditCard,
  Award,
  ShieldAlert,
  UserCheck,
} from 'lucide-react';

export default function AdminReportsPage() {
  const [overview, setOverview] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/backend/api/v1/admin/reports/overview')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setOverview(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const exportModules = [
    {
      title: 'সদস্য ডিরেক্টরি ও রোস্টার (Members Roster CSV)',
      desc: 'সকল নিবন্ধিত ও সক্রিয় সদস্যের নাম, আইডি, সার্কেল, পদবী ও মেয়াদের পূর্ণাঙ্গ তালিকা।',
      href: '/backend/api/v1/admin/exports/members.csv',
      icon: Users,
    },
    {
      title: 'সদস্যপদ আবেদন তালিকা (Membership Applications CSV)',
      desc: 'নতুন ও পর্যালোচনাধীন সদস্যপদ আবেদনের স্ট্যাটাস ও প্রাতিষ্ঠানিক বিবরণী।',
      href: '/backend/api/v1/admin/exports/applications.csv',
      icon: UserCheck,
    },
    {
      title: 'ইভেন্ট নিবন্ধন ও উপস্থিতি (Event Registrations CSV)',
      desc: 'সম্মেলন ও সেমিনারে নিবন্ধিত অংশগ্রহণকারী, টিকিট কোড ও চেক-ইন রিপোর্ট।',
      href: '/backend/api/v1/admin/exports/event-registrations.csv',
      icon: Calendar,
    },
    {
      title: 'আর্থিক লেনদেন ও পেমেন্ট লেজার (Payments Ledger CSV)',
      desc: 'সদস্যপদ চাঁদা ও ইভেন্ট ফি আদায়ের ট্রানজেকশন রেফারেন্স ও অডিট রিপোর্ট।',
      href: '/backend/api/v1/admin/exports/payments.csv',
      icon: CreditCard,
    },
    {
      title: 'ইস্যুকৃত ডিজিটাল সনদপত্র (Issued Certificates CSV)',
      desc: 'ইস্যুকৃত সকল সনদ নম্বর, গ্রহীতার নাম এবং ইস্যুর তারিখের তালিকা।',
      href: '/backend/api/v1/admin/exports/certificates.csv',
      icon: Award,
    },
    {
      title: 'সিকিউরিটি অডিট লগ (Security Audit Trail CSV)',
      desc: 'প্রশাসনিক কার্যক্রম, লগইন, অনুমোদন ও পরিবর্তনের অপরিবর্তনীয় অডিট লগ।',
      href: '/backend/api/v1/admin/exports/audit.csv',
      icon: ShieldAlert,
    },
  ];

  return (
    <>
      <AdminHeader
        title="প্রাতিষ্ঠানিক রিপোর্ট ও ডেটা এক্সপোর্ট হাব (Reports & Analytics)"
        subtitle="মাসিক প্রবৃদ্ধি বিশ্লেষণ এবং দাপ্তরিক CSV রিপোর্ট ডাউনলোড কেন্দ্র"
      />

      <div className="p-6 md:p-8 space-y-8 max-w-7xl">
        {/* Analytics Summary */}
        {overview && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
              <span className="text-xs text-secondary font-semibold">মোট সদস্য / সক্রিয়</span>
              <div className="text-2xl font-extrabold text-foreground">
                {overview.members?.total || 0} /{' '}
                <span className="text-emerald-600">{overview.members?.active || 0}</span>
              </div>
            </div>
            <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
              <span className="text-xs text-secondary font-semibold">প্রকাশিত সার্কুলার ও জার্নাল</span>
              <div className="text-2xl font-extrabold text-primary">
                {(overview.content?.published_circulars || 0) +
                  (overview.content?.published_journals || 0)}
                টি
              </div>
            </div>
            <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
              <span className="text-xs text-secondary font-semibold">ইভেন্ট নিবন্ধন / উপস্থিতি</span>
              <div className="text-2xl font-extrabold text-foreground">
                {overview.events?.registrations || 0} /{' '}
                <span className="text-emerald-600">{overview.events?.checked_in || 0}</span>
              </div>
            </div>
            <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
              <span className="text-xs text-secondary font-semibold">মোট অডিট ইভেন্ট</span>
              <div className="text-2xl font-extrabold text-foreground">
                {overview.system?.audit_logs || 0}টি
              </div>
            </div>
          </div>
        )}

        {/* 6-Month Time Series Table */}
        {overview?.members?.series && (
          <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
            <div className="p-4 border-b border-border flex items-center gap-2 text-xs font-bold text-foreground">
              <BarChart3 size={16} className="text-primary" />
              <span>বিগত ৬ মাসের সাংগঠনিক কার্যক্রমের পরিসংখ্যান</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="p-4">মাস (Month)</th>
                    <th className="p-4">নতুন সদস্য আবেদন</th>
                    <th className="p-4">অনুমোদিত সদস্য</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {overview.members.series.map((row: any) => (
                    <tr key={row.label}>
                      <td className="p-4 font-mono font-bold text-foreground">{row.label}</td>
                      <td className="p-4 text-secondary">{row.registrations}</td>
                      <td className="p-4 font-bold text-emerald-600">{row.approved}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Export Cards */}
        <div className="space-y-4">
          <h2 className="text-base font-extrabold text-foreground">
            দাপ্তরিক CSV ডেটা এক্সপোর্ট (Official Data Exports)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {exportModules.map((mod) => {
              const Icon = mod.icon;
              return (
                <div
                  key={mod.href}
                  className="bg-card border border-border rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-sm"
                >
                  <div className="space-y-2">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                      <Icon size={20} />
                    </div>
                    <h3 className="font-bold text-sm text-foreground">{mod.title}</h3>
                    <p className="text-xs text-secondary leading-relaxed">{mod.desc}</p>
                  </div>
                  <a
                    href={mod.href}
                    className="w-full py-2.5 px-4 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center justify-center gap-1.5 hover:opacity-90 transition-all"
                  >
                    <FileDown size={14} /> CSV ডাউনলোড করুন
                  </a>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
