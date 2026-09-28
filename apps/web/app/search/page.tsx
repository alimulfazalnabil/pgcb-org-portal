'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { api, CircleItem } from '@/lib/api';
import {
  Search,
  BookOpen,
  FileText,
  Filter,
  ExternalLink,
  CheckCircle2,
  History,
  Sparkles,
} from 'lucide-react';

type SiteResult = {
  type: string;
  id: number;
  title_bn: string;
  summary_bn?: string | null;
  date?: string | null;
  href: string;
};

type KnowledgePassage = {
  chunk_id: number;
  document_id: number;
  title: string;
  title_bn: string;
  category: string;
  document_type: string;
  version: string;
  is_current: boolean;
  approval_status: string;
  section: string;
  page: number;
  snippet: string;
  score: number;
  publication_date?: string;
  view_source_url: string;
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [year, setYear] = useState('');
  const [circleId, setCircleId] = useState('');
  const [includeHistorical, setIncludeHistorical] = useState(false);

  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [kbResults, setKbResults] = useState<KnowledgePassage[]>([]);
  const [siteResults, setSiteResults] = useState<SiteResult[]>([]);
  const [docsSearched, setDocsSearched] = useState(0);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.getCircles().then(setCircles).catch(() => {});
    const params = new URLSearchParams(window.location.search);
    const initial = params.get('q') || '';
    if (initial) {
      setQuery(initial);
      void runSearch(undefined, initial);
    } else {
      void runSearch(undefined, 'Membership Renewal');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function runSearch(e?: FormEvent, overrideQuery?: string) {
    e?.preventDefault();
    const q = (overrideQuery ?? query).trim();
    if (q.length < 2) {
      setMessage('কমপক্ষে ২টি অক্ষর দিয়ে অনুসন্ধান করুন।');
      return;
    }
    setBusy(true);
    setMessage('');
    try {
      const [kbRes, pubRes] = await Promise.allSettled([
        api.searchKnowledgeBase({
          q,
          category: category || undefined,
          year: year ? Number(year) : undefined,
          circle_id: circleId ? Number(circleId) : undefined,
          include_historical: includeHistorical,
        }),
        api.search(q),
      ]);

      let totalFound = 0;
      if (kbRes.status === 'fulfilled') {
        setKbResults(kbRes.value.results || []);
        setDocsSearched(kbRes.value.documents_searched || 0);
        totalFound += (kbRes.value.results || []).length;
      } else {
        setKbResults([]);
      }

      if (pubRes.status === 'fulfilled') {
        setSiteResults(pubRes.value.results || []);
        totalFound += (pubRes.value.results || []).length;
      } else {
        setSiteResults([]);
      }

      if (totalFound === 0) {
        setMessage('কোনো প্রামাণ্য নথি বা প্রকাশিত ফলাফল পাওয়া যায়নি।');
      }
    } catch (error: any) {
      setMessage(error.message || 'অনুসন্ধান ব্যর্থ হয়েছে।');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section py-12 min-h-screen bg-background">
      <div className="container max-w-5xl mx-auto px-4 space-y-8">
        {/* Header */}
        <div className="space-y-2 border-b border-border pb-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary">
            <Sparkles size={14} /> AI-POWERED SEMANTIC DOCUMENT SEARCH
          </span>
          <h1 className="text-3xl font-extrabold text-foreground">
            প্রামাণ্য নথিপত্র ও জ্ঞানভাণ্ডার অনুসন্ধান
          </h1>
          <p className="text-secondary text-sm">
            গঠনতন্ত্র, সদস্যপদ নির্দেশিকা ২০২৬, সার্কুলার, নোটিশ ও অফিসিয়াল নীতিমালা থেকে প্রাসঙ্গিক ধারা ও পৃষ্ঠা অনুসন্ধান করুন।
          </p>
        </div>

        {/* Search Input & Filters */}
        <form onSubmit={runSearch} className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                aria-label="Search"
                placeholder="প্রশ্ন বা বিষয় লিখুন (যেমন: How much to renew membership? / সদস্যপদ নবায়ন ফি কত?)..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              className="px-6 py-3 rounded-xl bg-primary text-white text-sm font-bold hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
            >
              {busy ? 'খোঁজা হচ্ছে...' : 'অনুসন্ধান করুন'}
            </button>
          </div>

          {/* Filter Row */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 border-t border-border text-xs">
            <div>
              <label className="block font-semibold text-secondary mb-1 flex items-center gap-1">
                <Filter size={12} /> নথির ধরন (Category)
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-background"
              >
                <option value="">সকল ক্যাটাগরি</option>
                <option value="MEMBERSHIP_GUIDELINES">Membership Guidelines</option>
                <option value="CONSTITUTION">Constitution (গঠনতন্ত্র)</option>
                <option value="CIRCULAR">Circulars (সার্কুলার)</option>
                <option value="REGULATIONS">Regulations (বিধিমালা)</option>
                <option value="NOTICE">Notices (নোটিশ)</option>
                <option value="ANNUAL_REPORT">Annual Reports</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-secondary mb-1">প্রকাশের বছর (Year)</label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-background"
              >
                <option value="">সকল বছর</option>
                <option value="2026">2026 (Current)</option>
                <option value="2025">2025 (Historical)</option>
                <option value="2024">2024</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-secondary mb-1">গ্রিড সার্কেল (Circle)</label>
              <select
                value={circleId}
                onChange={(e) => setCircleId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-border bg-background"
              >
                <option value="">কেন্দ্রীয় ও সকল সার্কেল</option>
                {circles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name_bn} ({c.name_en})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={includeHistorical}
                  onChange={(e) => setIncludeHistorical(e.target.checked)}
                  className="rounded border-border"
                />
                <span className="font-semibold text-foreground inline-flex items-center gap-1">
                  <History size={13} className="text-amber-600" /> পুরাতন (Superseded) সংস্করণসহ
                </span>
              </label>
            </div>
          </div>
        </form>

        {message && (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-700 text-xs font-medium">
            {message}
          </div>
        )}

        {/* Knowledge Base Semantic Passages */}
        {kbResults.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-extrabold text-foreground flex items-center gap-2">
                <BookOpen size={19} className="text-primary" /> প্রামাণ্য নথির অনুচ্ছেদসমূহ (Knowledge Passages)
              </h2>
              <span className="text-xs text-secondary">
                অনুসন্ধানকৃত নথি: <strong>{docsSearched}</strong> · প্রাপ্ত অনুচ্ছেদ: <strong>{kbResults.length}</strong>
              </span>
            </div>

            <div className="space-y-4">
              {kbResults.map((hit) => (
                <article
                  key={hit.chunk_id}
                  className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary">
                        {hit.category}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                          hit.is_current
                            ? 'bg-emerald-500/10 text-emerald-600'
                            : 'bg-amber-500/10 text-amber-700'
                        }`}
                      >
                        <CheckCircle2 size={11} />
                        {hit.is_current ? `CURRENT v${hit.version}` : `SUPERSEDED v${hit.version}`}
                      </span>
                      <span className="text-xs font-semibold text-secondary">
                        {hit.section} · Page {hit.page}
                      </span>
                    </div>

                    <a
                      href={hit.view_source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:underline"
                    >
                      [View source] <ExternalLink size={12} />
                    </a>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-foreground">{hit.title}</h3>
                    {hit.title_bn && hit.title_bn !== hit.title && (
                      <p className="text-xs text-secondary">{hit.title_bn}</p>
                    )}
                  </div>

                  <blockquote className="p-3.5 rounded-xl bg-surface border-l-4 border-primary text-xs md:text-sm text-foreground leading-relaxed">
                    &ldquo;{hit.snippet}&rdquo;
                  </blockquote>
                </article>
              ))}
            </div>
          </div>
        )}

        {/* Portal Site Search Results */}
        {siteResults.length > 0 && (
          <div className="space-y-4 pt-4 border-t border-border">
            <h2 className="text-lg font-extrabold text-foreground flex items-center gap-2">
              <FileText size={19} className="text-emerald-600" /> পোর্টাল সার্কুলার, ইভেন্ট ও প্রকাশনা
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {siteResults.map((item) => (
                <article
                  key={`${item.type}-${item.id}`}
                  className="bg-card border border-border rounded-2xl p-5 shadow-sm space-y-2"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="px-2.5 py-0.5 rounded-full font-bold bg-primary/10 text-primary">
                      {item.type}
                    </span>
                    <span className="text-secondary">
                      {item.date ? new Date(item.date).toLocaleDateString('bn-BD') : ''}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-foreground">{item.title_bn}</h3>
                  {item.summary_bn && (
                    <p className="text-xs text-secondary line-clamp-2">{item.summary_bn}</p>
                  )}
                  <Link
                    href={item.href}
                    className="inline-block text-xs font-bold text-primary hover:underline pt-1"
                  >
                    বিস্তারিত দেখুন →
                  </Link>
                </article>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
