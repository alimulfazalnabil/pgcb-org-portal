'use client';

import React, { useEffect, useState } from 'react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { StatusBadge } from '@/components/admin/StatusBadge';
import {
  Layers,
  Users,
  Building2,
  MessageSquare,
  Plus,
  CheckCircle2,
} from 'lucide-react';

export default function AdminContentPage() {
  const [committee, setCommittee] = useState<any[]>([]);
  const [circles, setCircles] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'committee' | 'circles' | 'inbox'>('committee');
  const [newCircle, setNewCircle] = useState({ name_bn: '', name_en: '', region_bn: '' });
  const [newCommittee, setNewCommittee] = useState({
    name_bn: '',
    role_bn: '',
    workplace_bn: '',
    session_year: '২০২৫-২০২৭',
    display_order: 10,
  });

  const loadCMSData = async () => {
    setLoading(true);
    try {
      const [comRes, cirRes, msgRes] = await Promise.all([
        fetch('/backend/api/v1/admin/committee').then((r) => (r.ok ? r.json() : [])),
        fetch('/backend/api/v1/admin/circles').then((r) => (r.ok ? r.json() : [])),
        fetch('/backend/api/v1/admin/messages').then((r) => (r.ok ? r.json() : [])),
      ]);
      setCommittee(Array.isArray(comRes) ? comRes : []);
      setCircles(Array.isArray(cirRes) ? cirRes : []);
      setMessages(Array.isArray(msgRes) ? msgRes : []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCMSData();
  }, []);

  const handleAddCircle = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCircle.name_bn.trim()) return;
    const res = await fetch('/backend/api/v1/admin/circles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newCircle, active: true }),
    });
    if (res.ok) {
      setNewCircle({ name_bn: '', name_en: '', region_bn: '' });
      loadCMSData();
    }
  };

  const handleAddCommittee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCommittee.name_bn.trim() || !newCommittee.role_bn.trim()) return;
    const res = await fetch('/backend/api/v1/admin/committee', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...newCommittee, active: true }),
    });
    if (res.ok) {
      setNewCommittee({
        name_bn: '',
        role_bn: '',
        workplace_bn: '',
        session_year: '২০২৫-২০২৭',
        display_order: 10,
      });
      loadCMSData();
    }
  };

  const handleResolveMessage = async (id: number, status: string) => {
    await fetch(`/backend/api/v1/admin/messages/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    loadCMSData();
  };

  return (
    <>
      <AdminHeader
        title="কনটেন্ট ম্যানেজমেন্ট ও সাংগঠনিক কাঠামো (CMS Desk)"
        subtitle="কেন্দ্রীয় কার্যনির্বাহী কমিটি, গ্রিড সার্কেল এবং যোগাযোগ ইনবক্স ব্যবস্থাপনা"
      />

      <div className="p-6 md:p-8 space-y-6 max-w-7xl">
        {/* Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-border pb-3">
          <button
            onClick={() => setActiveTab('committee')}
            className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
              activeTab === 'committee'
                ? 'bg-primary text-white'
                : 'bg-card border border-border text-secondary hover:text-foreground'
            }`}
          >
            <Users size={15} /> কার্যনির্বাহী কমিটি ({committee.length})
          </button>
          <button
            onClick={() => setActiveTab('circles')}
            className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
              activeTab === 'circles'
                ? 'bg-primary text-white'
                : 'bg-card border border-border text-secondary hover:text-foreground'
            }`}
          >
            <Building2 size={15} /> গ্রিড সার্কেলসমূহ ({circles.length})
          </button>
          <button
            onClick={() => setActiveTab('inbox')}
            className={`px-4 py-2 rounded-xl text-xs font-bold inline-flex items-center gap-2 transition-all ${
              activeTab === 'inbox'
                ? 'bg-primary text-white'
                : 'bg-card border border-border text-secondary hover:text-foreground'
            }`}
          >
            <MessageSquare size={15} /> যোগাযোগ বার্তা ({messages.length})
          </button>
        </div>

        {activeTab === 'committee' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <form
              onSubmit={handleAddCommittee}
              className="bg-card border border-border rounded-2xl p-5 space-y-3 h-fit shadow-sm"
            >
              <h3 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Plus size={15} className="text-primary" /> নতুন কমিটি সদস্য যুক্ত করুন
              </h3>
              <input
                type="text"
                required
                placeholder="সদস্যের নাম (বাংলায়) *"
                value={newCommittee.name_bn}
                onChange={(e) => setNewCommittee({ ...newCommittee, name_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                required
                placeholder="সাংগঠনিক পদবী (যেমন: সভাপতি / সাধারণ সম্পাদক) *"
                value={newCommittee.role_bn}
                onChange={(e) => setNewCommittee({ ...newCommittee, role_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="কর্মস্থল / দপ্তর"
                value={newCommittee.workplace_bn}
                onChange={(e) => setNewCommittee({ ...newCommittee, workplace_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-primary text-white text-xs font-bold"
              >
                কমিটিতে যুক্ত করুন
              </button>
            </form>

            <div className="lg:col-span-2 bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="p-4">নাম</th>
                    <th className="p-4">সাংগঠনিক পদবী</th>
                    <th className="p-4">কর্মস্থল</th>
                    <th className="p-4">সেশন</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {committee.map((m) => (
                    <tr key={m.id}>
                      <td className="p-4 font-bold text-foreground">{m.name_bn}</td>
                      <td className="p-4 text-primary font-semibold">{m.role_bn}</td>
                      <td className="p-4 text-secondary">{m.workplace_bn || 'কেন্দ্রীয় দপ্তর'}</td>
                      <td className="p-4 font-mono text-[11px] text-secondary">{m.session_year}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'circles' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <form
              onSubmit={handleAddCircle}
              className="bg-card border border-border rounded-2xl p-5 space-y-3 h-fit shadow-sm"
            >
              <h3 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Plus size={15} className="text-primary" /> নতুন গ্রিড সার্কেল যুক্ত করুন
              </h3>
              <input
                type="text"
                required
                placeholder="সার্কেলের নাম (বাংলায়) *"
                value={newCircle.name_bn}
                onChange={(e) => setNewCircle({ ...newCircle, name_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="সার্কেলের নাম (ইংরেজিতে)"
                value={newCircle.name_en}
                onChange={(e) => setNewCircle({ ...newCircle, name_en: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <input
                type="text"
                placeholder="অঞ্চল (Region)"
                value={newCircle.region_bn}
                onChange={(e) => setNewCircle({ ...newCircle, region_bn: e.target.value })}
                className="w-full px-3 py-2 rounded-xl border border-border bg-surface text-xs"
              />
              <button
                type="submit"
                className="w-full py-2.5 rounded-xl bg-primary text-white text-xs font-bold"
              >
                সার্কেল সংরক্ষণ করুন
              </button>
            </form>

            <div className="lg:col-span-2 bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px]">
                  <tr>
                    <th className="p-4">সার্কেল নাম (বাংলা)</th>
                    <th className="p-4">সার্কেল নাম (ইংরেজি)</th>
                    <th className="p-4">অঞ্চল</th>
                    <th className="p-4">স্ট্যাটাস</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {circles.map((c) => (
                    <tr key={c.id}>
                      <td className="p-4 font-bold text-foreground">{c.name_bn}</td>
                      <td className="p-4 text-secondary">{c.name_en || '—'}</td>
                      <td className="p-4 text-secondary">{c.region_bn || 'জাতীয় গ্রিড'}</td>
                      <td className="p-4">
                        <StatusBadge status={c.active ? 'ACTIVE' : 'ARCHIVED'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'inbox' && (
          <div className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface/80 border-b border-border text-secondary font-semibold uppercase text-[10px]">
                <tr>
                  <th className="p-4">প্রেরক</th>
                  <th className="p-4">বিষয় ও বার্তা</th>
                  <th className="p-4">স্ট্যাটাস</th>
                  <th className="p-4 text-right">পদক্ষেপ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {messages.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-secondary">
                      কোনো বার্তা পাওয়া যায়নি।
                    </td>
                  </tr>
                ) : (
                  messages.map((msg) => (
                    <tr key={msg.id}>
                      <td className="p-4">
                        <div className="font-bold text-foreground">{msg.name}</div>
                        <div className="text-[11px] text-secondary">{msg.email}</div>
                      </td>
                      <td className="p-4 max-w-md">
                        <div className="font-bold text-foreground">{msg.subject}</div>
                        <div className="text-secondary text-[11px] mt-0.5">{msg.message}</div>
                      </td>
                      <td className="p-4">
                        <StatusBadge status={msg.status} />
                      </td>
                      <td className="p-4 text-right">
                        {msg.status !== 'RESOLVED' && (
                          <button
                            onClick={() => handleResolveMessage(msg.id, 'RESOLVED')}
                            className="px-3 py-1 rounded-lg bg-emerald-600 text-white font-bold text-[11px] inline-flex items-center gap-1"
                          >
                            <CheckCircle2 size={12} /> সমাধানকৃত
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
