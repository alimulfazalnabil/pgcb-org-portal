'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import {
  CreditCard,
  CheckCircle2,
  XCircle,
  RotateCcw,
  FileDown,
  Search,
} from 'lucide-react';

export default function AdminPaymentsPage() {
  const [payments, setPayments] = useState<any[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [purposeFilter, setPurposeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const loadPayments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (purposeFilter) params.set('purpose', purposeFilter);

      const res = await fetch(`/backend/api/v1/admin/payments?${params.toString()}`);
      const data = res.ok ? await res.json() : [];
      setPayments(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
  }, [statusFilter, purposeFilter]);

  const updatePaymentStatus = async (paymentId: number, status: string) => {
    try {
      const res = await fetch(`/backend/api/v1/admin/payments/${paymentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error('পেমেন্ট স্ট্যাটাস আপডেট করা যায়নি।');
      setMessage({ text: `পেমেন্ট #${paymentId} স্ট্যাটাস '${status}'-এ আপডেট হয়েছে।`, type: 'success' });
      loadPayments();
    } catch (err: any) {
      setMessage({ text: err.message, type: 'error' });
    }
  };

  const filtered = payments.filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      String(p.id).includes(q) ||
      (p.transaction_ref || '').toLowerCase().includes(q) ||
      (p.provider || '').toLowerCase().includes(q) ||
      (p.purpose || '').toLowerCase().includes(q)
    );
  });

  const totalPaid = payments
    .filter((p) => p.status === 'PAID')
    .reduce((acc, cur) => acc + Number(cur.amount || 0), 0);

  return (
    <>
      <AdminHeader
        title="আর্থিক লেনদেন ও পেমেন্ট যাচাইকরণ (Financial Ledger)"
        subtitle="সদস্যপদ চাঁদা, নবায়ন ফি এবং ইভেন্ট নিবন্ধন পেমেন্ট সমন্বয় ও অডিট"
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
            <button onClick={() => setMessage(null)}>✕</button>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
            <span className="text-xs text-secondary font-semibold">মোট লেনদেন সংখ্যা</span>
            <div className="text-2xl font-extrabold text-foreground">{payments.length}টি</div>
          </div>
          <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
            <span className="text-xs text-secondary font-semibold">নিশ্চিতকৃত আদায় (PAID)</span>
            <div className="text-2xl font-extrabold text-emerald-600">৳ {totalPaid.toLocaleString()}</div>
          </div>
          <div className="bg-card border border-border rounded-2xl p-5 space-y-1 shadow-sm">
            <span className="text-xs text-secondary font-semibold">অপেক্ষমাণ যাচাই (PENDING)</span>
            <div className="text-2xl font-extrabold text-amber-600">
              {payments.filter((p) => p.status === 'PENDING').length}টি
            </div>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-card border border-border rounded-2xl p-4 flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between shadow-sm">
          <div className="flex flex-wrap gap-3 flex-1">
            <div className="relative flex-1 min-w-[200px]">
              <Search size={15} className="absolute left-3 top-2.5 text-secondary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="ট্রানজেকশন রেফারেন্স বা আইডি খুঁজুন..."
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
            >
              <option value="">সকল স্ট্যাটাস</option>
              <option value="PENDING">PENDING</option>
              <option value="PAID">PAID</option>
              <option value="FAILED">FAILED</option>
              <option value="REFUNDED">REFUNDED</option>
            </select>

            <select
              value={purposeFilter}
              onChange={(e) => setPurposeFilter(e.target.value)}
              className="px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground"
            >
              <option value="">সকল খাত (All Purposes)</option>
              <option value="MEMBERSHIP">MEMBERSHIP</option>
              <option value="EVENT">EVENT</option>
            </select>
          </div>

          <a
            href="/backend/api/v1/admin/exports/payments.csv"
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold inline-flex items-center justify-center gap-1.5 shrink-0"
          >
            <FileDown size={14} /> পেমেন্ট CSV এক্সপোর্ট
          </a>
        </div>

        {/* Payments Table */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">ট্রানজেকশন রেফারেন্স</th>
                  <th className="p-4">খাত (Purpose)</th>
                  <th className="p-4">পরিমাণ (Amount)</th>
                  <th className="p-4">মাধ্যম (Provider)</th>
                  <th className="p-4">স্ট্যাটাস</th>
                  <th className="p-4">তারিখ</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-secondary">
                      পেমেন্ট লেজার লোড হচ্ছে...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-secondary">
                      কোনো আর্থিক লেনদেন রেকর্ড পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  filtered.map((p) => (
                    <tr key={p.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-mono font-bold text-foreground">
                        {p.transaction_ref || `TXN-${p.id}`}
                      </td>
                      <td className="p-4 font-semibold text-foreground">{p.purpose}</td>
                      <td className="p-4 font-mono font-bold text-primary">
                        {p.amount} {p.currency || 'BDT'}
                      </td>
                      <td className="p-4 text-secondary">{p.provider || 'MANUAL'}</td>
                      <td className="p-4">
                        <StatusBadge status={p.status} />
                      </td>
                      <td className="p-4 font-mono text-[11px] text-secondary">
                        {p.created_at?.slice(0, 10)}
                      </td>
                      <td className="p-4 text-right space-x-1.5">
                        {p.status !== 'PAID' && (
                          <button
                            onClick={() => updatePaymentStatus(p.id, 'PAID')}
                            className="px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-bold text-[11px] inline-flex items-center gap-1"
                          >
                            <CheckCircle2 size={12} /> পরিশোধিত (Approve)
                          </button>
                        )}
                        {p.status === 'PENDING' && (
                          <button
                            onClick={() => updatePaymentStatus(p.id, 'FAILED')}
                            className="px-2.5 py-1 rounded-lg border border-rose-200 text-rose-600 hover:bg-rose-50 font-semibold text-[11px] inline-flex items-center gap-1"
                          >
                            <XCircle size={12} /> বাতিল
                          </button>
                        )}
                        {p.status === 'PAID' && (
                          <button
                            onClick={() => updatePaymentStatus(p.id, 'REFUNDED')}
                            className="px-2.5 py-1 rounded-lg border border-border text-secondary hover:text-foreground font-semibold text-[11px] inline-flex items-center gap-1"
                          >
                            <RotateCcw size={12} /> রিফান্ড
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
    </>
  );
}
