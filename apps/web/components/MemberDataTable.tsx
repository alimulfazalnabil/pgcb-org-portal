'use client';

import { useState, useMemo } from 'react';
import { 
  Search, 
  RefreshCw, 
  Download, 
  Upload,
  Check, 
  X, 
  Eye, 
  FileText, 
  ShieldCheck, 
  User, 
  AlertCircle,
  Clock,
  CheckCircle2
} from 'lucide-react';
import { api } from '@/lib/api';

export interface MemberRecord {
  id: number;
  membership_id: string | null;
  name_bn: string;
  name_en?: string | null;
  email: string;
  phone?: string | null;
  employee_id?: string | null;
  designation_bn?: string | null;
  designation_en?: string | null;
  circle_bn?: string | null;
  status: string;
  created_at: string;
  validity_date?: string | null;
}

export interface MemberDetailRecord extends MemberRecord {
  user_id?: number;
  application_note?: string | null;
  diploma_institution?: string | null;
  graduation_year?: number | string | null;
  nid_number?: string | null;
  date_of_birth?: string | null;
  current_address?: string | null;
  permanent_address?: string | null;
  documents?: {
    id: number;
    document_type: string;
    filename: string;
    review_status: string;
    created_at: string;
  }[];
}

interface MemberDataTableProps {
  members: MemberRecord[];
  onRefresh: () => void;
  onMemberAction: (id: number, action: string) => Promise<void>;
  onReviewDoc: (id: number, action: string) => Promise<void>;
  apiBase?: string;
}

