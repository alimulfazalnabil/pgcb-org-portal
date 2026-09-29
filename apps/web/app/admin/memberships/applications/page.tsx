'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { api } from '@/lib/api';
import {
  Search,
  CheckCircle2,
  Clock,
  Eye,
  AlertCircle,
  FileSearch,
  Building2,
  Filter,
  ArrowUpRight,
} from 'lucide-react';

export default function AdminMembershipApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [counts, setCounts] = useState({
    pending: 0,
    under_review: 0,
    correction: 0,
    approved: 0,
    payment_pending: 0,
    active: 0,
    rejected: 0,
    cancelled: 0,
    total: 0,
  });
  const [circles, setCircles] = useState<{ id: number; name_bn: string; name_en?: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [circleFilter, setCircleFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionBusyId, setActionBusyId] = useState<number | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await api.getMembershipApplications({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        circle_id: circleFilter === 'ALL' ? undefined : circleFilter,
        q: searchQuery || undefined,
        limit: 100,
      });
      setApplications(data.items || []);
      if (data.counts) setCounts(data.counts);
      if (data.circles) setCircles(data.circles);
    } catch (err: any) {
      console.error(err);
      setMessage({
        text: err.message || 'আবেদন তালিকা লোড করতে সমস্যা হয়েছে।',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [statusFilter, circleFilter]);

  const handleQuickReviewStart = async (memberId: number) => {
    setActionBusyId(memberId);
    try {
      await api.executeApplicationAction(memberId, {
        action: 'UNDER_REVIEW',
        note: 'Application opened for review by administrator.',
      });
      await fetchApplications();
    } catch (err: any) {
      setMessage({ text: err.message || 'পর্যালোচনা শুরু করা যায়নি।', type: 'error' });
    } finally {
      setActionBusyId(null);
    }
  };

  const kpiCards = [
    {
      label: 'অপেক্ষমাণ (Pending)',
      enLabel: 'Pending',
      value: counts.pending,
      filterValue: 'PENDING',
      icon: Clock,
      color: 'text-amber-600 bg-amber-500/10 border-amber-500/20',
    },
    {
      label: 'পর্যালোচনাধীন (Under Review)',
      enLabel: 'Under Review',
      value: counts.under_review,
      filterValue: 'UNDER_REVIEW',
      icon: FileSearch,
      color: 'text-blue-600 bg-blue-500/10 border-blue-500/20',
    },
    {
      label: 'সংশোধন প্রয়োজন (Correction)',
      enLabel: 'Correction',
      value: counts.correction,
      filterValue: 'CORRECTION_REQUIRED',
      icon: AlertCircle,
      color: 'text-purple-600 bg-purple-500/10 border-purple-500/20',
    },
    {
      label: 'অনুমোদিত (Approved)',
      enLabel: 'Approved',
      value: counts.approved,
      filterValue: 'APPROVED',
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-500/10 border-emerald-500/20',
    },
  ];

  return (
    <>
      <AdminHeader
        title="সদস্যপদ আবেদন ব্যবস্থাপনা (Membership Applications)"
        subtitle="আবেদন যাচাই, গ্রিড সার্কেল নির্ধারণ, সংশোধন অনুরোধ এবং পেমেন্ট-পেন্ডিং অনুমোদন ডেস্ক"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {message && (
          <div
            className={`p-4 rounded-xl text-xs font-semibold flex items-center justify-between border ${
              message.type === 'success'
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-700'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-700'
            }`}
          >
            <span>{message.text}</span>
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">
              ✕
            </button>
          </div>
        )}

        {/* 4 Summary Status Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {kpiCards.map((card) => {
            const Icon = card.icon;
            const active = statusFilter === card.filterValue;
            return (
              <button
                key={card.enLabel}
                onClick={() => setStatusFilter(active ? 'ALL' : card.filterValue)}
                className={`text-left p-4 rounded-2xl border transition-all bg-card shadow-sm hover:shadow-md flex items-center justify-between ${
                  active ? 'ring-2 ring-primary border-primary' : 'border-border'
                }`}
              >
                <div>
                  <div className="text-xs font-semibold text-secondary">{card.label}</div>
                  <div className="text-2xl font-extrabold text-foreground mt-1">{card.value}</div>
                </div>
                <div className={`w-11 h-11 rounded-xl border flex items-center justify-center ${card.color}`}>
                  <Icon size={20} />
                </div>
              </button>
            );
          })}
        </div>

        {/* Search + Circle + Status Filter Bar */}
        <div className="bg-card border border-border p-4 rounded-2xl shadow-sm flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          <div className="flex flex-1 items-center gap-2">
            <div className="relative flex-1 max-w-md">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                type="text"
                placeholder="আবেদনকারী, ইমেইল, ফোন বা আবেদন নম্বর খুঁজুন..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchApplications()}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-primary"
              />
            </div>
            <button
              onClick={fetchApplications}
              className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:opacity-90 transition-all shrink-0"
            >
              খুঁজুন
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Circle Filter Dropdown */}
            <div className="flex items-center gap-1.5 text-xs">
              <Building2 size={14} className="text-secondary" />
              <span className="text-secondary font-medium">Circle:</span>
              <select
                aria-label="Filter by Grid Circle"
                value={circleFilter}
                onChange={(e) => setCircleFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-border bg-surface text-xs font-semibold text-foreground focus:outline-none focus:border-primary"
              >
                <option value="ALL">সকল সার্কেল (All)</option>
                {circles.map((c) => (
                  <option key={c.id} value={String(c.id)}>
                    {c.name_bn} {c.name_en ? `(${c.name_en})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter Dropdown */}
            <div className="flex items-center gap-1.5 text-xs">
              <Filter size={14} className="text-secondary" />
              <span className="text-secondary font-medium">Status:</span>
              <select
                aria-label="Filter by Application Status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 rounded-xl border border-border bg-surface text-xs font-semibold text-foreground focus:outline-none focus:border-primary"
              >
                <option value="ALL">সকল স্ট্যাটাস (All)</option>
                <option value="PENDING">Pending / Submitted</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="CORRECTION_REQUIRED">Correction Required</option>
                <option value="PAYMENT_PENDING">Payment Pending</option>
                <option value="APPROVED">Approved / Active</option>
                <option value="REJECTED">Rejected</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>
        </div>

        {/* Applications Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">Applicant (আবেদনকারী)</th>
                  <th className="p-4">Circle (গ্রিড সার্কেল)</th>
                  <th className="p-4">আবেদন নম্বর ও ধরন</th>
                  <th className="p-4">Status (স্ট্যাটাস)</th>
                  <th className="p-4">পেমেন্ট ও নথি</th>
                  <th className="p-4 text-right">Action (পদক্ষেপ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      আবেদন তালিকা লোড হচ্ছে...
                    </td>
                  </tr>
                ) : applications.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      কোনো আবেদন পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => {
                    const isPending = ['DRAFT', 'PENDING', 'SUBMITTED'].includes(
                      (app.status || '').toUpperCase()
                    );
                    return (
                      <tr key={app.id} className="hover:bg-surface/40 transition-colors">
                        <td className="p-4">
                          <div className="font-bold text-foreground">{app.name_bn || app.name_en}</div>
                          {app.name_en && <div className="text-[11px] text-secondary">{app.name_en}</div>}
                          <div className="text-[11px] text-secondary">{app.email}</div>
                        </td>
                        <td className="p-4">
                          <div className="font-semibold text-foreground">{app.circle_bn || 'অনির্ধারিত'}</div>
                          <div className="text-[11px] text-secondary">{app.circle_en || ''}</div>
                        </td>
                        <td className="p-4">
                          <div className="font-mono font-semibold text-foreground">
                            {app.application_no || `PGCB-APP-${app.id}`}
                          </div>
                          <div className="text-[10px] text-secondary uppercase">
                            {app.membership_type || 'GENERAL'} • {app.designation_bn || 'প্রকৌশলী'}
                          </div>
                        </td>
                        <td className="p-4">
                          <StatusBadge status={app.status} />
                        </td>
                        <td className="p-4">
                          <div className="flex items-center gap-1.5">
                            <StatusBadge status={app.payment_status || 'UNPAID'} />
                            <span className="text-[11px] text-secondary">
                              ({app.documents_count || 0} docs)
                            </span>
                          </div>
                        </td>
                        <td className="p-4 text-right">
                          <div className="inline-flex items-center gap-2">
                            {isPending && (
                              <button
                                disabled={actionBusyId === app.id}
                                onClick={() => handleQuickReviewStart(app.id)}
                                className="px-2.5 py-1.5 rounded-xl border border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300 font-semibold text-xs hover:bg-blue-500/20 transition-all"
                              >
                                Review
                              </button>
                            )}
                            <Link
                              href={`/admin/memberships/applications/${app.id}`}
                              className="px-3 py-1.5 rounded-xl bg-primary text-white font-semibold text-xs inline-flex items-center gap-1.5 shadow-xs hover:opacity-90 transition-all"
                            >
                              <Eye size={13} /> {isPending ? 'Review' : 'Open'}
                              <ArrowUpRight size={12} />
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
