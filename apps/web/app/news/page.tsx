'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, NewsItem } from '@/lib/api';
import { Newspaper, Calendar, Eye, Tag, Search, Star, ArrowRight } from 'lucide-react';
import { useLanguage } from '@/lib/i18n';

const CATEGORIES = [
  { code: '', labelBn: 'সকল সংবাদ', labelEn: 'All News' },
  { code: 'ORGANIZATIONAL', labelBn: 'সাংগঠনিক', labelEn: 'Organizational' },
  { code: 'PRESS_RELEASE', labelBn: 'প্রেস বিজ্ঞপ্তি', labelEn: 'Press Release' },
  { code: 'WELFARE', labelBn: 'সদস্য কল্যাণ', labelEn: 'Member Welfare' },
  { code: 'GRID_OPERATIONS', labelBn: 'গ্রিড কার্যক্রম', labelEn: 'Grid Operations' },
  { code: 'EVENT', labelBn: 'সম্মেলন ও ইভেন্ট', labelEn: 'Conferences & Events' },
];

export default function NewsListPage() {
  const { language, t, pick, formatNumber, formatDate } = useLanguage();
  const [items, setItems] = useState<NewsItem[]>([]);
  const [category, setCategory] = useState('');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);

  async function fetchNews() {
    setLoading(true);
    try {
      const data = await api.getNews({
        category: category || undefined,
        q: query.trim() || undefined,
      });
      setItems(data);
    } catch (err) {
      console.error('Failed to load news', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchNews();
  }, [category]);

  const featured = items.find((item) => item.is_featured);

  return (
    <section className="section py-10 min-h-screen bg-background">
      <div className="container max-w-6xl mx-auto px-4 space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-6 border-b border-border">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary mb-2">
              <Newspaper size={14} /> NEWS & PRESS RELEASES
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-foreground">
              {t('সংবাদ ও প্রেস বিজ্ঞপ্তি', 'News & Press Releases')}
            </h1>
            <p className="text-secondary text-sm mt-1">
              {t(
                'পাওয়ার গ্রিড প্রকৌশলী সমিতির সাম্প্রতিক সাংগঠনিক সংবাদ, প্রেস বিজ্ঞপ্তি ও ঘোষণা।',
                'Recent organizational news, press releases, and official announcements of the Power Grid Engineers Association.'
              )}
            </p>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              fetchNews();
            }}
            className="flex items-center gap-2 w-full md:w-auto"
          >
            <div className="relative flex-1 md:w-64">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                type="text"
                placeholder={t('সংবাদ অনুসন্ধান করুন...', 'Search news...')}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-border bg-card text-xs focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold hover:opacity-90 transition-all"
            >
              {t('খুঁজুন', 'Search')}
            </button>
          </form>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.code}
              type="button"
              onClick={() => setCategory(cat.code)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                category === cat.code
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-card border border-border text-secondary hover:text-foreground'
              }`}
            >
              {t(cat.labelBn, cat.labelEn)}
            </button>
          ))}
        </div>

        {/* Featured News Banner */}
        {featured && !query && !category && (
          <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white p-6 md:p-8 shadow-lg border border-amber-500/30">
            <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-2">
              <Star size={14} /> {t('প্রধান সংবাদ (Featured News)', 'Featured News')}
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-white mb-2">
              {pick(featured, 'title', featured.title_bn || featured.title_en)}
            </h2>
            {(featured.summary_bn || featured.summary_en) && (
              <p className="text-sm text-slate-300 line-clamp-2 mb-4 max-w-3xl">
                {pick(featured, 'summary', featured.summary_bn || '')}
              </p>
            )}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span className="inline-flex items-center gap-1">
                  <Calendar size={13} />
                  {featured.published_at ? formatDate(featured.published_at) : t('সাম্প্রতিক', 'Recent')}
                </span>
                <span className="inline-flex items-center gap-1">
                  <Eye size={13} />{' '}
                  {language === 'en'
                    ? `${formatNumber(featured.view_count || 0)} views`
                    : `${formatNumber(featured.view_count || 0)} বার পঠিত`}
                </span>
              </div>
              <Link
                href={`/news/${encodeURIComponent(featured.slug)}`}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-500 text-slate-950 text-xs font-bold hover:bg-amber-400 transition-colors"
              >
                {t('বিস্তারিত পড়ুন', 'Read Full Story')} <ArrowRight size={14} />
              </Link>
            </div>
          </div>
        )}

        {/* News Grid */}
        {loading ? (
          <div className="py-16 text-center">
            <div className="inline-block animate-spin rounded-full h-9 w-9 border-4 border-primary border-t-transparent mb-3" />
            <p className="text-xs text-secondary">{t('সংবাদ লোড হচ্ছে...', 'Loading news...')}</p>
          </div>
        ) : items.length === 0 ? (
          <div className="bg-card border border-border rounded-2xl p-12 text-center">
            <Newspaper className="mx-auto text-secondary mb-3" size={40} />
            <h3 className="text-base font-bold text-foreground mb-1">
              {t('কোনো সংবাদ পাওয়া যায়নি', 'No news found')}
            </h3>
            <p className="text-xs text-secondary">
              {t('অনুগ্রহ করে ভিন্ন ক্যাটাগরি বা কীওয়ার্ড দিয়ে অনুসন্ধান করুন।', 'Please search with a different category or keyword.')}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map((item) => (
              <article
                key={item.id}
                className="bg-card border border-border rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                {item.cover_image_url && (
                  <div className="aspect-video w-full overflow-hidden bg-surface border-b border-border">
                    <img
                      src={item.cover_image_url}
                      alt={item.title_bn || item.title_en}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <div className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">
                        {item.category}
                      </span>
                      <span className="text-[11px] text-secondary inline-flex items-center gap-1">
                        <Calendar size={12} />
                        {item.published_at ? formatDate(item.published_at) : ''}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-foreground line-clamp-2">
                      <Link href={`/news/${encodeURIComponent(item.slug)}`} className="hover:text-primary">
                        {pick(item, 'title', item.title_bn || item.title_en)}
                      </Link>
                    </h3>

                    {(item.summary_bn || item.summary_en || item.body_bn || item.body_en) && (
                      <p className="text-xs text-secondary line-clamp-3 leading-relaxed">
                        {pick(item, 'summary', item.summary_bn || item.body_bn || '')}
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-border flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {(item.tags || []).slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-0.5 text-[10px] px-2 py-0.5 rounded bg-surface text-secondary"
                        >
                          <Tag size={10} /> {tag}
                        </span>
                      ))}
                    </div>
                    <Link
                      href={`/news/${encodeURIComponent(item.slug)}`}
                      className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:underline"
                    >
                      {t('পড়ুন', 'Read')} <ArrowRight size={13} />
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
