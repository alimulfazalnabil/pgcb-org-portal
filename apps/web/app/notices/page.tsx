'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, Notice } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { Search, Pin, AlertCircle, Calendar } from 'lucide-react';
import { useLanguage } from '../../lib/i18n';

const CATEGORIES = [
  { labelBn: 'সকল ক্যাটাগরি', labelEn: 'All Categories', value: '' },
  { labelBn: 'সাধারণ', labelEn: 'General', value: 'GENERAL' },
  { labelBn: 'জরুরী', labelEn: 'Urgent', value: 'URGENT' },
  { labelBn: 'সার্কুলার', labelEn: 'Circular', value: 'CIRCULAR' },
  { labelBn: 'ইভেন্ট', labelEn: 'Event', value: 'EVENT' },
  { labelBn: 'কল্যাণমূলক', labelEn: 'Welfare', value: 'WELFARE' },
  { labelBn: 'পরীক্ষা', labelEn: 'Exam', value: 'EXAM' },
];

export default function NoticesPage() {
  const { t, pick, formatDate } = useLanguage();
  const [notices, setNotices] = useState<Notice[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setLoading(true);
    api.getNotices({
      category: category || undefined,
      page,
      limit: 12,
    })
      .then((data) => {
        setNotices(data);
      })
      .catch((err) => {
        console.error('Failed to load notices', err);
        setNotices([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [category, page]);

  const filteredNotices = notices.filter((n) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      n.title_bn.toLowerCase().includes(q) ||
      (n.title_en && n.title_en.toLowerCase().includes(q)) ||
      n.content_bn.toLowerCase().includes(q) ||
      (n.content_en && n.content_en.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6 mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-2">
          {t('অফিসিয়াল নোটিশ বোর্ড', 'Official Notice Board')}
        </h1>
        <p className="text-slate-600 text-sm md:text-base">
          {t(
            'পাওয়ার গ্রিড প্রকৌশলী সমিতি ও পিজিসিবি সংক্রান্ত সকল বিজ্ঞপ্তি, প্রেস রিলিজ ও প্রাতিষ্ঠানিক নোটিশ।',
            'All official announcements, press releases, and institutional notices of the Power Grid Engineers Association and PGCB.'
          )}
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-8">
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              onClick={() => {
                setCategory(c.value);
                setPage(1);
              }}
              className={`px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all ${
                category === c.value
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {t(c.labelBn, c.labelEn)}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-72">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder={t('নোটিশ খুঁজুন...', 'Search notices...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <LoadingState message={t('নোটিশসমূহ লোড হচ্ছে...', 'Loading notices...')} />
      ) : filteredNotices.length === 0 ? (
        <EmptyState
          icon="📭"
          title={t('কোনো নোটিশ পাওয়া যায়নি', 'No notices found')}
          description={t(
            'আপনার নির্বাচিত ক্যাটাগরি বা সার্চ কিওয়ার্ডের সাথে মিল রেখে কোনো নোটিশ নেই।',
            'No notices match your selected category or search keyword.'
          )}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotices.map((n) => (
            <div
              key={n.id}
              className={`bg-white rounded-xl border p-5 flex flex-col justify-between shadow-sm hover:shadow-md transition-all ${
                n.is_pinned ? 'border-amber-300 ring-1 ring-amber-200' : 'border-slate-200 hover:border-emerald-500'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-1.5">
                    {n.is_pinned && (
                      <span className="flex items-center gap-1 bg-amber-100 text-amber-800 text-[11px] font-bold px-2 py-0.5 rounded">
                        <Pin size={10} /> {t('পিন করা', 'Pinned')}
                      </span>
                    )}
                    {n.priority === 'URGENT' && (
                      <span className="flex items-center gap-1 bg-red-100 text-red-700 text-[11px] font-bold px-2 py-0.5 rounded">
                        <AlertCircle size={10} /> {t('জরুরী', 'URGENT')}
                      </span>
                    )}
                    <span className="bg-slate-100 text-slate-700 text-[11px] font-medium px-2 py-0.5 rounded">
                      {n.category}
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar size={12} />
                    {n.published_at ? formatDate(n.published_at) : ''}
                  </span>
                </div>

                <Link
                  href={`/notices/${n.id}`}
                  className="font-bold text-slate-900 hover:text-emerald-700 transition-colors line-clamp-2 text-base mb-2"
                >
                  {pick(n, 'title', n.title_bn)}
                </Link>

                <p className="text-slate-600 text-xs md:text-sm line-clamp-3 leading-relaxed mb-4">
                  {pick(n, 'content', n.content_bn)}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  {n.attachment_url ? t('📎 সংযুক্তি বিদ্যমান', '📎 Attachment available') : ''}
                </span>
                <Link
                  href={`/notices/${n.id}`}
                  className="text-xs font-semibold text-emerald-700 hover:underline"
                >
                  {t('বিস্তারিত পড়ুন', 'Read More')} &rarr;
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalPages={Math.max(1, Math.ceil(filteredNotices.length / 12))}
        onPageChange={(newPage) => setPage(newPage)}
      />
    </div>
  );
}
