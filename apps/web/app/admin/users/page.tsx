'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { api } from '@/lib/api';
import { Users, Plus, ShieldCheck, UserPlus, CheckCircle, XCircle } from 'lucide-react';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const [formData, setFormData] = useState({
    name_bn: '',
    name_en: '',
    email: '',
    phone: '',
    role: 'CONTENT_EDITOR',
    password: '',
    is_active: true,
  });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await api.getUsers();
      setUsers(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.createUser(formData);
      setMessage({ text: 'নতুন স্টাফ ব্যবহারকারী সফলভাবে তৈরি হয়েছে।', type: 'success' });
      setCreateModal(false);
      setFormData({
        name_bn: '',
        name_en: '',
        email: '',
        phone: '',
        role: 'CONTENT_EDITOR',
        password: '',
        is_active: true,
      });
      fetchUsers();
    } catch (err: any) {
      setMessage({ text: err.message || 'তৈরি করা সম্ভব হয়নি।', type: 'error' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <AdminHeader
        title="ব্যবহারকারী ও অ্যাক্সেস নিয়ন্ত্রণ (Staff & RBAC Users)"
        subtitle="সিস্টেম অ্যাডমিন, এডিটর, মেম্বারশিপ অফিসার এবং অডিটর অ্যাকাউন্ট ব্যবস্থাপনা"
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
            <button onClick={() => setMessage(null)} className="opacity-70 hover:opacity-100">✕</button>
          </div>
        )}

        <div className="flex justify-between items-center bg-card border border-border p-4 rounded-2xl shadow-sm">
          <div className="text-xs font-bold text-foreground flex items-center gap-2">
            <Users size={18} className="text-primary" />
            <span>সিস্টেম স্টাফ তালিকা ({users.length} জন)</span>
          </div>

          <button
            onClick={() => setCreateModal(true)}
            className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
          >
            <UserPlus size={14} /> নতুন কর্মকর্তা যুক্ত করুন
          </button>
        </div>

        <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-4">কর্মকর্তার নাম</th>
                  <th className="p-4">ইমেইল ঠিকানা</th>
                  <th className="p-4">নিযুক্ত রোল (RBAC Role)</th>
                  <th className="p-4">অ্যাকাউন্ট স্থিতি</th>
                  <th className="p-4">তৈরির তারিখ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {loading ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">ব্যবহারকারী লোড হচ্ছে...</td></tr>
                ) : users.length === 0 ? (
                  <tr><td colSpan={5} className="p-8 text-center text-secondary">কোনো ব্যবহারকারী পাওয়া যায়নি।</td></tr>
                ) : (
                  users.map((u) => (
                    <tr key={u.id} className="hover:bg-surface/40 transition-colors">
                      <td className="p-4 font-bold text-foreground">{u.name_bn || u.name_en || 'কর্মকর্তা'}</td>
                      <td className="p-4 font-mono text-[11px] text-foreground">{u.email}</td>
                      <td className="p-4">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                          {u.role}
                        </span>
                      </td>
                      <td className="p-4">
                        {u.is_active ? (
                          <span className="text-emerald-600 font-semibold flex items-center gap-1">
                            <CheckCircle size={12} /> সক্রিয়
                          </span>
                        ) : (
                          <span className="text-rose-600 font-semibold flex items-center gap-1">
                            <XCircle size={12} /> নিষ্ক্রিয়
                          </span>
                        )}
                      </td>
                      <td className="p-4 font-mono text-[11px] text-secondary">
                        {u.created_at?.slice(0, 10)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {createModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-card border border-border w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-4 text-xs">
            <h3 className="text-sm font-bold text-foreground">নতুন স্টাফ বা কর্মকর্তা অ্যাকাউন্ট</h3>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="font-semibold text-foreground">পূর্ণ নাম (বাংলা) *</label>
                <input
                  required
                  type="text"
                  placeholder="যেমন: প্রকৌ. নাজমুল হুদা"
                  value={formData.name_bn}
                  onChange={(e) => setFormData({ ...formData, name_bn: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">অফিসিয়াল ইমেইল *</label>
                <input
                  required
                  type="email"
                  placeholder="nazmul@pgcb.org.bd"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">প্রাথমিক পাসওয়ার্ড (কমপক্ষে ৮ অক্ষর) *</label>
                <input
                  required
                  type="password"
                  minLength={8}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="font-semibold text-foreground">দায়িত্ব ও রোল (RBAC Role) *</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full p-2.5 rounded-xl border border-border bg-surface text-foreground focus:outline-none focus:border-primary"
                >
                  <option value="CONTENT_EDITOR">কনটেন্ট এডিটর (Content Editor)</option>
                  <option value="MEMBERSHIP_OFFICER">মেম্বারশিপ অফিসার (Membership Officer)</option>
                  <option value="CIRCLE_ADMIN">সার্কেল অ্যাডমিন (Circle Admin)</option>
                  <option value="FINANCE_OFFICER">অর্থ ও হিসাব কর্মকর্তা (Finance Officer)</option>
                  <option value="AUDITOR">নিরীক্ষক (Auditor - Read Only)</option>
                  <option value="SUPER_ADMIN">সিস্টেম অ্যাডমিনিস্ট্রেটর (Super Admin)</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateModal(false)}
                  className="px-4 py-2 rounded-xl border border-border text-foreground hover:bg-surface"
                >
                  বাতিল
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="px-5 py-2 rounded-xl bg-primary text-white font-bold disabled:opacity-50"
                >
                  {busy ? 'তৈরি হচ্ছে...' : 'অ্যাকাউন্ট নিশ্চিত করুন'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
