'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { api } from '@/lib/api';
import {
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  FileText,
  UserCheck,
  AlertCircle,
  Download,
} from 'lucide-react';

export default function AdminApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedApp, setSelectedApp] = useState<any | null>(null);
  const [actionBusy, setActionBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await api.getAdminMembers({
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        q: searchQuery || undefined,
        limit: 100,
      });
      // Sort so submitted/pending/under_review come first
      setApplications(data || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [statusFilter]);

  const handleAction = async (memberId: number, action: 'APPROVE' | 'REJECT' | 'REVIEW' | 'SUSPEND') => {
    setActionBusy(true);
    try {
      await api.reviewMember(memberId, action);
      setMessage({
        text: `আবেদনের স্ট্যাটাস সফলভাবে পরিবর্তিত হয়েছে (${action})।`,
        type: 'success',
      });
      setSelectedApp(null);
      fetchApplications();
    } catch (err: any) {
      setMessage({
        text: err.message || 'কার্যক্রম সম্পন্ন করা যায়নি।',
        type: 'error',
      });
    } finally {
      setActionBusy(false);
    }
  };

  const statusTabs = [
    { label: 'সকল আবেদন (All)', value: 'ALL' },
    { label: 'অপেক্ষমাণ (Pending)', value: 'PENDING' },
    { label: 'পর্যালোচনাধীন (Under Review)', value: 'UNDER_REVIEW' },
    { label: 'অনুমোদিত (Approved)', value: 'ACTIVE' },
    { label: 'প্রত্যাখ্যাত (Rejected)', value: 'REJECTED' },
  ];

  return (
    <>
      <AdminHeader
        title="সদস্য আবেদন পর্যালোচনা ডেস্ক (Membership Applications Desk)"
        subtitle="প্রকৌশলীদের নতুন আবেদন যাচাই, সনদ পরীক্ষা এবং সদস্যপদ অনুমোদন ব্যবস্থাপনা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Status Toast */}
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

        {/* Filter Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-stretch sm:items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {statusTabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setStatusFilter(tab.value)}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                  statusFilter === tab.value
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-secondary hover:text-foreground hover:bg-surface'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1 sm:w-64">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                type="text"
                placeholder="নাম বা আবেদন নম্বর খুঁজুন..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchApplications()}
                className="w-full pl-9 pr-4 py-1.5 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-primary"
              />
            </div>
            <button
              onClick={fetchApplications}
              className="px-3.5 py-1.5 rounded-xl bg-primary text-white text-xs font-semibold hover:opacity-90 transition-all shrink-0"
            >
              খুঁজুন
            </button>
          </div>
        </div>

        {/* Applications Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">আবেদনকারী (Applicant)</th>
                  <th className="p-4">গ্রিড সার্কেল (Circle)</th>
                  <th className="p-4">পদবী ও প্রতিষ্ঠান</th>
                  <th className="p-4">আবেদন আইডি</th>
                  <th className="p-4">স্ট্যাটাস (Status)</th>
                  <th className="p-4 text-right">পদক্ষেপ (Action)</th>
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
                  applications.map((app) => (
                    <tr key={app.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-bold text-foreground">
                        <div>{app.name_bn || app.name_en}</div>
                        <div className="text-[11px] font-normal text-secondary">{app.email}</div>
                      </td>
                      <td className="p-4 text-secondary">{app.circle_name || 'ঢাকা'}</td>
                      <td className="p-4 text-secondary">
                        <div>{app.designation_bn || 'ডিপ্লোমা প্রকৌশলী'}</div>
                        <div className="text-[10px] opacity-75">{app.diploma_institution || 'Polytechnic'}</div>
                      </td>
                      <td className="p-4 font-mono font-medium text-foreground">
                        {app.application_no || `PGCB-APP-${app.id}`}
                      </td>
                      <td className="p-4">
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="p-4 text-right">
                        <button
                          onClick={() => setSelectedApp(app)}
                          className="px-3 py-1.5 rounded-xl border border-border bg-surface hover:bg-card text-foreground font-semibold text-xs inline-flex items-center gap-1.5 shadow-xs transition-all"
                        >
                          <Eye size={13} /> পর্যালোচনা
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Review Modal / Drawer */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-2xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            <div className="p-5 border-b border-border flex items-center justify-between bg-surface/50">
              <div>
                <h3 className="text-base font-bold text-foreground">আবেদন বিস্তারিত ও পর্যালোচনা</h3>
                <p className="text-xs text-secondary mt-0.5">
                  আইডি: {selectedApp.application_no || `APP-${selectedApp.id}`}
                </p>
              </div>
              <button
                onClick={() => setSelectedApp(null)}
                className="w-7 h-7 rounded-full hover:bg-border/60 flex items-center justify-center text-secondary text-sm"
              >
                ✕
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 text-xs">
              {/* Profile Overview */}
              <div className="grid grid-cols-2 gap-4 bg-surface/50 p-4 rounded-xl border border-border">
                <div>
                  <span className="text-secondary text-[11px]">আবেদনকারীর নাম:</span>
                  <div className="font-bold text-foreground text-sm mt-0.5">{selectedApp.name_bn}</div>
                  <div className="text-secondary">{selectedApp.name_en}</div>
                </div>
                <div>
                  <span className="text-secondary text-[11px]">যোগাযোগ:</span>
                  <div className="font-medium text-foreground mt-0.5">{selectedApp.email}</div>
                  <div className="text-secondary">{selectedApp.phone || 'N/A'}</div>
                </div>
                <div>
                  <span className="text-secondary text-[11px]">পদবী ও গ্রিড সার্কেল:</span>
                  <div className="font-medium text-foreground mt-0.5">{selectedApp.designation_bn}</div>
                  <div className="text-secondary">{selectedApp.circle_name}</div>
                </div>
                <div>
                  <span className="text-secondary text-[11px]">বর্তমান স্ট্যাটাস:</span>
                  <div className="mt-1">
                    <StatusBadge status={selectedApp.status} />
                  </div>
                </div>
              </div>

              {/* Documents List */}
              <div className="space-y-2">
                <h4 className="font-bold text-foreground text-xs flex items-center gap-1.5">
                  <FileText size={14} /> সংযুক্ত নথিপত্র (Attached Documents)
                </h4>
                {selectedApp.documents && selectedApp.documents.length > 0 ? (
                  <div className="space-y-2">
                    {selectedApp.documents.map((doc: any) => (
                      <div
                        key={doc.id}
                        className="flex items-center justify-between p-3 rounded-xl border border-border bg-surface text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <FileText size={16} className="text-primary" />
                          <div>
                            <div className="font-semibold text-foreground">
                              {doc.document_type} — {doc.filename}
                            </div>
                            <div className="text-[10px] text-secondary">
                              স্ট্যাটাস: <span className="font-bold">{doc.review_status}</span>
                            </div>
                          </div>
                        </div>
                        <a
                          href={`/backend/api/v1/admin/documents/${doc.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 rounded-lg border border-border bg-card hover:bg-surface font-semibold text-primary text-[11px] inline-flex items-center gap-1"
                        >
                          <Download size={12} /> ডাউনলোড
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-secondary italic">কোনো নথি সংযুক্ত নেই।</p>
                )}
              </div>
            </div>

            {/* Modal Actions */}
            <div className="p-4 border-t border-border flex items-center justify-end gap-2.5 bg-surface/50">
              <button
                disabled={actionBusy}
                onClick={() => setSelectedApp(null)}
                className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
              >
                বন্ধ করুন
              </button>

              {['SUBMITTED', 'PENDING'].includes(selectedApp.status) && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedApp.id, 'REVIEW')}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  পর্যালোচনাধীন রাখুন (Move to Review)
                </button>
              )}

              {selectedApp.status !== 'REJECTED' && selectedApp.status !== 'ACTIVE' && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedApp.id, 'REJECT')}
                  className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  প্রত্যাখ্যান (Reject)
                </button>
              )}

              {selectedApp.status !== 'ACTIVE' && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedApp.id, 'APPROVE')}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm"
                >
                  সদস্যপদ অনুমোদন (Approve)
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
