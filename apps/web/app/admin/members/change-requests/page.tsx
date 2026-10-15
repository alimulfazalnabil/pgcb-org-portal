'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import {
  Search,
  CheckCircle2,
  Clock,
  XCircle,
  FileText,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  User,
  ArrowRight,
  Filter,
  RefreshCw,
  Eye,
  Check,
  X,
  ShieldAlert,
  Calendar,
  Lock,
} from 'lucide-react';

interface ChangeRequestItem {
  id: number;
  member_id: number;
  membership_id?: string;
  user_id: number;
  member_name_bn?: string;
  member_name_en?: string;
  field_name: string;
  current_value?: string;
  requested_value: string;
  reason: string;
  supporting_doc_url?: string;
  supporting_document_id?: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  review_note?: string;
  reviewer_comment?: string;
  reviewer_id?: number;
  created_at: string;
  reviewed_at?: string;
}

const FIELD_LABELS: Record<string, { bn: string; en: string }> = {
  name_en: { bn: 'পূর্ণ নাম (ইংরেজি)', en: 'Full Legal Name (English)' },
  name_bn: { bn: 'পূর্ণ নাম (বাংলা)', en: 'Full Legal Name (Bangla)' },
  date_of_birth: { bn: 'জন্ম তারিখ', en: 'Date of Birth' },
  dob: { bn: 'জন্ম তারিখ', en: 'Date of Birth' },
  nid_number: { bn: 'জাতীয় পরিচয়পত্র / পাসপোর্ট নম্বর', en: 'NID / Passport Number' },
  nid_no: { bn: 'জাতীয় পরিচয়পত্র / পাসপোর্ট নম্বর', en: 'NID / Passport Number' },
  grid_circle: { bn: 'গ্রিড সার্কেল পরিবর্তন', en: 'Grid Circle' },
  circle_id: { bn: 'গ্রিড সার্কেল', en: 'Grid Circle' },
  membership_id: { bn: 'মেম্বারশিপ নম্বর', en: 'Membership ID' },
};

