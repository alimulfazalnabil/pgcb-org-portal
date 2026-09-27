'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import {
  Award,
  Plus,
  XCircle,
  Download,
  AlertTriangle,
  FileDown,
} from 'lucide-react';

export default function AdminCertificatesPage() {
  const [certificates, setCertificates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [revokeModal, setRevokeModal] = useState<any | null>(null);
  const [revokeReason, setRevokeReason] = useState('');
  const [issueModal, setIssueModal] = useState(false);
  const [issueForm, setIssueForm] = useState({
    recipient_name: '',
    certificate_type: 'MEMBERSHIP',
    recipient_user_id: '',
  });
  const [actionBusy, setActionBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchCertificates = async () => {
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/admin/certificates').then((r) => r.json());
      setCertificates(Array.isArray(res) ? res : []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCertificates();
  }, []);

  const handleIssue = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!issueForm.recipient_name.trim()) return;
    setActionBusy(true);
    try {
      const payload: Record<string, any> = {
        recipient_name: issueForm.recipient_name.trim(),
        certificate_type: issueForm.certificate_type,
      };
      if (issueForm.recipient_user_id.trim()) {
        payload.recipient_user_id = Number(issueForm.recipient_user_id.trim());
      }
      const res = await fetch('/backend/api/v1/admin/certificates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('নতুন সনদ প্রস্তুত করা সম্ভব হয়নি।');
      setMessage({ text: 'নতুন ডিজিটাল সনদ সফলভাবে ইস্যু করা হয়েছে।', type: 'success' });
      setIssueModal(false);
      setIssueForm({ recipient_name: '', certificate_type: 'MEMBERSHIP', recipient_user_id: '' });
      fetchCertificates();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setActionBusy(false);
    }
  };

  const handleRevoke = async () => {
    if (!revokeModal || !revokeReason.trim()) return;
    setActionBusy(true);
    try {
      const res = await fetch(`/backend/api/v1/admin/certificates/${revokeModal.id}/revoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: revokeReason.trim() }),
      });
      if (!res.ok) throw new Error('সার্টিফিকেট বাতিল করা সম্ভব হয়নি।');
      setMessage({ text: 'সার্টিফিকেট সফলভাবে বাতিল করা হয়েছে।', type: 'success' });
      setRevokeModal(null);
      setRevokeReason('');
      fetchCertificates();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="সার্টিফিকেট ও সনদপত্র ব্যবস্থাপনা (Certificates Desk)"
        subtitle="সদস্যপদ সনদ, বার্ষিক সম্মেলন ও প্রশিক্ষণ সার্টিফিকেট ইস্যু, যাচাইকরণ এবং বাতিলকরণ"
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

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between items-stretch sm:items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <Award size={18} className="text-primary" />
            <span>ইস্যুকৃত সনদের তালিকা ({certificates.length}টি)</span>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="/backend/api/v1/admin/exports/certificates.csv"
              className="px-3.5 py-2 rounded-xl border border-border bg-surface hover:bg-card text-foreground text-xs font-bold transition-all inline-flex items-center gap-1.5"
            >
              <FileDown size={14} /> CSV এক্সপোর্ট
            </a>
            <button
              onClick={() => setIssueModal(true)}
              className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm shrink-0"
            >
              <Plus size={14} /> নতুন সনদ প্রস্তুত করুন
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">সার্টিফিকেট নম্বর (Serial / Token)</th>
                  <th className="p-4">গ্রহীতা / সদস্য</th>
                  <th className="p-4">ধরন (Type)</th>
                  <th className="p-4">ইস্যুর তারিখ</th>
                  <th className="p-4">স্ট্যাটাস</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      সার্টিফিকেট তালিকা লোড হচ্ছে...
                    </td>
                  </tr>
                ) : certificates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-secondary">
                      এখনো কোনো সার্টিফিকেট ইস্যু করা হয়নি।
                    </td>
                  </tr>
                ) : (
                  certificates.map((cert) => (
                    <tr key={cert.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-mono font-medium text-foreground">
                        {cert.certificate_number || cert.certificate_no || cert.token}
                      </td>
                      <td className="p-4 font-bold text-foreground">
                        {cert.recipient_name || cert.recipient_name_bn || 'সদস্য'}
                      </td>
                      <td className="p-4 text-secondary">
                        {cert.title_bn || cert.certificate_type || 'MEMBERSHIP'}
                      </td>
                      <td className="p-4 text-secondary font-mono text-[11px]">
                        {cert.issue_date || cert.created_at?.slice(0, 10)}
                      </td>
                      <td className="p-4">
                        <StatusBadge status={cert.status || 'ISSUED'} />
                      </td>
                      <td className="p-4 text-right space-x-2">
                        {cert.pdf_path && (
                          <a
                            href={`/backend/api/v1/certificates/${cert.token || cert.certificate_no}/download`}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2.5 py-1 rounded-lg border border-border bg-surface hover:bg-card text-primary font-semibold text-[11px] inline-flex items-center gap-1"
                          >
                            <Download size={12} /> PDF
                          </a>
                        )}
                        {cert.status !== 'REVOKED' && (
                          <button
                            onClick={() => setRevokeModal(cert)}
                            className="px-2.5 py-1 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 font-semibold text-[11px] inline-flex items-center gap-1"
                          >
                            <XCircle size={12} /> বাতিল
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Issue Certificate Modal */}
      {issueModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <form
            onSubmit={handleIssue}
            className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4"
          >
            <div className="flex items-center gap-2.5 text-primary">
              <Award size={20} />
              <h3 className="text-sm font-bold text-foreground">নতুন ডিজিটাল সনদ ইস্যু করুন</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-secondary mb-1">
                  গ্রহীতার নাম (Recipient Name) *
                </label>
                <input
                  type="text"
                  required
                  value={issueForm.recipient_name}
                  onChange={(e) => setIssueForm({ ...issueForm, recipient_name: e.target.value })}
                  placeholder="যেমন: প্রকৌ. মোঃ রাশেদুল ইসলাম"
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-secondary mb-1">
                  সনদের ধরন (Certificate Type)
                </label>
                <select
                  value={issueForm.certificate_type}
                  onChange={(e) => setIssueForm({ ...issueForm, certificate_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
                >
                  <option value="MEMBERSHIP">সদস্যপদ সনদ (Membership Certificate)</option>
                  <option value="EVENT_PARTICIPATION">ইভেন্ট ও সম্মেলন সনদ (Event Participation)</option>
                  <option value="TRAINING_EXCELLENCE">কারিগরি প্রশিক্ষণ সনদ (Technical Training)</option>
                  <option value="HONORARY_AWARD">বিশেষ সম্মাননা সনদ (Honorary Award)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-secondary mb-1">
                  ব্যবহারকারী আইডি (Optional User ID)
                </label>
                <input
                  type="number"
                  value={issueForm.recipient_user_id}
                  onChange={(e) => setIssueForm({ ...issueForm, recipient_user_id: e.target.value })}
                  placeholder="ঐচ্ছিক User ID"
                  className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIssueModal(false)}
                className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
              >
                বাতিল
              </button>
              <button
                type="submit"
                disabled={actionBusy || !issueForm.recipient_name.trim()}
                className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold disabled:opacity-50"
              >
                {actionBusy ? 'প্রস্তুত হচ্ছে...' : 'সনদ ইস্যু করুন'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Revocation Modal */}
      {revokeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4">
            <div className="flex items-center gap-2.5 text-rose-600">
              <AlertTriangle size={20} />
              <h3 className="text-sm font-bold text-foreground">সার্টিফিকেট বাতিলের কারণ উল্লেখ করুন</h3>
            </div>
            <p className="text-xs text-secondary leading-relaxed">
              সনদপত্র নং{' '}
              <span className="font-mono font-bold text-foreground">
                {revokeModal.certificate_number || revokeModal.certificate_no || revokeModal.token}
              </span>{' '}
              বাতিল করলে কিউআর ভেরিফিকেশনে এটি তাৎক্ষণিকভাবে &apos;REVOKED&apos; হিসেবে প্রদর্শিত হবে।
            </p>
            <textarea
              required
              rows={3}
              placeholder="বাতিলকরণের প্রাতিষ্ঠানিক কারণ লিখুন (যেমন: তথ্যে ত্রুটি বা সদস্যপদ স্থগিত)..."
              value={revokeReason}
              onChange={(e) => setRevokeReason(e.target.value)}
              className="w-full p-3 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-rose-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setRevokeModal(null)}
                className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface text-xs font-semibold"
              >
                বাতিল
              </button>
              <button
                disabled={actionBusy || !revokeReason.trim()}
                onClick={handleRevoke}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold disabled:opacity-50"
              >
                {actionBusy ? 'বাতিল হচ্ছে...' : 'সনদ বাতিল নিশ্চিত করুন'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
