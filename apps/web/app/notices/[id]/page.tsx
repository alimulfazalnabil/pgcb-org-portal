'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { api, Notice } from '../../../lib/api';
import { LoadingState } from '../../../components/ui/LoadingState';
import { ErrorState } from '../../../components/ui/ErrorState';
import { Calendar, ArrowLeft, Download, Pin, AlertCircle, Share2 } from 'lucide-react';

export default function NoticeDetailPage() {
  const router = useRouter();
  const routeParams = useParams();
  const noticeId = routeParams?.id ? Number(routeParams.id) : null;
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!noticeId) {
      setError('অবৈধ নোটিশ আইডি');
      setLoading(false);
      return;
    }

    api.getNotice(noticeId)
      .then((data) => {
        setNotice(data);
      })
      .catch((err) => {
        setError(err.message || 'নোটিশ লোড করতে সমস্যা হয়েছে');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [noticeId]);

  if (loading) return <div className="max-w-4xl mx-auto px-6 py-16"><LoadingState message="নোটিশ লোড হচ্ছে..." /></div>;
  if (error || !notice) return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      <ErrorState message={error || 'নোটিশ খুঁজে পাওয়া যায়নি'} />
      <div className="text-center mt-4">
        <Link href="/notices" className="text-emerald-700 font-medium hover:underline">
          &larr; নোটিশ বোর্ডে ফিরে যান
        </Link>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 min-h-screen">
      <div className="mb-6">
        <Link href="/notices" className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700 hover:underline">
          <ArrowLeft size={16} /> সকল নোটিশে ফিরে যান
        </Link>
      </div>

      <article className="bg-white rounded-xl border border-slate-200 p-6 md:p-10 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {notice.is_pinned && (
            <span className="flex items-center gap-1 bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded">
              <Pin size={12} /> পিন করা
            </span>
          )}
          {notice.priority === 'URGENT' && (
            <span className="flex items-center gap-1 bg-red-100 text-red-700 text-xs font-bold px-2.5 py-1 rounded">
              <AlertCircle size={12} /> জরুরী
            </span>
          )}
          <span className="bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-1 rounded">
            ক্যাটাগরি: {notice.category}
          </span>
          <span className="text-xs text-slate-400 ml-auto flex items-center gap-1">
            <Calendar size={13} />
            প্রকাশের তারিখ: {notice.published_at ? new Date(notice.published_at).toLocaleDateString('bn-BD', { year: 'numeric', month: 'long', day: 'numeric' }) : '—'}
          </span>
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 leading-snug mb-6">
          {notice.title_bn}
        </h1>

        {notice.title_en && (
          <h2 className="text-lg font-medium text-slate-500 mb-6 italic">
            {notice.title_en}
          </h2>
        )}

        <div className="border-t border-slate-100 pt-6 text-slate-800 text-base md:text-lg leading-relaxed whitespace-pre-wrap">
          {notice.content_bn}
        </div>

        {notice.content_en && (
          <div className="mt-8 pt-6 border-t border-slate-100 text-slate-600 text-sm md:text-base leading-relaxed whitespace-pre-wrap">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">English Translation:</div>
            {notice.content_en}
          </div>
        )}

        {notice.attachment_url && (
          <div className="mt-10 p-5 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-100 text-emerald-800 rounded-lg">
                <Download size={24} />
              </div>
              <div>
                <h4 className="font-semibold text-slate-900 text-sm">অফিসিয়াল সংযুক্তি / ফাইল</h4>
                <p className="text-xs text-slate-500">মূল সার্কুলার বা দলিলের কপি ডাউনলোড করুন</p>
              </div>
            </div>
            <a
              href={notice.attachment_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 bg-emerald-700 text-white rounded-lg text-sm font-semibold hover:bg-emerald-800 transition-colors shadow-sm"
            >
              সংযুক্তি ডাউনলোড
            </a>
          </div>
        )}
      </article>
    </div>
  );
}
