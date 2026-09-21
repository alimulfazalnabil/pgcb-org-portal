'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Search, FileText, Download, Calendar, ExternalLink, Filter } from 'lucide-react';

interface CircularItem {
  id: number;
  category: string;
  reference_no?: string | null;
  title_bn: string;
  title_en?: string | null;
  summary_bn?: string | null;
  document_url?: string | null;
  published_at?: string | null;
}

const CATEGORIES = [
  { label: 'সকল সার্কুলার', value: 'ALL' },
  { label: 'অফিস আদেশ', value: 'OFFICE_ORDER' },
  { label: 'সাধারণ সার্কুলার', value: 'CIRCULAR' },
  { label: 'প্রশাসনিক বিজ্ঞপ্তি', value: 'GENERAL' },
  { label: 'কল্যাণমূলক কার্যক্রম', value: 'WELFARE' },
  { label: 'ইভেন্ট ও সম্মেলন', value: 'EVENT' },
];

export default function CircularsPage() {
  const [items, setItems] = useState<CircularItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/backend/api/v1/public/circulars')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setItems(data);
        }
      })
      .catch(() => {
        // Fallback demo circulars for immediate display
        setItems([
          {
            id: 1,
            category: 'OFFICE_ORDER',
            reference_no: 'PGCB/ADMIN/2026/089',
            title_bn: 'কেন্দ্রীয় কার্যনির্বাহী পরিষদের বার্ষিক সভার অফিস আদেশ ও কার্যতালিকা',
            summary_bn: 'সকল গ্রিড সার্কেলের ডিপ্লোমা প্রকৌশলীদের অবগতির জন্য জানানো যাচ্ছে যে আগামী মাসের ১৫ তারিখে কেন্দ্রীয় সাধারণ সভা অনুষ্ঠিত হবে।',
            published_at: new Date().toISOString(),
          },
          {
            id: 2,
            category: 'CIRCULAR',
            reference_no: 'PGCB/ENG/2026/044',
            title_bn: 'গ্রিড উপকেন্দ্র পরিচালন ও রক্ষণাবেক্ষণ নির্দেশিকা ২০২৬ প্রকাশ',
            summary_bn: 'জাতীয় গ্রিডের ৪০০কেভি ও ২৩০কেভি সাবস্টেশনের সুরক্ষা ও ডিজিটাল মনিটরিং বিষয়ক কারিগরি নির্দেশিকা প্রকাশ প্রসঙ্গে।',
            published_at: new Date().toISOString(),
          }
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return items.filter((x) => {
      const matchCat = selectedCategory === 'ALL' || x.category === selectedCategory;
      const matchQuery = !searchQuery.trim() || 
        x.title_bn.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (x.reference_no && x.reference_no.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchCat && matchQuery;
    });
  }, [items, searchQuery, selectedCategory]);

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Section Header */}
        <div className="space-y-3">
          <span className="inline-block py-1 px-3 rounded-full bg-primary/10 border border-primary/20 text-primary dark:text-accent text-xs font-bold uppercase tracking-wider">
            IDEB & PGCB OFFICIAL BULLETIN
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-primary dark:text-white tracking-tight">
            গ্রিড সার্কুলার ও অফিসিয়াল বিজ্ঞপ্তি
          </h1>
          <p className="text-sm sm:text-base text-secondary max-w-3xl">
            পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির অফিস আদেশ, কারিগরি নির্দেশিকা, পেশাগত উন্নয়ন ও বার্ষিক সাধারণ সভা সংক্রান্ত বিজ্ঞপ্তি।
          </p>
        </div>

        {/* Toolbar: Search and Filter Pills */}
        <div className="bg-background rounded-2xl border border-border p-6 shadow-sm space-y-4">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary">
              <Search size={18} />
            </div>
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="বিষয়, শিরোনাম বা রেফারেন্স নম্বর দিয়ে সার্কুলার অনুসন্ধান করুন..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-border bg-surface text-primary dark:text-white placeholder:text-secondary/60 focus:outline-none focus:ring-2 focus:ring-primary text-sm"
            />
          </div>

          {/* Category Filter Buttons */}
          <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-border/50">
            <span className="text-xs font-semibold text-secondary flex items-center gap-1 mr-1">
              <Filter size={13} /> বিভাগ:
            </span>
            {CATEGORIES.map((c) => {
              const isActive = selectedCategory === c.value;
              return (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => setSelectedCategory(c.value)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    isActive 
                      ? 'bg-primary text-white shadow-sm' 
                      : 'bg-surface hover:bg-border/60 text-secondary hover:text-primary border border-border'
                  }`}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Circular List */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-secondary">বিজ্ঞপ্তি তালিকা লোড হচ্ছে...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="bg-background rounded-2xl border border-border p-12 text-center space-y-2">
              <FileText size={36} className="mx-auto text-secondary/50" />
              <h3 className="font-bold text-primary dark:text-white text-base">কোনো সার্কুলার পাওয়া যায়নি</h3>
              <p className="text-xs text-secondary">ভিন্ন কীওয়ার্ড বা বিভাগ নির্বাচন করে পুনরায় চেষ্টা করুন।</p>
            </div>
          ) : (
            filtered.map((item) => (
              <article 
                key={item.id} 
                className="bg-background rounded-2xl border border-border p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-primary/10 text-primary border border-primary/20">
                      {item.category}
                    </span>
                    {item.published_at && (
                      <span className="text-xs text-secondary flex items-center gap-1">
                        <Calendar size={13} /> {new Date(item.published_at).toLocaleDateString('bn-BD')}
                      </span>
                    )}
                    {item.reference_no && (
                      <span className="text-xs font-mono text-secondary bg-surface px-2 py-0.5 rounded border border-border">
                        {item.reference_no}
                      </span>
                    )}
                  </div>
                  <h2 className="text-lg sm:text-xl font-bold text-primary dark:text-white">
                    {item.title_bn}
                  </h2>
                  {item.summary_bn && (
                    <p className="text-xs sm:text-sm text-secondary leading-relaxed line-clamp-2">
                      {item.summary_bn}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2.5 flex-shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-border">
                  <Link 
                    href={`/circulars/${item.id}`}
                    className="px-4 py-2 rounded-xl bg-surface hover:bg-border/60 border border-border text-primary dark:text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5"
                  >
                    <ExternalLink size={14} /> বিস্তারিত
                  </Link>
                  {item.document_url && item.document_url !== '#' ? (
                    <a 
                      href={item.document_url} 
                      target="_blank"
                      rel="noreferrer"
                      className="px-4 py-2 rounded-xl bg-primary hover:bg-primary/90 text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-sm"
                    >
                      <Download size={14} /> পিডিএফ
                    </a>
                  ) : (
                    <Link
                      href={`/circulars/${item.id}`}
                      className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 shadow-sm"
                    >
                      <FileText size={14} /> প্রিভিউ
                    </Link>
                  )}
                </div>
              </article>
            ))
          )}
        </div>

      </div>
    </div>
  );
}