export function MemberDataTable({
  members,
  onRefresh,
  onMemberAction,
  onReviewDoc,
  apiBase = '/backend/api/v1'
}: MemberDataTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedMember, setSelectedMember] = useState<MemberDetailRecord | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);

  // CSV Import States
  const [showImportModal, setShowImportModal] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [previewResult, setPreviewResult] = useState<{
    total_rows: number;
    valid_count: number;
    error_count: number;
    rows: any[];
  } | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [commitLoading, setCommitLoading] = useState(false);
  const [commitResult, setCommitResult] = useState<{
    ok: boolean;
    imported_count: number;
    skipped_count: number;
    message: string;
  } | null>(null);

  const handleFilePreview = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImportFile(file);
    setPreviewLoading(true);
    setCommitResult(null);
    try {
      const res = await api.previewMemberImport(file);
      setPreviewResult(res);
    } catch (err: any) {
      alert(err.message || 'CSV প্রিভিউ ব্যর্থ হয়েছে।');
    } finally {
      setPreviewLoading(false);
      e.target.value = '';
    }
  };

  const handleCommitImport = async () => {
    if (!previewResult || !previewResult.rows) return;
    const validRows = previewResult.rows.filter((r) => r.is_valid).map((r) => r.parsed_data);
    if (validRows.length === 0) {
      alert('ইমপোর্ট করার মতো কোনো বৈধ সারি পাওয়া যায়নি।');
      return;
    }
    setCommitLoading(true);
    try {
      const res = await api.commitMemberImport(validRows);
      setCommitResult(res);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'সদস্য ইমপোর্ট ব্যর্থ হয়েছে।');
    } finally {
      setCommitLoading(false);
    }
  };

  // Status Filter options
  const statusTabs = [
    { label: 'সকল আবেদন (All)', value: 'ALL' },
    { label: 'নতুন জমা (Submitted)', value: 'SUBMITTED' },
    { label: 'পর্যালোচনাধীন (In Review)', value: 'UNDER_REVIEW' },
    { label: 'অনুমোদিত (Active)', value: 'ACTIVE' },
    { label: 'প্রত্যাখ্যাত (Rejected)', value: 'REJECTED' },
    { label: 'স্থগিত (Suspended)', value: 'SUSPENDED' },
  ];

  // Filtered members list
  const filteredMembers = useMemo(() => {
    return members.filter((m) => {
      // Status matching
      if (statusFilter !== 'ALL') {
        if (statusFilter === 'SUBMITTED' && !['SUBMITTED', 'PENDING'].includes(m.status)) return false;
        if (statusFilter !== 'SUBMITTED' && m.status !== statusFilter) return false;
      }
      // Query matching
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchNameBn = m.name_bn?.toLowerCase().includes(q);
        const matchNameEn = m.name_en?.toLowerCase().includes(q);
        const matchEmail = m.email?.toLowerCase().includes(q);
        const matchPhone = m.phone?.toLowerCase().includes(q);
        const matchMemberId = m.membership_id?.toLowerCase().includes(q);
        const matchEmpId = m.employee_id?.toLowerCase().includes(q);
        return matchNameBn || matchNameEn || matchEmail || matchPhone || matchMemberId || matchEmpId;
      }
      return true;
    });
  }, [members, statusFilter, searchQuery]);

  // Counts for tabs
  const pendingCount = useMemo(() => {
    return members.filter(m => ['SUBMITTED', 'PENDING', 'UNDER_REVIEW'].includes(m.status)).length;
  }, [members]);

  const openMemberDetail = async (id: number) => {
    setLoadingDetail(true);
    try {
      const res = await fetch(`${apiBase}/admin/members/${id}`);
      if (res.ok) {
        setSelectedMember(await res.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleAction = async (id: number, action: string) => {
    setActionBusy(true);
    try {
      await onMemberAction(id, action);
      if (selectedMember && selectedMember.id === id) {
        // Refresh details
        const res = await fetch(`${apiBase}/admin/members/${id}`);
        if (res.ok) {
          setSelectedMember(await res.json());
        }
      }
    } finally {
      setActionBusy(false);
    }
  };

  const handleDocReview = async (docId: number, action: string) => {
    try {
      await onReviewDoc(docId, action);
      if (selectedMember) {
        setSelectedMember({
          ...selectedMember,
          documents: selectedMember.documents?.map(d => 
            d.id === docId ? { ...d, review_status: action } : d
          )
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">সক্রিয় (Active)</span>;
      case 'SUBMITTED':
      case 'PENDING':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">অপেক্ষমাণ (Submitted)</span>;
      case 'UNDER_REVIEW':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">পর্যালোচনাধীন (In Review)</span>;
      case 'REJECTED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">প্রত্যাখ্যাত (Rejected)</span>;
      case 'SUSPENDED':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-300">স্থগিত (Suspended)</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-surface text-secondary">{status}</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Controls & Filter Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-background p-4 rounded-xl border border-border">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-success">MEMBERSHIP OPERATIONS</span>
          <h2 className="text-2xl font-bold text-primary dark:text-white flex items-center gap-2">
            সদস্য আবেদন ও রেজিস্ট্রি
            {pendingCount > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-accent text-primary">
                {pendingCount} টি অপেক্ষমাণ
              </span>
            )}
          </h2>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={onRefresh}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-md border border-border bg-surface hover:bg-border/50 text-primary transition-colors"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <a
            href={`${apiBase}/admin/exports/members.csv`}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-md border border-border bg-surface hover:bg-border/50 text-primary transition-colors"
          >
            <Download size={14} /> Export CSV
          </a>
          <button
            onClick={() => {
              setShowImportModal(true);
              setPreviewResult(null);
              setCommitResult(null);
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-md bg-primary text-white hover:opacity-90 transition-opacity"
          >
            <Upload size={14} /> Import CSV
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-border">
        {statusTabs.map(tab => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              statusFilter === tab.value
                ? 'bg-primary text-white shadow-sm'
                : 'bg-surface hover:bg-border/50 text-secondary'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-secondary" size={18} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="নাম, PGCB Employee ID, ইমেইল, মোবাইল বা সদস্য ID দিয়ে খুঁজুন..."
          className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm focus:ring-2 focus:ring-accent outline-none transition-all"
        />
      </div>

      {/* Main Data Table */}
      <div className="overflow-x-auto rounded-xl border border-border bg-background shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-surface border-b border-border text-xs uppercase font-semibold text-secondary">
            <tr>
              <th className="py-3 px-4">Member ID</th>
              <th className="py-3 px-4">প্রকৌশলীর বিবরণ (Engineer)</th>
              <th className="py-3 px-4">Employee ID</th>
              <th className="py-3 px-4">পদবী (Designation)</th>
              <th className="py-3 px-4">গ্রিড সার্কেল</th>
              <th className="py-3 px-4">আবেদনের তারিখ</th>
              <th className="py-3 px-4">স্ট্যাটাস (Status)</th>
              <th className="py-3 px-4 text-right">কার্যক্রম (Actions)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredMembers.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-secondary">
                  <User className="mx-auto mb-2 text-secondary opacity-40" size={36} />
                  কোনো সদস্য রেকর্ড পাওয়া যায়নি।
                </td>
              </tr>
            ) : (
              filteredMembers.map((m) => (
                <tr key={m.id} className="hover:bg-surface/50 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-xs text-primary dark:text-white">
                    {m.membership_id || '—'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="font-semibold text-primary dark:text-white">
                      {m.name_bn}
                    </div>
                    <div className="text-xs text-secondary">
                      {m.email} {m.phone ? `· ${m.phone}` : ''}
                    </div>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-secondary font-medium">
                    {m.employee_id || '—'}
                  </td>
                  <td className="py-3 px-4 text-xs font-medium text-secondary">
                    {m.designation_en || m.designation_bn || '—'}
                  </td>
                  <td className="py-3 px-4 text-xs font-medium text-secondary">
                    {m.circle_bn || '—'}
                  </td>
                  <td className="py-3 px-4 text-xs text-secondary">
                    {m.created_at ? new Date(m.created_at).toLocaleDateString('bn-BD') : '—'}
                  </td>
                  <td className="py-3 px-4">
                    {getStatusBadge(m.status)}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="inline-flex items-center gap-1.5 justify-end">
                      <button
                        onClick={() => openMemberDetail(m.id)}
                        className="p-1.5 rounded-md hover:bg-border/60 text-secondary hover:text-primary transition-colors"
                        title="বিস্তারিত দেখুন"
                      >
                        <Eye size={16} />
                      </button>

                      {m.status !== 'ACTIVE' && (
                        <button
                          disabled={actionBusy}
                          onClick={() => handleAction(m.id, 'APPROVE')}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
                          title="আবেদন অনুমোদন করুন"
                        >
                          <Check size={13} /> Approve
                        </button>
                      )}

                      {['SUBMITTED', 'PENDING'].includes(m.status) && (
                        <button
                          disabled={actionBusy}
                          onClick={() => handleAction(m.id, 'REVIEW')}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
                          title="পর্যালোচনাতে পাঠান"
                        >
                          <Clock size={13} /> Review
                        </button>
                      )}

                      {!['ACTIVE', 'REJECTED'].includes(m.status) && (
                        <button
                          disabled={actionBusy}
                          onClick={() => handleAction(m.id, 'REJECT')}
                          className="p-1.5 rounded-md hover:bg-rose-100 text-rose-600 hover:text-rose-800 transition-colors"
                          title="প্রত্যাখ্যান করুন"
                        >
                          <X size={16} />
                        </button>
                      )}

                      {m.status === 'ACTIVE' && (
                        <button
                          disabled={actionBusy}
                          onClick={() => handleAction(m.id, 'SUSPEND')}
                          className="px-2 py-1 rounded bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold transition-colors disabled:opacity-50"
                          title="সদস্যপদ স্থগিত করুন"
                        >
                          Suspend
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Member Details Drawer / Modal */}
      {selectedMember && (
        <div 
          className="fixed inset-0 bg-black/50 z-50 flex justify-end"
          onClick={() => setSelectedMember(null)}
        >
          <div 
            className="w-full max-w-2xl bg-background h-full shadow-2xl overflow-y-auto p-6 md:p-8 space-y-6 animate-in slide-in-from-right duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex justify-between items-start border-b border-border pb-4">
              <div>
                <span className="text-xs font-bold text-success uppercase">APPLICATION REVIEW</span>
                <h3 className="text-2xl font-bold text-primary dark:text-white mt-1">
                  {selectedMember.name_bn}
                </h3>
                {selectedMember.name_en && (
                  <p className="text-sm text-secondary">{selectedMember.name_en}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedMember(null)}
                className="p-2 rounded-full hover:bg-surface text-secondary"
              >
                <X size={20} />
              </button>
            </div>

            {/* Status & ID Summary */}
            <div className="flex items-center justify-between p-4 bg-surface rounded-xl border border-border">
              <div>
                <span className="text-xs text-secondary font-semibold">বর্তমান স্ট্যাটাস</span>
                <div className="mt-1">{getStatusBadge(selectedMember.status)}</div>
              </div>
              <div className="text-right">
                <span className="text-xs text-secondary font-semibold">Membership ID</span>
                <div className="text-base font-bold font-mono text-primary dark:text-white mt-0.5">
                  {selectedMember.membership_id || 'অনুমোদনের পর তৈরি হবে'}
                </div>
              </div>
            </div>

            {/* Member Information Grid */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-primary dark:text-white border-b border-border pb-1">
                প্রকৌশলীর পরিচিতি ও তথ্য
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">PGCB Employee ID</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.employee_id || '—'}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">পদবী (Designation)</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.designation_en || selectedMember.designation_bn || '—'}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">অফিসিয়াল ইমেইল</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.email}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">মোবাইল নম্বর</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.phone || '—'}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">গ্রিড সার্কেল</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.circle_bn || '—'}</p>
                </div>
                <div className="p-3 rounded-lg bg-surface border border-border">
                  <span className="text-secondary font-semibold">ডিপ্লোমা প্রতিষ্ঠান</span>
                  <p className="font-bold text-primary text-sm mt-0.5">{selectedMember.diploma_institution || '—'}</p>
                </div>
              </div>
            </div>

            {/* Document Verification Section */}
            <div className="space-y-3">
              <h4 className="text-sm font-bold text-primary dark:text-white border-b border-border pb-1 flex items-center gap-1.5">
                <FileText size={16} /> সংযুক্ত নথিপত্র (Uploaded Documents)
              </h4>
              <div className="space-y-2">
                {selectedMember.documents && selectedMember.documents.length > 0 ? (
                  selectedMember.documents.map((doc) => (
                    <div 
                      key={doc.id} 
                      className="flex items-center justify-between p-3 rounded-lg border border-border bg-surface"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded bg-primary/10 text-primary">
                          <FileText size={18} />
                        </div>
                        <div>
                          <div className="font-semibold text-xs text-primary dark:text-white">
                            {doc.document_type} — {doc.filename}
                          </div>
                          <div className="text-[11px] text-secondary">
                            Status: <span className="font-bold">{doc.review_status}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <a
                          href={`${apiBase}/admin/documents/${doc.id}/download`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded border border-border text-xs font-semibold hover:bg-border/50 text-primary transition-colors"
                        >
                          View
                        </a>
                        <button
                          onClick={() => handleDocReview(doc.id, 'APPROVED')}
                          className="p-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white"
                          title="নথি অনুমোদন করুন"
                        >
                          <Check size={14} />
                        </button>
                        <button
                          onClick={() => handleDocReview(doc.id, 'REJECTED')}
                          className="p-1 rounded bg-rose-600 hover:bg-rose-700 text-white"
                          title="নথি প্রত্যাখ্যান করুন"
                        >
                          <X size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-4 rounded-lg bg-surface border border-border text-center text-xs text-secondary">
                    কোনো নথি সংযুক্ত করা হয়নি।
                  </div>
                )}
              </div>
            </div>

            {/* Digital ID Card Section for Active Members */}
            {selectedMember.status === 'ACTIVE' && selectedMember.membership_id && (
              <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 flex items-center justify-between flex-wrap gap-3">
                <div>
                  <span className="text-xs font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider">OFFICIAL DIGITAL ID</span>
                  <p className="text-xs text-secondary mt-0.5">মুদ্রণযোগ্য পরিচয়পত্র ও কিউআর যাচাইপত্র ডাউনলোড করুন</p>
                </div>
                <div className="flex items-center gap-2">
                  <a 
                    href={`${apiBase}/member/cards/${selectedMember.id}/png`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary/90 transition-colors inline-flex items-center gap-1.5 shadow-sm"
                  >
                    <Download size={13} /> PNG Card
                  </a>
                  <a 
                    href={`${apiBase}/member/cards/${selectedMember.id}/pdf`} 
                    target="_blank" 
                    rel="noreferrer"
                    className="px-3 py-1.5 rounded-lg bg-surface border border-border text-primary dark:text-white text-xs font-bold hover:bg-border/60 transition-colors inline-flex items-center gap-1.5 shadow-sm"
                  >
                    <Download size={13} /> PDF Document
                  </a>
                </div>
              </div>
            )}

            {/* Modal Decision Actions */}
            <div className="pt-4 border-t border-border flex justify-end gap-3 flex-wrap">
              {selectedMember.status !== 'ACTIVE' && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedMember.id, 'APPROVE')}
                  className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-bold shadow-md transition-colors disabled:opacity-50 inline-flex items-center gap-1.5"
                >
                  <ShieldCheck size={16} /> চূড়ান্ত অনুমোদন (Approve)
                </button>
              )}

              {['SUBMITTED', 'PENDING'].includes(selectedMember.status) && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedMember.id, 'REVIEW')}
                  className="px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-colors disabled:opacity-50"
                >
                  পর্যালোচনাধীন রাখুন (Review)
                </button>
              )}

              {!['ACTIVE', 'REJECTED'].includes(selectedMember.status) && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedMember.id, 'REJECT')}
                  className="px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-sm font-bold transition-colors disabled:opacity-50"
                >
                  প্রত্যাখ্যান (Reject)
                </button>
              )}

              {selectedMember.status === 'ACTIVE' && (
                <button
                  disabled={actionBusy}
                  onClick={() => handleAction(selectedMember.id, 'SUSPEND')}
                  className="px-4 py-2.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold transition-colors disabled:opacity-50"
                >
                  সদস্যপদ স্থগিত (Suspend)
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CSV Batch Import Modal */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-border flex items-center justify-between bg-surface/50">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                  <Upload size={20} />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-foreground">সদস্য বাল্ক ইমপোর্ট (CSV Batch Import)</h3>
                  <p className="text-xs text-secondary">
                    CSV ফাইলের মাধ্যমে একাধিক প্রকৌশলী/সদস্যের তথ্য একবারে সিস্টেমে যুক্ত করুন
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowImportModal(false)}
                className="p-2 rounded-lg text-secondary hover:text-foreground hover:bg-surface transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6">
              {commitResult ? (
                <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-3">
                  <div className="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto">
                    <CheckCircle2 size={24} />
                  </div>
                  <h4 className="text-lg font-bold text-emerald-800 dark:text-emerald-300">ইমপোর্ট সম্পন্ন হয়েছে!</h4>
                  <p className="text-sm text-emerald-700 dark:text-emerald-400 font-medium">{commitResult.message}</p>
                  <div className="flex justify-center gap-4 text-xs font-semibold text-secondary pt-2">
                    <span>সফলভাবে যুক্ত: {commitResult.imported_count} জন</span>
                    <span>বাদ দেওয়া হয়েছে: {commitResult.skipped_count} জন</span>
                  </div>
                </div>
              ) : (
                <>
                  {/* File Upload Area */}
                  <div className="border-2 border-dashed border-border hover:border-primary/50 rounded-2xl p-6 text-center bg-surface/30 transition-all">
                    <Upload className="mx-auto text-secondary mb-2" size={36} />
                    <p className="text-sm font-semibold text-foreground">সদস্য তালিকা সম্বলিত .csv ফাইল নির্বাচন করুন</p>
                    <p className="text-xs text-secondary mt-1">
                      কলামসমূহ: name_bn, name_en, email, phone, employee_id, designation_bn, diploma_institution, graduation_year, nid_number, circle_id
                    </p>
                    <label className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 cursor-pointer shadow-sm">
                      ফাইল বাছাই করুন
                      <input type="file" accept=".csv,text/csv" hidden onChange={handleFilePreview} />
                    </label>
                  </div>

                  {previewLoading && (
                    <div className="py-8 text-center text-sm text-secondary">
                      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent mb-2"></div>
                      <p>CSV ফাইল যাচাই ও প্রিভিউ প্রস্তুত করা হচ্ছে...</p>
                    </div>
                  )}

                  {/* Preview Table */}
                  {previewResult && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 rounded-xl bg-surface border border-border">
                        <div className="text-sm font-bold text-foreground">যাচাইয়ের ফলাফল:</div>
                        <div className="flex items-center gap-3 text-xs font-bold">
                          <span className="px-2.5 py-1 rounded-full bg-surface border border-border text-foreground">
                            মোট সারি: {previewResult.total_rows}
                          </span>
                          <span className="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600">
                            বৈধ: {previewResult.valid_count}
                          </span>
                          <span className="px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-600">
                            ত্রুটিযুক্ত: {previewResult.error_count}
                          </span>
                        </div>
                      </div>

                      <div className="overflow-x-auto max-h-60 rounded-xl border border-border">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-surface/80 text-secondary uppercase font-bold sticky top-0">
                            <tr>
                              <th className="py-2.5 px-3">#</th>
                              <th className="py-2.5 px-3">নাম (বাংলা)</th>
                              <th className="py-2.5 px-3">ইমেইল</th>
                              <th className="py-2.5 px-3">সদস্য আইডি</th>
                              <th className="py-2.5 px-3">অবস্থা</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {previewResult.rows.map((row: any) => (
                              <tr key={row.row_num} className={row.is_valid ? 'bg-background' : 'bg-rose-500/5'}>
                                <td className="py-2 px-3 font-mono">{row.row_num}</td>
                                <td className="py-2 px-3 font-semibold text-foreground">{row.name_bn || '—'}</td>
                                <td className="py-2 px-3 text-secondary">{row.email}</td>
                                <td className="py-2 px-3 font-mono">{row.membership_id || 'Auto'}</td>
                                <td className="py-2 px-3">
                                  {row.is_valid ? (
                                    <span className="text-emerald-600 font-bold inline-flex items-center gap-1">
                                      <Check size={14} /> সঠিক
                                    </span>
                                  ) : (
                                    <span className="text-rose-600 font-bold" title={row.errors.join(', ')}>
                                      ✕ {row.errors.join('; ')}
                                    </span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border flex justify-end gap-3 bg-surface/50">
              <button
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 rounded-xl border border-border bg-card hover:bg-surface text-foreground text-xs font-semibold"
              >
                {commitResult ? 'বন্ধ করুন' : 'বাতিল'}
              </button>
              {previewResult && !commitResult && (
                <button
                  disabled={commitLoading || previewResult.valid_count === 0}
                  onClick={handleCommitImport}
                  className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm flex items-center gap-1.5"
                >
                  {commitLoading ? 'ইমপোর্ট হচ্ছে...' : `${previewResult.valid_count} জন সদস্য যুক্ত করুন`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MemberDataTable;