export default function AdminMemberChangeRequestsPage() {
  const [requests, setRequests] = useState<ChangeRequestItem[]>([]);
  const [currentAdmin, setCurrentAdmin] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRequest, setSelectedRequest] = useState<ChangeRequestItem | null>(null);
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | null>(null);
  const [reviewerNote, setReviewerNote] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const fetchChangeRequests = async () => {
    setLoading(true);
    try {
      const [adminUser, response] = await Promise.all([
        api.getMe().catch(() => null),
        api.getMemberChangeRequests({ status: statusFilter === 'ALL' ? undefined : statusFilter }),
      ]);
      if (adminUser) setCurrentAdmin(adminUser);
      setRequests(response.items || []);
    } catch (err: any) {
      console.error(err);
      setFeedback({
        message: err.message || 'অনুরোধ তালিকা লোড করতে ব্যর্থ হয়েছে।',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChangeRequests();
  }, [statusFilter]);

  const handleOpenActionModal = (req: ChangeRequestItem, type: 'APPROVE' | 'REJECT') => {
    setSelectedRequest(req);
    setActionType(type);
    setReviewerNote('');
    setFeedback(null);
  };

  const handleCloseModal = () => {
    setSelectedRequest(null);
    setActionType(null);
    setReviewerNote('');
  };

  const handleSubmitAction = async () => {
    if (!selectedRequest || !actionType) return;
    if (actionType === 'REJECT' && !reviewerNote.trim()) {
      setFeedback({
        message: 'প্রত্যাখ্যানের কারণ উল্লেখ করা বাধ্যতামূলক (Rejection reason is required).',
        type: 'error',
      });
      return;
    }

    setSubmittingAction(true);
    setFeedback(null);
    try {
      if (actionType === 'APPROVE') {
        await api.approveMemberChangeRequest(selectedRequest.id, reviewerNote.trim() || undefined);
        setFeedback({
          message: `অনুরোধ #${selectedRequest.id} সফলভাবে অনুমোদিত হয়েছে।`,
          type: 'success',
        });
      } else {
        await api.rejectMemberChangeRequest(selectedRequest.id, reviewerNote.trim());
        setFeedback({
          message: `অনুরোধ #${selectedRequest.id} প্রত্যাখ্যান করা হয়েছে।`,
          type: 'success',
        });
      }
      handleCloseModal();
      await fetchChangeRequests();
    } catch (err: any) {
      setFeedback({
        message: err.message || 'পদক্ষেপ সম্পন্ন করা যায়নি।',
        type: 'error',
      });
    } finally {
      setSubmittingAction(false);
    }
  };

  const filteredRequests = requests.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const nameEn = (r.member_name_en || '').toLowerCase();
    const nameBn = (r.member_name_bn || '').toLowerCase();
    const mid = (r.membership_id || '').toLowerCase();
    const field = (r.field_name || '').toLowerCase();
    const reqVal = (r.requested_value || '').toLowerCase();
    return nameEn.includes(q) || nameBn.includes(q) || mid.includes(q) || field.includes(q) || reqVal.includes(q);
  });

  const totalCount = requests.length;
  const pendingCount = requests.filter((r) => r.status === 'PENDING').length;
  const approvedCount = requests.filter((r) => r.status === 'APPROVED').length;
  const rejectedCount = requests.filter((r) => r.status === 'REJECTED').length;

  return (
    <>
      <AdminHeader
        title="সদস্য প্রোফাইল পরিবর্তন অনুরোধ (Profile Change Requests)"
        subtitle="সুরক্ষিত তথ্য পরিবর্তন যাচাইকরণ, সহায়ক ডকুমেন্ট পর্যালোচনা ও প্রশাসনিক সিদ্ধান্ত"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Breadcrumb & Navigation */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs text-secondary">
            <Link href="/admin" className="hover:text-primary transition-colors">
              অ্যাডমিন ড্যাশবোর্ড
            </Link>
            <span>/</span>
            <Link href="/admin/members" className="hover:text-primary transition-colors">
              সদস্য তালিকা
            </Link>
            <span>/</span>
            <span className="text-foreground font-semibold">প্রোফাইল পরিবর্তন অনুরোধ</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/admin/members"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card text-xs font-medium text-foreground hover:bg-muted transition-colors shadow-sm"
            >
              <User size={14} className="text-secondary" />
              <span>সদস্য ডিরেক্টরি</span>
            </Link>
            <button
              onClick={fetchChangeRequests}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-card text-xs font-medium text-foreground hover:bg-muted transition-colors shadow-sm"
              title="রিফ্রেশ করুন"
            >
              <RefreshCw size={14} className={`text-secondary ${loading ? 'animate-spin' : ''}`} />
              <span>রিফ্রেশ</span>
            </button>
          </div>
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between gap-3 ${
              feedback.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            <div className="flex items-center gap-2.5 text-xs font-medium">
              {feedback.type === 'success' ? (
                <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
              ) : (
                <AlertCircle size={18} className="text-rose-600 flex-shrink-0" />
              )}
              <span>{feedback.message}</span>
            </div>
            <button
              onClick={() => setFeedback(null)}
              className="text-secondary hover:text-foreground p-1"
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* KPI Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div
            onClick={() => setStatusFilter('ALL')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              statusFilter === 'ALL'
                ? 'bg-primary/5 border-primary shadow-sm'
                : 'bg-card border-border hover:border-border/80'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-secondary">মোট অনুরোধ (Total)</span>
              <FileText size={16} className="text-secondary" />
            </div>
            <div className="text-2xl font-bold text-foreground mt-2">{totalCount}</div>
            <div className="text-[11px] text-secondary mt-1">সর্বমোট আবেদনসমূহ</div>
          </div>

          <div
            onClick={() => setStatusFilter('PENDING')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              statusFilter === 'PENDING'
                ? 'bg-amber-500/10 border-amber-500 shadow-sm'
                : 'bg-card border-border hover:border-border/80'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-amber-700">অপেক্ষমাণ (Pending)</span>
              <Clock size={16} className="text-amber-600" />
            </div>
            <div className="text-2xl font-bold text-amber-700 mt-2">{pendingCount}</div>
            <div className="text-[11px] text-amber-600/80 mt-1">পর্যালোচনা আবশ্যক</div>
          </div>

          <div
            onClick={() => setStatusFilter('APPROVED')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              statusFilter === 'APPROVED'
                ? 'bg-emerald-500/10 border-emerald-500 shadow-sm'
                : 'bg-card border-border hover:border-border/80'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-emerald-700">অনুমোদিত (Approved)</span>
              <CheckCircle2 size={16} className="text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-emerald-700 mt-2">{approvedCount}</div>
            <div className="text-[11px] text-emerald-600/80 mt-1">সফলভাবে কার্যকর</div>
          </div>

          <div
            onClick={() => setStatusFilter('REJECTED')}
            className={`p-4 rounded-xl border cursor-pointer transition-all ${
              statusFilter === 'REJECTED'
                ? 'bg-rose-500/10 border-rose-500 shadow-sm'
                : 'bg-card border-border hover:border-border/80'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-rose-700">প্রত্যাখ্যাত (Rejected)</span>
              <XCircle size={16} className="text-rose-600" />
            </div>
            <div className="text-2xl font-bold text-rose-700 mt-2">{rejectedCount}</div>
            <div className="text-[11px] text-rose-600/80 mt-1">বাতিলকৃত অনুরোধ</div>
          </div>
        </div>

        {/* Filters and Search Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-card border border-border p-3 rounded-xl">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
            <input
              type="text"
              placeholder="সদস্যের নাম, মেম্বারশিপ নম্বর বা ফিল্ড দিয়ে খুঁজুন..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-background border border-border rounded-lg text-xs text-foreground placeholder:text-secondary/60 focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
            {(['ALL', 'PENDING', 'APPROVED', 'REJECTED'] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                  statusFilter === st
                    ? 'bg-primary text-white shadow-sm'
                    : 'text-secondary hover:text-foreground hover:bg-muted'
                }`}
              >
                {st === 'ALL' && 'সকল (All)'}
                {st === 'PENDING' && 'অপেক্ষমাণ (Pending)'}
                {st === 'APPROVED' && 'অনুমোদিত (Approved)'}
                {st === 'REJECTED' && 'প্রত্যাখ্যাত (Rejected)'}
              </button>
            ))}
          </div>
        </div>

        {/* Change Requests List */}
        {loading ? (
          <div className="p-12 text-center bg-card border border-border rounded-2xl space-y-3">
            <RefreshCw size={24} className="animate-spin text-primary mx-auto" />
            <p className="text-xs text-secondary font-medium">অনুরোধ তালিকা লোড হচ্ছে...</p>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="p-12 text-center bg-card border border-border rounded-2xl space-y-3">
            <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto text-secondary">
              <FileText size={24} />
            </div>
            <h3 className="text-sm font-semibold text-foreground">কোনো প্রোফাইল পরিবর্তন অনুরোধ পাওয়া যায়নি</h3>
            <p className="text-xs text-secondary max-w-sm mx-auto">
              {searchQuery
                ? 'আপনার সার্চ অনুযায়ী কোনো রেকর্ড মেলেনি।'
                : 'বর্তমানে পর্যালোচনা করার মতো কোনো অনুরোধ অপেক্ষমাণ নেই।'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRequests.map((req) => {
              const fieldMeta = FIELD_LABELS[req.field_name] || {
                bn: req.field_name,
                en: req.field_name,
              };
              const isSelf =
                currentAdmin &&
                (currentAdmin.id === req.user_id ||
                  (currentAdmin.member_id && currentAdmin.member_id === req.member_id));

              return (
                <div
                  key={req.id}
                  className="bg-card border border-border rounded-xl p-5 hover:border-border/80 transition-shadow shadow-sm space-y-4"
                >
                  {/* Top Bar: Member & Status */}
                  <div className="flex flex-wrap items-start justify-between gap-3 pb-3 border-b border-border/60">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-foreground">
                          {req.member_name_bn || req.member_name_en || `Member #${req.member_id}`}
                        </span>
                        {req.member_name_en && req.member_name_bn && (
                          <span className="text-xs text-secondary font-normal">
                            ({req.member_name_en})
                          </span>
                        )}
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-primary/10 text-primary border border-primary/20">
                          {req.membership_id || `ID: ${req.member_id}`}
                        </span>
                        <span className="text-[11px] text-secondary">
                          • অনুরোধ #{req.id}
                        </span>
                      </div>
                      <div className="text-[11px] text-secondary flex items-center gap-2">
                        <Calendar size={12} />
                        <span>
                          জমা দেওয়ার সময়:{' '}
                          {req.created_at
                            ? new Date(req.created_at).toLocaleString('bn-BD', {
                                dateStyle: 'medium',
                                timeStyle: 'short',
                              })
                            : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div className="flex items-center gap-2">
                      {req.status === 'PENDING' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-700 border border-amber-500/20">
                          <Clock size={13} className="text-amber-600" />
                          অপেক্ষমাণ (Pending)
                        </span>
                      )}
                      {req.status === 'APPROVED' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-700 border border-emerald-500/20">
                          <CheckCircle2 size={13} className="text-emerald-600" />
                          অনুমোদিত (Approved)
                        </span>
                      )}
                      {req.status === 'REJECTED' && (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-700 border border-rose-500/20">
                          <XCircle size={13} className="text-rose-600" />
                          প্রত্যাখ্যাত (Rejected)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Field & Value Comparison Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Field Info */}
                    <div className="p-3 bg-muted/40 rounded-lg border border-border/50">
                      <div className="text-[11px] text-secondary font-medium uppercase tracking-wider">
                        সংশোধনযোগ্য সুরক্ষিত তথ্য
                      </div>
                      <div className="text-xs font-bold text-foreground mt-1">
                        {fieldMeta.bn}
                      </div>
                      <div className="text-[11px] text-secondary mt-0.5 font-mono">
                        {fieldMeta.en} ({req.field_name})
                      </div>
                    </div>

                    {/* Current Value */}
                    <div className="p-3 bg-muted/40 rounded-lg border border-border/50">
                      <div className="text-[11px] text-secondary font-medium uppercase tracking-wider">
                        বর্তমান মান (Current)
                      </div>
                      <div className="text-xs font-medium text-secondary mt-1 break-words">
                        {req.current_value || '— (অনির্ধারিত / Not Set)'}
                      </div>
                    </div>

                    {/* Requested Value */}
                    <div className="p-3 bg-primary/5 rounded-lg border border-primary/20">
                      <div className="text-[11px] text-primary font-semibold uppercase tracking-wider">
                        প্রস্তাবিত নতুন মান (Requested)
                      </div>
                      <div className="text-xs font-bold text-foreground mt-1 break-words">
                        {req.requested_value}
                      </div>
                    </div>
                  </div>

                  {/* Justification Reason */}
                  <div className="p-3 bg-muted/30 rounded-lg border border-border/40 text-xs space-y-1">
                    <span className="font-semibold text-foreground">সদস্যের যুক্তি / বিবরণ (Reason):</span>
                    <p className="text-secondary leading-relaxed">{req.reason}</p>
                  </div>

                  {/* Supporting Document & Reviewer Note Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                    <div className="flex items-center gap-3">
                      {req.supporting_doc_url ? (
                        <a
                          href={req.supporting_doc_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary/30 bg-primary/5 text-primary text-xs font-semibold hover:bg-primary/10 transition-colors"
                        >
                          <FileText size={14} />
                          <span>সংযুক্ত ডকুমেন্ট দেখুন (View Document)</span>
                          <ExternalLink size={12} />
                        </a>
                      ) : (
                        <span className="text-xs text-secondary italic">
                          কোনো সহায়ক ডকুমেন্ট সংযুক্ত নেই
                        </span>
                      )}

                      {req.review_note && (
                        <div className="text-xs text-secondary">
                          <span className="font-semibold text-foreground">প্রশাসনিক মন্তব্য:</span>{' '}
                          {req.review_note}
                        </div>
                      )}
                    </div>

                    {/* Actions for PENDING */}
                    {req.status === 'PENDING' && (
                      <div className="flex items-center gap-2">
                        {isSelf ? (
                          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-700 text-xs font-semibold">
                            <ShieldAlert size={14} className="text-amber-600" />
                            <span>স্ব-অনুমোদন নিষিদ্ধ (Self-approval prohibited)</span>
                          </div>
                        ) : (
                          <>
                            <button
                              onClick={() => handleOpenActionModal(req, 'REJECT')}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rose-300 text-rose-700 hover:bg-rose-50 text-xs font-semibold transition-colors"
                            >
                              <X size={14} />
                              <span>প্রত্যাখ্যান (Reject)</span>
                            </button>
                            <button
                              onClick={() => handleOpenActionModal(req, 'APPROVE')}
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-semibold transition-colors shadow-sm"
                            >
                              <Check size={14} />
                              <span>অনুমোদন (Approve)</span>
                            </button>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Review Modal (Approve / Reject) */}
      {selectedRequest && actionType && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in-50 zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                {actionType === 'APPROVE' ? (
                  <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <CheckCircle2 size={18} />
                  </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center">
                    <XCircle size={18} />
                  </div>
                )}
                <div>
                  <h3 className="text-sm font-bold text-foreground">
                    {actionType === 'APPROVE'
                      ? 'প্রোফাইল তথ্য সংশোধন অনুমোদন'
                      : 'প্রোফাইল তথ্য সংশোধন প্রত্যাখ্যান'}
                  </h3>
                  <p className="text-[11px] text-secondary">
                    অনুরোধ #{selectedRequest.id} •{' '}
                    {selectedRequest.member_name_bn || selectedRequest.member_name_en}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                disabled={submittingAction}
                className="text-secondary hover:text-foreground p-1"
              >
                <X size={16} />
              </button>
            </div>

            {/* Change Summary Card */}
            <div className="p-3.5 bg-muted/40 rounded-xl border border-border/60 text-xs space-y-2">
              <div className="flex justify-between items-center text-secondary text-[11px]">
                <span>সংশোধনযোগ্য ফিল্ড:</span>
                <span className="font-semibold text-foreground">
                  {FIELD_LABELS[selectedRequest.field_name]?.bn || selectedRequest.field_name}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border/40">
                <div>
                  <span className="text-[10px] text-secondary uppercase font-semibold">বর্তমান মান:</span>
                  <div className="font-medium text-secondary truncate">
                    {selectedRequest.current_value || '—'}
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-primary uppercase font-semibold">অনুরোধকৃত নতুন মান:</span>
                  <div className="font-bold text-foreground truncate">
                    {selectedRequest.requested_value}
                  </div>
                </div>
              </div>
            </div>

            {/* Reviewer Note Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>
                  প্রশাসনিক মন্তব্য / পর্যালোচনার নোট{' '}
                  {actionType === 'REJECT' && <span className="text-rose-600">* (বাধ্যতামূলক)</span>}
                </span>
                <span className="text-[11px] text-secondary font-normal">
                  {actionType === 'APPROVE' ? 'ঐচ্ছিক' : 'সদস্যের কাছে প্রদর্শিত হবে'}
                </span>
              </label>
              <textarea
                rows={3}
                value={reviewerNote}
                onChange={(e) => setReviewerNote(e.target.value)}
                placeholder={
                  actionType === 'APPROVE'
                    ? 'অনুমোদনের কারণ বা রেফারেন্স নোট লিখুন (ঐচ্ছিক)...'
                    : 'প্রত্যাখ্যানের নির্দিষ্ট কারণ লিখুন (যেমন: অস্পষ্ট জাতীয় পরিচয়পত্রের কপি)...'
                }
                className="w-full p-3 bg-background border border-border rounded-xl text-xs text-foreground placeholder:text-secondary/50 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={handleCloseModal}
                disabled={submittingAction}
                className="px-4 py-2 rounded-xl border border-border text-xs font-medium text-secondary hover:text-foreground hover:bg-muted transition-colors"
              >
                বাতিল করুন
              </button>
              <button
                type="button"
                onClick={handleSubmitAction}
                disabled={submittingAction}
                className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white transition-all shadow-sm ${
                  actionType === 'APPROVE'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-rose-600 hover:bg-rose-700'
                } ${submittingAction ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                {submittingAction ? (
                  <>
                    <RefreshCw size={13} className="animate-spin" />
                    <span>প্রক্রিয়াধীন...</span>
                  </>
                ) : actionType === 'APPROVE' ? (
                  <>
                    <Check size={14} />
                    <span>অনুমোদন নিশ্চিত করুন</span>
                  </>
                ) : (
                  <>
                    <X size={14} />
                    <span>প্রত্যাখ্যান নিশ্চিত করুন</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
