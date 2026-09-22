'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, PublicMember, CircleItem } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { Search, ShieldCheck, MapPin, Briefcase } from 'lucide-react';

export default function PublicMembersPage() {
  const [members, setMembers] = useState<PublicMember[]>([]);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [circleId, setCircleId] = useState<number | undefined>(undefined);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.getCircles().then(setCircles).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api.getMembers({
      q: searchQuery || undefined,
      circle_id: circleId,
      page,
      limit: 20,
    })
      .then((res) => {
        setMembers(res.items);
        setTotal(res.total);
      })
      .catch((err) => {
        console.error('Failed to load public members directory', err);
        setMembers([]);
        setTotal(0);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [circleId, searchQuery, page]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
      {/* Page Header */}
      <div className="border-b border-slate-200 pb-6 mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">সদস্য প্রকৌশলী ডিরেক্টরি</h1>
        <p className="text-slate-600 text-sm md:text-base">
          পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর নিবন্ধিত সদস্য প্রকৌশলীদের প্রাতিষ্ঠানিক তালিকা।
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-8 flex flex-col md:flex-row gap-4 justify-between items-center">
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          <select
            value={circleId || ''}
            onChange={(e) => {
              setCircleId(e.target.value ? Number(e.target.value) : undefined);
              setPage(1);
            }}
            className="px-3.5 py-2 border border-slate-200 rounded-lg text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-600"
          >
            <option value="">সকল গ্রিড সার্কেল</option>
            {circles.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name_bn} ({c.name_en})
              </option>
            ))}
          </select>

          <span className="text-xs text-slate-500 font-medium">
            মোট সক্রিয় সদস্য: {total.toLocaleString('bn-BD')} জন
          </span>
        </div>

        <div className="relative w-full md:w-80">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="নাম, পদবি বা সদস্য আইডি খুঁজুন..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* Members Directory */}
      {loading ? (
        <LoadingState message="সদস্য তালিকা লোড হচ্ছে..." />
      ) : members.length === 0 ? (
        <EmptyState
          icon="👥"
          title="কোনো সদস্য পাওয়া যায়নি"
          description="অনুসন্ধানের ফলাফলে কোনো সক্রিয় সদস্য প্রকৌশলী মিলছে না।"
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {members.map((m) => (
            <div
              key={m.membership_id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm hover:border-emerald-500 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-12 h-12 bg-emerald-50 text-emerald-800 font-bold rounded-full flex items-center justify-center text-lg border border-emerald-100">
                    {m.name_bn ? m.name_bn.charAt(0) : 'প'}
                  </div>
                  <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
                    <ShieldCheck size={12} /> যাচাইকৃত
                  </span>
                </div>

                <h3 className="font-bold text-slate-900 text-base">{m.name_bn}</h3>
                {m.name_en && <p className="text-xs text-slate-500 italic mb-2">{m.name_en}</p>}

                <div className="space-y-1.5 text-xs text-slate-600 mt-3 pt-3 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    <Briefcase size={13} className="text-slate-400 shrink-0" />
                    <span>{m.designation_bn || 'প্রকৌশলী'}</span>
                  </div>
                  {m.circle_name_bn && (
                    <div className="flex items-center gap-1.5">
                      <MapPin size={13} className="text-slate-400 shrink-0" />
                      <span>{m.circle_name_bn}</span>
                    </div>
                  )}
                  <div className="font-mono text-[11px] text-slate-500 pt-1">
                    আইডি: {m.membership_id}
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end">
                <Link
                  href={`/verify?membership_id=${encodeURIComponent(m.membership_id)}`}
                  className="text-xs font-semibold text-emerald-700 hover:underline flex items-center gap-1"
                >
                  ডিজিটাল সার্টিফিকেট যাচাই &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalPages={Math.max(1, Math.ceil(total / 20))}
        onPageChange={(p) => setPage(p)}
      />
    </div>
  );
}
