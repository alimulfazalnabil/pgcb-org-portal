'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ArrowLeft, Calendar, Download, FileText, Hash } from 'lucide-react';

export default function CircularDetail() {
  const params = useParams();
  const id = String(params?.id || '');
  const [item, setItem] = useState<any>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    fetch(`/backend/api/v1/public/circulars/${encodeURIComponent(id)}`)
      .then(async (r) => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.detail || 'সার্কুলার খুঁজে পাওয়া যায়নি');
        setItem(b);
      })
      .catch((e) => setError(e.message || 'সার্কুলার সেবা সাময়িকভাবে অনুপলব্ধ'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-secondary font-medium">সার্কুলার লোড হচ্ছে...</p>
        </div>
      </div>
    );
  }

  if (error || !item) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16">
        <div className="bg-background rounded-2xl border border-border p-10 text-center space-y-4 shadow-sm">
          <FileText size={40} className="mx-auto text-secondary/50" />
          <h1 className="text-2xl font-extrabold text-primary dark:text-white">সার্কুলার পাওয়া যায়নি</h1>
          <p className="text-sm text-secondary">{error || 'অনুরোধকৃত সার্কুলারটি বিদ্যমান নেই।'}</p>
          <Link
            href="/circulars"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all"
          >
            <ArrowLeft size={14} /> সকল সার্কুলারে ফিরুন
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link
          href="/circulars"
          className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
        >
          <ArrowLeft size={14} /> সকল সার্কুলার ও অফিস আদেশ
        </Link>

        <article className="bg-background rounded-3xl border border-border p-6 sm:p-10 shadow-sm space-y-6">
          <div className="flex flex-wrap items-center gap-2.5 pb-4 border-b border-border/60">
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
              {item.category}
            </span>
            {item.published_at && (
              <span className="text-xs text-secondary inline-flex items-center gap-1">
                <Calendar size={13} /> {new Date(item.published_at).toLocaleDateString('bn-BD')}
              </span>
            )}
            {item.reference_no && (
              <span className="text-xs font-mono text-secondary bg-surface px-2.5 py-1 rounded-lg border border-border inline-flex items-center gap-1">
                <Hash size={12} /> রেফারেন্স: {item.reference_no}
              </span>
            )}
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-primary dark:text-white leading-snug">
              {item.title_bn}
            </h1>
            {item.title_en && (
              <p className="text-sm sm:text-base text-secondary italic">{item.title_en}</p>
            )}
          </div>

          <div className="text-sm sm:text-base text-foreground leading-relaxed whitespace-pre-wrap pt-2">
            {item.summary_bn || item.content_bn || 'এই সার্কুলারের জন্য বিস্তারিত বিবরণ প্রকাশিত হয়নি।'}
          </div>

          <div className="pt-6 border-t border-border/60 flex flex-wrap items-center justify-between gap-4">
            {item.document_url && item.document_url !== '#' ? (
              <a
                href={item.document_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primary/90 text-white text-xs font-bold shadow-sm transition-all"
              >
                <Download size={15} /> অফিসিয়াল নথি ডাউনলোড করুন (PDF)
              </a>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-surface border border-border text-xs font-semibold text-secondary">
                <FileText size={14} /> আলাদা পিডিএফ সংযুক্তি নেই
              </span>
            )}
          </div>
        </article>
      </div>
    </div>
  );
}
