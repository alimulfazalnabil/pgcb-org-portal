'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import { ShieldAlert, Search, RefreshCw, Calendar, Globe, User } from 'lucide-react';

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs({ limit: 100 });
      setLogs(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <>
      <AdminHeader
        title="নিরাপত্তা ও অপারেশন অডিট লগ (Security Audit Log)"
        subtitle="অপরিবর্তনশীল অডিট ট্রেইল: প্রশাসনিক সিদ্ধান্ত, লগইন, সদস্য অনুমোদন ও সংবেদনশীল পরিবর্তনের রেকর্ড"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        <div className="flex justify-between items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <ShieldAlert size={18} className="text-primary" />
            <span>সর্বশেষ রেকর্ডকৃত অডিট এন্ট্রি ({logs.length}টি)</span>
          </div>

          <button
            onClick={fetchLogs}
            className="px-3 py-1.5 rounded-xl border border-border bg-card hover:bg-surface text-foreground text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs"
          >
            <RefreshCw size={13} /> রিফ্রেশ করুন
          </button>
        </div>

        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">সময় ও তারিখ (UTC)</th>
                  <th className="p-4">অ্যাক্টর (Actor / User)</th>
                  <th className="p-4">অ্যাকশন টাইপ (Action)</th>
                  <th className="p-4">টার্গেট এন্টিটি</th>
                  <th className="p-4">আইপি ঠিকানা (IP)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">অডিট লগ লোড হচ্ছে...</td></tr>
                ) : logs.length === 0 ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">কোনো অডিট রেকর্ড পাওয়া যায়নি।</td></tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-mono text-[11px] text-secondary">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-4 font-bold text-foreground">
                        <div className="flex items-center gap-1.5">
                          <User size={12} className="text-secondary" />
                          <span>{log.actor_email || `User #${log.user_id}`}</span>
                        </div>
                      </td>
                      <td className="p-4 font-mono font-bold text-primary">
                        <span className="px-2 py-0.5 rounded-md bg-primary/10 border border-primary/20 text-[11px]">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 text-secondary">
                        <span className="font-semibold text-foreground">{log.entity_type}</span>
                        {log.entity_id && <span className="font-mono ml-1">#{log.entity_id}</span>}
                      </td>
                      <td className="p-4 font-mono text-[11px] text-secondary">
                        {log.ip_address || '127.0.0.1'}
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
