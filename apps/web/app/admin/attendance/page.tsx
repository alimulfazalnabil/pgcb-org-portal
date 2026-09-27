'use client';

import React, { useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import {
  QrCode,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  UserCheck,
  Calendar,
} from 'lucide-react';

export default function AdminAttendancePage() {
  const [ticketInput, setTicketInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    ok: boolean;
    message: string;
    name?: string;
    details?: any;
  } | null>(null);
  const [recentScans, setRecentScans] = useState<any[]>([]);

  const handleCheckIn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketInput.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const res = await api.checkInTicket(ticketInput.trim());
      const scanItem = {
        code: ticketInput.trim(),
        ok: true,
        message: res.message || 'উপস্থিতি সফলভাবে রেকর্ড করা হয়েছে।',
        name: res.participant_name || 'নিবন্ধিত প্রতিনিধি',
        time: new Date().toLocaleTimeString(),
      };
      setResult(scanItem);
      setRecentScans((prev) => [scanItem, ...prev.slice(0, 9)]);
      setTicketInput('');
    } catch (err: any) {
      const scanItem = {
        code: ticketInput.trim(),
        ok: false,
        message: err.message || 'টিকিট যাচাই ব্যর্থ হয়েছে।',
        time: new Date().toLocaleTimeString(),
      };
      setResult(scanItem);
      setRecentScans((prev) => [scanItem, ...prev.slice(0, 9)]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="ইভেন্ট উপস্থিতি ও কিউআর স্ক্যান ডেস্ক (Event Attendance Desk)"
        subtitle="সম্মেলন ও কর্মশালার দিন অংশগ্রহণকারীদের টিকিট কিউআর কোড স্ক্যান ও তাৎক্ষণিক উপস্থিতি নিবন্ধন"
      />

      <div className="p-6 md:p-8 space-y-8 max-w-4xl">
        {/* Scanner Form */}
        <div className="bg-card border border-border p-6 rounded-2xl shadow-sm space-y-5">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
              <QrCode size={24} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-foreground">টিকিট কোড স্ক্যান বা ইনপুট করুন</h2>
              <p className="text-xs text-secondary mt-0.5">
                বারকোড/কিউআর স্ক্যানার দিয়ে স্ক্যান করুন অথবা টিকিটের ইউনিক কোডটি লিখে এন্টার চাপুন
              </p>
            </div>
          </div>

          <form onSubmit={handleCheckIn} className="flex gap-2">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                type="text"
                autoFocus
                placeholder="যেমন: TC-2026-XXXXX অথবা কিউআর স্ক্যান ডেটা..."
                value={ticketInput}
                onChange={(e) => setTicketInput(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-primary font-mono"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !ticketInput.trim()}
              className="px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm shrink-0"
            >
              {loading ? 'যাচাই হচ্ছে...' : 'উপস্থিতি নিশ্চিত করুন'}
            </button>
          </form>

          {/* Real-time Result Callout */}
          {result && (
            <div
              className={`p-4 rounded-xl border flex items-start gap-3 animate-fadeIn text-xs ${
                result.ok
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-800 dark:text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-800 dark:text-rose-300'
              }`}
            >
              {result.ok ? (
                <CheckCircle size={20} className="text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <XCircle size={20} className="text-rose-600 shrink-0 mt-0.5" />
              )}
              <div>
                <div className="font-bold text-sm">
                  {result.ok ? 'বৈধ টিকিট — প্রবেশ অনুমোদিত' : 'টিকিট অবৈধ বা বাতিল'}
                </div>
                <div className="mt-1">{result.message}</div>
                {result.name && (
                  <div className="mt-1 font-semibold text-foreground">অংশগ্রহণকারী: {result.name}</div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Recent Scan History */}
        <div className="bg-card border border-border rounded-2xl p-6 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">
            সর্বশেষ স্ক্যান ইতিহাস (Recent Scans)
          </h3>

          {recentScans.length === 0 ? (
            <p className="text-xs text-secondary py-4 text-center">এখনো কোনো টিকিট স্ক্যান করা হয়নি।</p>
          ) : (
            <div className="divide-y divide-border">
              {recentScans.map((scan, idx) => (
                <div key={idx} className="py-2.5 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    {scan.ok ? (
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                    )}
                    <span className="font-mono font-medium text-foreground">{scan.code}</span>
                    {scan.name && <span className="text-secondary">— {scan.name}</span>}
                  </div>
                  <span className="text-[11px] text-secondary font-mono">{scan.time}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
