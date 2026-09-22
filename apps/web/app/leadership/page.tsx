'use client';

import { useEffect, useState } from 'react';
import { api, CommitteeItem, CircleItem } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { Mail, Phone, MapPin, Award } from 'lucide-react';

export default function LeadershipPage() {
  const [centralCommittee, setCentralCommittee] = useState<CommitteeItem[]>([]);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [selectedCircleId, setSelectedCircleId] = useState<number | null>(null);
  const [circleCommittee, setCircleCommittee] = useState<CommitteeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingCircle, setLoadingCircle] = useState(false);

  useEffect(() => {
    Promise.allSettled([api.getCommittee(), api.getCircles()]).then(([commRes, circleRes]) => {
      if (commRes.status === 'fulfilled') {
        setCentralCommittee(commRes.value);
      }
      if (circleRes.status === 'fulfilled') {
        setCircles(circleRes.value);
        if (circleRes.value.length > 0) {
          setSelectedCircleId(circleRes.value[0].id);
        }
      }
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!selectedCircleId) return;
    setLoadingCircle(true);
    api.getCircleCommittee(selectedCircleId)
      .then((data) => setCircleCommittee(data))
      .catch(() => setCircleCommittee([]))
      .finally(() => setLoadingCircle(false));
  }, [selectedCircleId]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
      <div className="border-b border-slate-200 pb-6 mb-10 text-center max-w-3xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3">সাংগঠনিক নেতৃত্ব ও কার্যনির্বাহী কমিটি</h1>
        <p className="text-slate-600 text-sm md:text-base leading-relaxed">
          পাওয়ার গ্রিড প্রকৌশলী সমিতি (পিজিসিবি)-এর কেন্দ্রীয় কার্যনির্বাহী পরিষদ এবং আঞ্চলিক গ্রিড সার্কেল সমূহের দায়িত্বপ্রাপ্ত কর্মকর্তাবৃন্দ।
        </p>
      </div>

      {loading ? (
        <LoadingState message="কমিটির তথ্য লোড হচ্ছে..." />
      ) : (
        <div className="space-y-16">
          {/* Central Executive Committee Section */}
          <section>
            <div className="flex items-center gap-3 border-b-2 border-primary pb-3 mb-8">
              <span className="text-2xl">🏛️</span>
              <h2 className="text-2xl font-bold text-slate-900">কেন্দ্রীয় কার্যনির্বাহী কমিটি</h2>
            </div>

            {centralCommittee.length === 0 ? (
              <EmptyState title="কোনো তথ্য পাওয়া যায়নি" description="বর্তমানে কেন্দ্রীয় কমিটির তথ্য অন্তর্ভুক্ত করা হচ্ছে।" />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {centralCommittee.map((member) => (
                  <div
                    key={member.id}
                    className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center text-center shadow-sm hover:shadow-md hover:border-emerald-500 transition-all"
                  >
                    <div className="w-24 h-24 rounded-full bg-slate-100 border-2 border-emerald-600 mb-4 overflow-hidden flex items-center justify-center text-3xl shadow-inner">
                      {member.photo_url ? (
                        <img src={member.photo_url} alt={member.name_bn} className="w-full h-full object-cover" />
                      ) : (
                        '👤'
                      )}
                    </div>
                    <h3 className="font-bold text-base text-slate-900">{member.name_bn}</h3>
                    {member.name_en && <p className="text-xs text-slate-500 italic mb-1">{member.name_en}</p>}
                    <span className="inline-block px-3 py-1 bg-emerald-50 text-emerald-800 text-xs font-semibold rounded-full mt-2 mb-3">
                      {member.designation_bn}
                    </span>
                    {member.term_start && member.term_end && (
                      <p className="text-[11px] text-slate-400">
                        মেয়াদ: {member.term_start} - {member.term_end}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Circle Committees Section */}
          <section>
            <div className="flex items-center gap-3 border-b-2 border-primary pb-3 mb-6">
              <span className="text-2xl">⚡</span>
              <h2 className="text-2xl font-bold text-slate-900">গ্রিড সার্কেল উপ-কমিটি</h2>
            </div>

            {/* Circle Selection Pills */}
            <div className="flex flex-wrap gap-2 mb-8">
              {circles.map((circle) => (
                <button
                  key={circle.id}
                  onClick={() => setSelectedCircleId(circle.id)}
                  className={`px-4 py-2 rounded-lg text-xs md:text-sm font-semibold transition-all ${
                    selectedCircleId === circle.id
                      ? 'bg-emerald-800 text-white shadow-md'
                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {circle.name_bn}
                </button>
              ))}
            </div>

            {loadingCircle ? (
              <LoadingState message="সার্কেল কমিটির তথ্য লোড হচ্ছে..." />
            ) : circleCommittee.length === 0 ? (
              <EmptyState
                icon="👥"
                title="সার্কেল কমিটির তালিকা প্রস্তুত হচ্ছে"
                description="এই সার্কেলের নবনির্বাচিত কমিটির তালিকা শীঘ্র হালনাগাদ করা হবে।"
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                {circleCommittee.map((m) => (
                  <div
                    key={m.id}
                    className="bg-white rounded-xl border border-slate-200 p-5 flex flex-col items-center text-center shadow-sm hover:border-emerald-500 transition-all"
                  >
                    <div className="w-20 h-20 rounded-full bg-slate-100 border border-slate-300 mb-3 overflow-hidden flex items-center justify-center text-2xl">
                      {m.photo_url ? (
                        <img src={m.photo_url} alt={m.name_bn} className="w-full h-full object-cover" />
                      ) : (
                        '👤'
                      )}
                    </div>
                    <h4 className="font-bold text-sm text-slate-900">{m.name_bn}</h4>
                    <p className="text-xs text-emerald-700 font-medium mt-1">{m.designation_bn}</p>
                    {m.term_start && (
                      <p className="text-[11px] text-slate-400 mt-2">মেয়াদ: {m.term_start} - {m.term_end || 'বর্তমান'}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
