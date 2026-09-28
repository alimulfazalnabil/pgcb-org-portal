'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api, NewsItem } from '@/lib/api';
import { Calendar, Eye, Tag, ArrowLeft, Newspaper } from 'lucide-react';

export default function NewsDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params?.slug || '';
  const [news, setNews] = useState<NewsItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    api
      .getNewsBySlug(decodeURIComponent(slug))
      .then((data) => setNews(data))
      .catch(() => setNews(null))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-3xl mx-auto px-4 text-center">
          <div className="inline-block animate-spin rounded-full h-9 w-9 border-4 border-primary border-t-transparent mb-3" />
          <p className="text-xs text-secondary">সংবাদ বিস্তারিত লোড হচ্ছে...</p>
        </div>
      </section>
    );
  }

  if (!news) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-md mx-auto px-4 text-center">
          <div className="bg-card border border-border rounded-2xl p-8">
            <Newspaper className="mx-auto text-secondary mb-3" size={40} />
            <h1 className="text-lg font-bold text-foreground mb-2">সংবাদটি খুঁজে পাওয়া যায়নি</h1>
            <Link
              href="/news"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-primary text-white text-xs font-semibold mt-3"
            >
              <ArrowLeft size={14} /> সংবাদ তালিকায় ফিরে যান
            </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="section py-12 min-h-screen bg-background">
      {news.structured_data && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(news.structured_data) }}
        />
      )}
      <div className="container max-w-4xl mx-auto px-4 space-y-6">
        <Link
          href="/news"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary"
        >
          <ArrowLeft size={14} /> সকল সংবাদে ফিরে যান
        </Link>

        <article className="bg-card border border-border rounded-3xl overflow-hidden shadow-sm">
          {news.cover_image_url && (
            <div className="w-full max-h-96 overflow-hidden bg-surface border-b border-border">
              <img
                src={news.cover_image_url}
                alt={news.title_bn || news.title_en}
                className="w-full h-full object-cover"
              />
            </div>
          )}

          <div className="p-6 md:p-10 space-y-6">
            <div className="flex flex-wrap items-center gap-3 text-xs text-secondary">
              <span className="px-3 py-1 rounded-full font-bold bg-primary/10 text-primary">
                {news.category}
              </span>
              {news.published_at && (
                <span className="inline-flex items-center gap-1">
                  <Calendar size={13} />
                  {new Date(news.published_at).toLocaleDateString('bn-BD', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}
                </span>
              )}
              <span className="inline-flex items-center gap-1">
                <Eye size={13} /> {news.view_count || 0} বার পঠিত
              </span>
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl md:text-3xl font-extrabold text-foreground leading-snug">
                {news.title_bn}
              </h1>
              {news.title_en && (
                <h2 className="text-base font-semibold text-secondary">{news.title_en}</h2>
              )}
            </div>

            {news.summary_bn && (
              <div className="p-4 rounded-2xl bg-surface border-l-4 border-primary text-sm text-foreground font-medium leading-relaxed">
                {news.summary_bn}
              </div>
            )}

            <div className="prose max-w-none text-foreground text-sm md:text-base leading-relaxed whitespace-pre-line">
              {news.body_bn}
            </div>

            {news.body_en && (
              <div className="pt-6 border-t border-border prose max-w-none text-secondary text-sm leading-relaxed whitespace-pre-line">
                {news.body_en}
              </div>
            )}

            {news.tags && news.tags.length > 0 && (
              <div className="pt-4 border-t border-border flex flex-wrap items-center gap-2">
                {news.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs bg-surface border border-border text-secondary"
                  >
                    <Tag size={12} /> {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}
