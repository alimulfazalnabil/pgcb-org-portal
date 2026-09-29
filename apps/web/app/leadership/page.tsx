'use client';

import { useEffect, useState } from 'react';
import { api, CommitteeItem, CircleItem } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { useLanguage } from '../../lib/i18n';

export default function LeadershipPage() {
  const { language, t, pick } = useLanguage();
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
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 mb-3">
          {t('সাংগঠনিক নেতৃত্ব ও কার্যনির্বাহী কমিটি', 'Organizational Leadership & Executive Committee')}
        </h1>
        <p className="text-slate-600 text-sm md:text-base leading-relaxed">
          {t(
            'পাওয়ার গ্রিড প্রকৌশলী সমিতি (পিজিসিবি)-এর কেন্দ্রীয় কার্যনির্বাহী পরিষদ এবং আঞ্চলিক গ্রিড সার্কেল সমূহের দায়িত্বপ্রাপ্ত কর্মকর্তাবৃন্দ।',
            'Central Executive Council and Regional Grid Circle office-bearers of the Power Grid Engineers Association (PGCB).'
          )}
        </p>
      </div>

      {loading ? (
        <LoadingState message={t('কমিটির তথ্য লোড হচ্ছে...', 'Loading committee information...')} />
      ) : (
        <div className="space-y-14">
          {/* Central Executive Committee Section */}
          <section>
            <div className="flex items-center gap-3 border-b-2 border-primary pb-3 mb-8">
              <span className="text-xl sm:text-2xl">🏛️</span>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                {t('কেন্দ্রীয় কার্যনির্বাহী কমিটি', 'Central Executive Committee')}
              </h2>
            </div>

            {centralCommittee.length === 0 ? (
              <EmptyState
                title={t('কোনো তথ্য পাওয়া যায়নি', 'No information found')}
                description={t('বর্তমানে কেন্দ্রীয় কমিটির তথ্য অন্তর্ভুক্ত করা হচ্ছে।', 'Central committee records are currently being updated.')}
              />
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
                    <h3 className="font-bold text-base text-slate-900">
                      {pick(member, 'name', member.name_bn)}
                    </h3>
                    {language === 'bn' && member.name_en && (
                      <p className="text-xs text-slate-500 italic mb-1">{member.name_en}</p>
                    )}
                    <span className="inline-block px-3 py-1 bg-emerald-50 text-emerald-800 text-xs font-semibold rounded-full mt-2 mb-3">
                      {pick(member, 'designation', member.designation_bn)}
                    </span>
                    {member.term_start && member.term_end && (
                      <p className="text-[11px] text-slate-400">
                        {t('মেয়াদ:', 'Term:')} {member.term_start} - {member.term_end}
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
              <span className="text-xl sm:text-2xl">⚡</span>
              <h2 className="text-xl sm:text-2xl font-bold text-slate-900">
                {t('গ্রিড সার্কেল উপ-কমিটি', 'Grid Circle Sub-Committees')}
              </h2>
            </div>

            {/* Circle Selection Pills */}
            <div className="flex flex-wrap gap-2 mb-8">
              {circles.map((circle) => (
                <button
                  key={circle.id}
                  onClick={() => setSelectedCircleId(circle.id)}
                  className={`px-3.5 py-2 rounded-lg text-xs md:text-sm font-semibold transition-all ${
                    selectedCircleId === circle.id
                      ? 'bg-emerald-800 text-white shadow-md'
                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {pick(circle, 'name', circle.name_bn)}
                </button>
              ))}
            </div>

            {loadingCircle ? (
              <LoadingState message={t('সার্কেল কমিটির তথ্য লোড হচ্ছে...', 'Loading circle committee information...')} />
            ) : circleCommittee.length === 0 ? (
              <EmptyState
                icon="👥"
                title={t('সার্কেল কমিটির তালিকা প্রস্তুত হচ্ছে', 'Circle committee list is being prepared')}
                description={t('এই সার্কেলের নবনির্বাচিত কমিটির তালিকা শীঘ্র হালনাগাদ করা হবে।', 'The newly elected committee list for this circle will be updated shortly.')}
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
                    <h4 className="font-bold text-sm text-slate-900">{pick(m, 'name', m.name_bn)}</h4>
                    <p className="text-xs text-emerald-700 font-medium mt-1">{pick(m, 'designation', m.designation_bn)}</p>
                    {m.term_start && (
                      <p className="text-[11px] text-slate-400 mt-2">
                        {t('মেয়াদ:', 'Term:')} {m.term_start} - {m.term_end || t('বর্তমান', 'Present')}
                      </p>
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
