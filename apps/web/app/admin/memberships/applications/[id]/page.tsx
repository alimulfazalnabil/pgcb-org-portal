'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import { api } from '@/lib/api';
import {
  ArrowLeft,
  User,
  Briefcase,
  Building2,
  FileText,
  CreditCard,
  History,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  MessageSquarePlus,
  Download,
  Award,
  Check,
  X,
} from 'lucide-react';

export default function AdminApplicationReviewDetailPage() {
  const params = useParams();
  const memberId = Number(params?.id);

  const [detail, setDetail] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [selectedCircleId, setSelectedCircleId] = useState<string>('');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadDetail = async () => {
    if (!memberId) return;
    setLoading(true);
    try {
      const data = await api.getMembershipApplicationDetail(memberId);
      setDetail(data);
      setSelectedCircleId(data.circle_id ? String(data.circle_id) : '');
    } catch (err: any) {
      setMessage({
        text: err.message || 'আবেদনের বিস্তারিত তথ্য লোড করা যায়নি।',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [memberId]);

  const runAction = async (
    action:
      | 'APPROVE'
      | 'REQUEST_CORRECTION'
      | 'REJECT'
      | 'UNDER_REVIEW'
      | 'ASSIGN_CIRCLE'
      | 'ADD_NOTE',
    extra?: { circle_id?: number; customNote?: string }
  ) => {
    if (!memberId) return;
    setBusy(true);
    setMessage(null);
    try {
      const resolvedNote = extra?.customNote ?? (noteText.trim() || undefined);
      const res = await api.executeApplicationAction(memberId, {
        action,
        note: resolvedNote,
        circle_id: extra?.circle_id,
        require_payment: true,
      });
      setMessage({
        text: `কার্যক্রম সম্পন্ন হয়েছে (${action}) — বর্তমান স্ট্যাটাস: ${res.status}`,
        type: 'success',
      });
      if (action === 'ADD_NOTE') {
        setNoteText('');
      }
      await loadDetail();
    } catch (err: any) {
      setMessage({
        text: err.message || 'প্রশাসনিক পদক্ষেপ সম্পন্ন করা যায়নি।',
        type: 'error',
      });
    } finally {
      setBusy(false);
    }
  };

  const handleDocReview = async (docId: number, action: 'APPROVE' | 'REJECT') => {
    setBusy(true);
    try {
      await api.reviewDocument(docId, action);
      setMessage({
        text: `নথি যাচাই সম্পন্ন হয়েছে (${action})।`,
        type: 'success',
      });
      await loadDetail();
    } catch (err: any) {
      setMessage({
        text: err.message || 'নথি যাচাই করা যায়নি।',
        type: 'error',
      });
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-secondary">
        আবেদনকারীর বিস্তারিত তথ্য ও পর্যালোচনা ইতিহাস লোড হচ্ছে...
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-8 space-y-4">
        <p className="text-xs text-rose-600 font-semibold">আবেদন খুঁজে পাওয়া যায়নি।</p>
        <Link
          href="/admin/memberships/applications"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
        >
          <ArrowLeft size={14} /> তালিকায় ফিরে যান
        </Link>
      </div>
    );
  }

  const personal = detail.personal_information || {};
  const professional = detail.professional_information || {};
  const gridCircle = detail.grid_circle || {};
  const availableCircles: { id: number; name_bn: string; name_en?: string }[] =
    gridCircle.available_circles || [];
  const docs: any[] = detail.uploaded_documents || detail.documents || [];
  const paymentInfo = detail.payment || {};
  const transactions: any[] = paymentInfo.transactions || detail.payments || [];
  const appReviews: any[] = detail.application_reviews || [];
  const auditHistory: any[] = detail.review_history || [];

  return (
    <>
      <AdminHeader
        title={`আবেদন পর্যালোচনা: ${detail.name_bn || detail.name_en}`}
        subtitle={`Application No: ${detail.application_no} • বর্তমান স্ট্যাটাস: ${detail.status}`}
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Back Link & Status Banner */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/admin/memberships/applications"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-border bg-card hover:bg-surface text-xs font-semibold text-foreground shadow-xs"
          >
            <ArrowLeft size={14} /> সকল সদস্যপদ আবেদন (Back to Applications)
          </Link>

          <div className="flex items-center gap-3">
            <span className="text-xs text-secondary font-medium">আবেদন স্ট্যাটাস:</span>
            <StatusBadge status={detail.status} />
            {detail.membership_id && (
              <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 font-mono text-xs font-bold">
                ID: {detail.membership_id}
              </span>
            )}
          </div>
        </div>

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

        {/* Admin Actions Control Bar */}
        <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex flex-col lg:flex-row gap-4 lg:items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-foreground">
                প্রশাসনিক সিদ্ধান্ত ও নোট (Admin Review Actions)
              </h3>
              <p className="text-xs text-secondary mt-0.5">
                প্রতিটি সিদ্ধান্ত স্বয়ংক্রিয়ভাবে অডিট লগ এবং রিভিউ হিস্টোরিতে সংরক্ষিত হবে। অনুমোদন করলে পেমেন্ট-পেন্ডিং স্টেটে যাবে।
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <button
                disabled={busy}
                onClick={() => runAction('APPROVE')}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold inline-flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
              >
                <CheckCircle2 size={14} /> Approve (অনুমোদন)
              </button>

              <button
                disabled={busy}
                onClick={() => runAction('REQUEST_CORRECTION')}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold inline-flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
              >
                <AlertTriangle size={14} /> Request Correction (সংশোধন অনুরোধ)
              </button>

              <button
                disabled={busy}
                onClick={() => runAction('REJECT')}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold inline-flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
              >
                <XCircle size={14} /> Reject (প্রত্যাখ্যান)
              </button>
            </div>
          </div>

          {/* Note Input + Add Internal Note */}
          <div className="flex flex-col sm:flex-row gap-2.5 pt-2 border-t border-border">
            <input
              type="text"
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="পর্যালোচনা মন্তব্য বা অভ্যন্তরীণ নোট লিখুন (Internal Note / Correction Reason)..."
              className="flex-1 px-3.5 py-2 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-primary"
            />
            <button
              disabled={busy || !noteText.trim()}
              onClick={() => runAction('ADD_NOTE')}
              className="px-4 py-2 rounded-xl border border-border bg-surface hover:bg-card text-foreground text-xs font-bold inline-flex items-center gap-1.5 shrink-0 disabled:opacity-50"
            >
              <MessageSquarePlus size={14} /> Add Internal Note (নোট যুক্ত করুন)
            </button>
          </div>
        </div>

        {/* 7-Section Review Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Personal Information */}
          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
              <User size={15} className="text-primary" /> ১. ব্যক্তিগত তথ্য (Personal Information)
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-secondary text-[11px]">নাম (বাংলা):</div>
                <div className="font-bold text-foreground">{personal.name_bn || detail.name_bn || '—'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">নাম (ইংরেজি):</div>
                <div className="font-semibold text-foreground">{personal.name_en || detail.name_en || '—'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">ইমেইল:</div>
                <div className="font-medium text-foreground">{personal.email || detail.email || '—'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">মোবাইল নম্বর:</div>
                <div className="font-medium text-foreground">{personal.phone || detail.phone || '—'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">জাতীয় পরিচয়পত্র (NID):</div>
                <div className="font-mono text-foreground">{personal.nid_number || detail.nid_number || '—'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">বর্তমান ঠিকানা:</div>
                <div className="text-foreground">{personal.current_address || detail.current_address || '—'}</div>
              </div>
            </div>
          </div>

          {/* 2. Professional Information */}
          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
              <Briefcase size={15} className="text-primary" /> ২. পেশাগত তথ্য (Professional Information)
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-secondary text-[11px]">পিজিসিবি এমপ্লয়ি আইডি:</div>
                <div className="font-mono font-bold text-foreground">
                  {professional.employee_id || detail.employee_id || '—'}
                </div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">পদবী (বাংলা):</div>
                <div className="font-bold text-foreground">
                  {professional.designation_bn || detail.designation_bn || '—'}
                </div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">পদবী (ইংরেজি):</div>
                <div className="text-foreground">
                  {professional.designation_en || detail.designation_en || '—'}
                </div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">ডিপ্লোমা প্রতিষ্ঠান ও সাল:</div>
                <div className="text-foreground">
                  {professional.diploma_institution || detail.diploma_institution || '—'}{' '}
                  {professional.graduation_year ? `(${professional.graduation_year})` : ''}
                </div>
              </div>
            </div>
          </div>

          {/* 3. Grid Circle & Assign Circle */}
          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
              <Building2 size={15} className="text-primary" /> ৩. গ্রিড সার্কেল (Grid Circle Assignment)
            </h4>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between bg-surface/60 p-3 rounded-xl border border-border">
                <span className="text-secondary">বর্তমান গ্রিড সার্কেল:</span>
                <span className="font-bold text-foreground">
                  {gridCircle.circle_bn || detail.circle_bn || 'অনির্ধারিত'}{' '}
                  {gridCircle.circle_en ? `(${gridCircle.circle_en})` : ''}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <select
                  aria-label="Assign Grid Circle"
                  value={selectedCircleId}
                  onChange={(e) => setSelectedCircleId(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-xl border border-border bg-surface text-xs font-semibold text-foreground"
                >
                  <option value="">গ্রিড সার্কেল নির্বাচন করুন...</option>
                  {availableCircles.map((c) => (
                    <option key={c.id} value={String(c.id)}>
                      {c.name_bn} {c.name_en ? `(${c.name_en})` : ''}
                    </option>
                  ))}
                </select>
                <button
                  disabled={busy || !selectedCircleId}
                  onClick={() =>
                    runAction('ASSIGN_CIRCLE', { circle_id: Number(selectedCircleId) })
                  }
                  className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50"
                >
                  Assign Circle
                </button>
              </div>
            </div>
          </div>

          {/* 4. Membership Type & Status */}
          <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
              <Award size={15} className="text-primary" /> ৪. সদস্যপদের ধরন (Membership Type)
            </h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <div className="text-secondary text-[11px]">সদস্যপদের ধরন:</div>
                <div className="font-bold text-foreground">{detail.membership_type || 'GENERAL'}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">আবেদন নম্বর:</div>
                <div className="font-mono font-bold text-foreground">{detail.application_no}</div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">সদস্য আইডি (Membership ID):</div>
                <div className="font-mono font-bold text-emerald-600">
                  {detail.membership_id || 'অপেক্ষমাণ (Issued on Payment Activation)'}
                </div>
              </div>
              <div>
                <div className="text-secondary text-[11px]">সর্বশেষ পর্যালোচনা নোট:</div>
                <div className="text-foreground">{detail.application_note || '—'}</div>
              </div>
            </div>
          </div>
        </div>

        {/* 5. Uploaded Documents Review */}
        <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
            <FileText size={15} className="text-primary" /> ৫. দাখিলকৃত নথিপত্র যাচাই (Uploaded Documents)
          </h4>
          {docs.length === 0 ? (
            <p className="text-xs text-secondary italic">কোনো নথিপত্র আপলোড করা হয়নি।</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="p-3.5 rounded-xl border border-border bg-surface/60 flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="font-bold text-foreground">
                      {doc.document_type} — {doc.filename}
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <StatusBadge status={doc.review_status} />
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      disabled={busy}
                      onClick={() => handleDocReview(doc.id, 'APPROVE')}
                      title="Approve Document"
                      className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/20 border border-emerald-500/20"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => handleDocReview(doc.id, 'REJECT')}
                      title="Reject Document"
                      className="p-1.5 rounded-lg bg-rose-500/10 text-rose-700 hover:bg-rose-500/20 border border-rose-500/20"
                    >
                      <X size={14} />
                    </button>
                    <a
                      href={`/backend/api/v1/admin/documents/${doc.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1.5 rounded-lg border border-border bg-card hover:bg-surface font-semibold text-primary inline-flex items-center gap-1"
                    >
                      <Download size={13} /> ডাউনলোড
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 6. Payment Information */}
        <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
              <CreditCard size={15} className="text-primary" /> ৬. পেমেন্ট ও লেনদেন (Payment Status)
            </h4>
            <StatusBadge status={paymentInfo.payment_status || 'UNPAID'} />
          </div>
          {transactions.length === 0 ? (
            <p className="text-xs text-secondary italic">
              এখনো কোনো পেমেন্ট লেনদেন সম্পন্ন হয়নি। আবেদন অনুমোদন (Approve) করলে সদস্য পেমেন্ট রিকোয়েস্ট পাবেন।
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface/80 border-b border-border text-secondary uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Transaction Ref</th>
                    <th className="p-3">Provider</th>
                    <th className="p-3">Amount</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Receipt / Invoice</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {transactions.map((tx) => (
                    <tr key={tx.id}>
                      <td className="p-3 font-mono font-semibold">{tx.transaction_ref || `#${tx.id}`}</td>
                      <td className="p-3">{tx.provider}</td>
                      <td className="p-3 font-bold">৳{tx.amount}</td>
                      <td className="p-3">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="p-3 font-mono text-[11px]">
                        {tx.receipt_no || tx.invoice_number || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* 7. Review History & Audit Trail */}
        <div className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-secondary flex items-center gap-2">
            <History size={15} className="text-primary" /> ৭. পর্যালোচনা ইতিহাস ও অডিট ট্রেইল (Review History & Audit Trail)
          </h4>
          {appReviews.length === 0 && auditHistory.length === 0 ? (
            <p className="text-xs text-secondary italic">কোনো পর্যালোচনা ইতিহাস পাওয়া যায়নি।</p>
          ) : (
            <div className="space-y-2.5">
              {appReviews.map((rev) => (
                <div
                  key={`rev-${rev.id}`}
                  className="p-3.5 rounded-xl border border-border bg-surface/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                >
                  <div>
                    <div className="font-bold text-foreground">
                      {rev.action}{' '}
                      <span className="text-secondary font-normal">
                        ({rev.previous_status || '—'} → {rev.new_status})
                      </span>
                    </div>
                    {rev.note && <div className="text-secondary mt-0.5">{rev.note}</div>}
                  </div>
                  <div className="text-right text-[11px] text-secondary">
                    <div className="font-semibold text-foreground">
                      {rev.reviewer_name} ({rev.reviewer_role})
                    </div>
                    <div>{rev.created_at ? new Date(rev.created_at).toLocaleString() : ''}</div>
                  </div>
                </div>
              ))}
              {auditHistory.map((log) => (
                <div
                  key={`aud-${log.id}`}
                  className="p-3 rounded-xl border border-border/60 bg-surface/20 flex items-center justify-between text-xs"
                >
                  <div>
                    <span className="font-mono font-bold text-primary">{log.action}</span>
                    <span className="text-secondary ml-2">by {log.reviewer_name}</span>
                  </div>
                  <div className="text-[11px] text-secondary">
                    {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
