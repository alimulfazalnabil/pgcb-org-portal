'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  BookOpen,
  FilePlus,
  CheckCircle2,
  ShieldAlert,
  BarChart3,
  HelpCircle,
  Wand2,
  ArrowLeft,
} from 'lucide-react';
import {
  getAIUsageAnalytics,
  getAdminIntelligenceDashboard,
  getAdminKnowledgeDocuments,
  getAdminFAQs,
  createKnowledgeDocument,
  generateSmartFAQs,
  updateAdminFAQ,
  runAIContentAssist,
} from '@/lib/api/admin';
import type {
  AIUsageAnalytics,
  AdminIntelligenceDashboard,
  KnowledgeDocumentItem,
  KnowledgeFAQItem,
} from '@/lib/api/types';

export default function AdminAIConsolePage() {
  const [analytics, setAnalytics] = useState<AIUsageAnalytics | null>(null);
  const [intelligence, setIntelligence] = useState<AdminIntelligenceDashboard | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocumentItem[]>([]);
  const [faqs, setFaqs] = useState<KnowledgeFAQItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Knowledge document creation state
  const [docTitleBn, setDocTitleBn] = useState('');
  const [docTitleEn, setDocTitleEn] = useState('');
  const [docCategory, setDocCategory] = useState('MEMBERSHIP_GUIDELINES');
  const [docVersion, setDocVersion] = useState('2026.1');
  const [docAccessLevel, setDocAccessLevel] = useState('PUBLIC');
  const [docRawText, setDocRawText] = useState('');

  // Content Assist state
  const [assistTitleBn, setAssistTitleBn] = useState('');
  const [assistContentBn, setAssistContentBn] = useState('');
  const [assistResult, setAssistResult] = useState<any | null>(null);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [aData, iData, dData, fData] = await Promise.all([
        getAIUsageAnalytics().catch(() => null),
        getAdminIntelligenceDashboard().catch(() => null),
        getAdminKnowledgeDocuments().catch(() => []),
        getAdminFAQs().catch(() => []),
      ]);
      setAnalytics(aData);
      setIntelligence(iData);
      setDocuments(dData);
      setFaqs(fData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleIngestDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docTitleBn.trim() || !docRawText.trim()) return;
    try {
      await createKnowledgeDocument({
        title_bn: docTitleBn,
        title_en: docTitleEn || docTitleBn,
        category: docCategory,
        version: docVersion,
        access_level: docAccessLevel,
        raw_text: docRawText,
      });
      setStatusMsg('নতুন প্রামাণ্য নথি সফলভাবে এআই নলেজ বেসে যুক্ত ও ইনডেক্স করা হয়েছে।');
      setDocTitleBn('');
      setDocTitleEn('');
      setDocRawText('');
      loadAll();
    } catch {
      setStatusMsg('নথি যুক্ত করতে ত্রুটি হয়েছে।');
    }
  };

  const handleGenerateFAQs = async (docId: number) => {
    try {
      const res = await generateSmartFAQs(docId, 3);
      setStatusMsg(`${res.generated_count} টি খসড়া (DRAFT) প্রশ্নোত্তর তৈরি হয়েছে। অনুমোদনের পর তা প্রকাশিত হবে।`);
      loadAll();
    } catch {
      setStatusMsg('FAQ তৈরিতে ত্রুটি হয়েছে।');
    }
  };

  const handlePublishFAQ = async (faqId: number, status: string) => {
    try {
      await updateAdminFAQ(faqId, { status });
      setStatusMsg(`FAQ স্ট্যাটাস ${status}-এ হালনাগাদ করা হয়েছে।`);
      loadAll();
    } catch {
      setStatusMsg('FAQ স্ট্যাটাস পরিবর্তনে ত্রুটি হয়েছে।');
    }
  };

  const handleRunAssist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assistTitleBn.trim()) return;
    try {
      const res = await runAIContentAssist({
        title_bn: assistTitleBn,
        content_bn: assistContentBn,
        entity_type: 'NOTICE',
      });
      setAssistResult(res.suggestions);
    } catch {
      setStatusMsg('এআই কনটেন্ট অ্যাসিস্ট চালাতে ত্রুটি হয়েছে।');
    }
  };

  return (
    <section className="section">
      <div className="container space-y-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold mb-2">
              <Sparkles size={14} />
              <span>Sprint 5 — Institutional Intelligence &amp; AI</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">
              প্রাতিষ্ঠানিক ইন্টেলিজেন্স ও এআই ব্যবস্থাপনা (AI &amp; Knowledge Console)
            </h1>
            <p className="text-sm text-secondary mt-1">
              পিজিসিবি-এর প্রামাণ্য নথিপত্র, সংস্করণ নিয়ন্ত্রণ, স্মার্ট FAQ অনুমোদন, এবং এআই ব্যবহারের রিয়েল-টাইম পর্যবেক্ষণ।
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/admin/health" className="btn btn-outline text-xs">
              সিস্টেম হেলথ (System Health)
            </Link>
            <Link href="/admin" className="btn btn-outline text-xs inline-flex items-center gap-1">
              <ArrowLeft size={14} /> অ্যাডমিন ড্যাশবোর্ড
            </Link>
          </div>
        </div>

        {statusMsg && (
          <div
            role="status"
            className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-900 text-sm font-semibold flex items-center justify-between"
          >
            <span>{statusMsg}</span>
            <button type="button" onClick={() => setStatusMsg(null)} className="text-xs underline">
              বন্ধ করুন
            </button>
          </div>
        )}

        {/* 1. AI Usage Monitoring & Administrative Intelligence KPIs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card card-body space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <BarChart3 size={18} className="text-primary" />
                <span>AI Usage Monitoring (এআই ব্যবহার পর্যবেক্ষণ)</span>
              </h2>
              <span className="badge badge-success">Guardrails Active</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Questions Today</div>
                <div className="text-xl font-extrabold text-primary">{analytics?.questions_today ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Documents Searched</div>
                <div className="text-xl font-extrabold text-foreground">{analytics?.documents_searched ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Unanswered</div>
                <div className="text-xl font-extrabold text-amber-600">{analytics?.unanswered ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Avg Response Time</div>
                <div className="text-xl font-extrabold text-emerald-600">
                  {analytics?.avg_response_time_sec ?? 0.1}s
                </div>
              </div>
            </div>
            <div className="flex flex-wrap items-center justify-between text-xs text-secondary pt-2 border-t border-border">
              <span>Prompt-Injection Blocked: {analytics?.security_blocked ?? 0}</span>
              <span>Total Tokens: {analytics?.total_tokens ?? 0}</span>
              <span>Est. Cost: ${analytics?.estimated_cost_usd ?? 0}</span>
            </div>
          </div>

          <div className="card card-body space-y-4">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <ShieldAlert size={18} className="text-primary" />
              <span>Administrative Intelligence (প্রাতিষ্ঠানিক সামারি)</span>
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Total / Active Members</div>
                <div className="text-lg font-extrabold text-foreground">
                  {intelligence?.members ?? 0} / <span className="text-emerald-600">{intelligence?.active ?? 0}</span>
                </div>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Pending / Expiring (30d)</div>
                <div className="text-lg font-extrabold text-amber-600">
                  {intelligence?.pending ?? 0} / {intelligence?.expiring_next_30_days ?? 0}
                </div>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-border">
                <div className="text-xs text-secondary">Revenue This Month</div>
                <div className="text-lg font-extrabold text-primary">
                  {intelligence?.revenue_this_month_formatted ?? '৳0'}
                </div>
              </div>
            </div>
            {intelligence?.circles_by_pending_applications && (
              <div className="text-xs space-y-1 pt-2 border-t border-border">
                <div className="font-bold text-foreground">
                  Top Grid Circles by Pending Applications:
                </div>
                <div className="flex flex-wrap gap-2">
                  {intelligence.circles_by_pending_applications.slice(0, 4).map((c) => (
                    <span
                      key={c.circle_id}
                      className="px-2.5 py-1 rounded-lg bg-surface border border-border text-secondary font-medium"
                    >
                      {c.circle_name_en}: <strong className="text-foreground">{c.pending_applications}</strong> pending
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. Knowledge Base Document Repository & Ingestion */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <form onSubmit={handleIngestDocument} className="card card-body space-y-3">
            <h2 className="text-base font-bold flex items-center gap-2">
              <FilePlus size={17} className="text-primary" />
              <span>নলেজ বেসে নতুন নথি যুক্ত করুন</span>
            </h2>
            <div>
              <label className="label text-xs" htmlFor="kb-title-bn">
                শিরোনাম (বাংলা)
              </label>
              <input
                id="kb-title-bn"
                className="input text-xs"
                value={docTitleBn}
                onChange={(e) => setDocTitleBn(e.target.value)}
                placeholder="যেমন: সদস্যপদ নির্দেশিকা ২০২৬"
                required
              />
            </div>
            <div>
              <label className="label text-xs" htmlFor="kb-title-en">
                Title (English)
              </label>
              <input
                id="kb-title-en"
                className="input text-xs"
                value={docTitleEn}
                onChange={(e) => setDocTitleEn(e.target.value)}
                placeholder="e.g. Membership Guidelines 2026"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="label text-xs" htmlFor="kb-category">
                  ক্যাটাগরি
                </label>
                <select
                  id="kb-category"
                  className="input text-xs"
                  value={docCategory}
                  onChange={(e) => setDocCategory(e.target.value)}
                >
                  <option value="CONSTITUTION">CONSTITUTION</option>
                  <option value="REGULATIONS">REGULATIONS</option>
                  <option value="MEMBERSHIP_GUIDELINES">MEMBERSHIP_GUIDELINES</option>
                  <option value="CIRCULAR">CIRCULAR</option>
                  <option value="NOTICE">NOTICE</option>
                  <option value="ANNUAL_REPORT">ANNUAL_REPORT</option>
                </select>
              </div>
              <div>
                <label className="label text-xs" htmlFor="kb-access">
                  অ্যাক্সেস লেভেল (RBAC)
                </label>
                <select
                  id="kb-access"
                  className="input text-xs"
                  value={docAccessLevel}
                  onChange={(e) => setDocAccessLevel(e.target.value)}
                >
                  <option value="PUBLIC">PUBLIC</option>
                  <option value="MEMBER">MEMBER</option>
                  <option value="CIRCLE_ADMIN">CIRCLE_ADMIN</option>
                  <option value="CENTRAL_ADMIN">CENTRAL_ADMIN</option>
                </select>
              </div>
            </div>
            <div>
              <label className="label text-xs" htmlFor="kb-version">
                সংস্করণ (Version)
              </label>
              <input
                id="kb-version"
                className="input text-xs"
                value={docVersion}
                onChange={(e) => setDocVersion(e.target.value)}
              />
            </div>
            <div>
              <label className="label text-xs" htmlFor="kb-text">
                নথির বিষয়বস্তু ([Page X] Section Y.Z ফরম্যাট সমর্থিত)
              </label>
              <textarea
                id="kb-text"
                rows={4}
                className="input text-xs"
                value={docRawText}
                onChange={(e) => setDocRawText(e.target.value)}
                placeholder="[Page 14] Section 4.2: Annual membership renewal fee is 2,000 BDT..."
                required
              />
            </div>
            <button type="submit" className="btn btn-primary text-xs w-full">
              নলেজ বেসে ইনডেক্স করুন
            </button>
          </form>

          <div className="card card-body lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold flex items-center gap-2">
                <BookOpen size={17} className="text-primary" />
                <span>প্রামাণ্য নথিপত্র ও সংস্করণ নিয়ন্ত্রণ ({documents.length})</span>
              </h2>
              <Link href="/search" className="text-xs text-primary font-semibold hover:underline">
                সিম্যান্টিক সার্চ পরীক্ষা করুন →
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-border text-secondary">
                    <th className="py-2 pr-3">শিরোনাম (Title)</th>
                    <th className="py-2 pr-3">ক্যাটাগরি</th>
                    <th className="py-2 pr-3">সংস্করণ</th>
                    <th className="py-2 pr-3">অ্যাক্সেস</th>
                    <th className="py-2 pr-3">অবস্থা</th>
                    <th className="py-2">অ্যাকশন</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td className="py-2.5 pr-3">
                        <div className="font-bold text-foreground">{doc.title_en || doc.title_bn}</div>
                        <div className="text-[11px] text-secondary">{doc.title_bn}</div>
                      </td>
                      <td className="py-2.5 pr-3">{doc.category}</td>
                      <td className="py-2.5 pr-3 font-mono">{doc.version}</td>
                      <td className="py-2.5 pr-3">
                        <span className="badge">{doc.access_level}</span>
                      </td>
                      <td className="py-2.5 pr-3">
                        {doc.is_current ? (
                          <span className="badge badge-success">Current (Authoritative)</span>
                        ) : (
                          <span className="badge badge-warning">Superseded</span>
                        )}
                      </td>
                      <td className="py-2.5">
                        <button
                          type="button"
                          onClick={() => handleGenerateFAQs(doc.id)}
                          className="btn btn-outline text-[11px] py-1 px-2"
                        >
                          Generate Smart FAQs
                        </button>
                      </td>
                    </tr>
                  ))}
                  {!loading && documents.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-4 text-center text-secondary">
                        কোনো নথি পাওয়া যায়নি।
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 3. Smart FAQ Review & Approval + AI-Assisted Content Management */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card card-body space-y-4">
            <h2 className="text-base font-bold flex items-center gap-2">
              <HelpCircle size={17} className="text-primary" />
              <span>Smart FAQ Approval Queue (অ্যাডমিন অনুমোদন ছাড়া অপ্রকাশিত)</span>
            </h2>
            <div className="space-y-2.5 max-h-[340px] overflow-y-auto">
              {faqs.map((faq) => (
                <div key={faq.id} className="p-3 rounded-xl bg-surface border border-border space-y-1.5 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold text-foreground">{faq.question_en || faq.question_bn}</span>
                    <span className={`badge ${faq.status === 'PUBLISHED' ? 'badge-success' : 'badge-warning'}`}>
                      {faq.status}
                    </span>
                  </div>
                  <p className="text-secondary">{faq.answer_en || faq.answer_bn}</p>
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-secondary">
                      Ref: {faq.section_ref || 'General'} {faq.page_ref ? `(Page ${faq.page_ref})` : ''}
                    </span>
                    {faq.status !== 'PUBLISHED' && (
                      <button
                        type="button"
                        onClick={() => handlePublishFAQ(faq.id, 'PUBLISHED')}
                        className="px-2.5 py-1 rounded-lg bg-primary text-white text-[11px] font-bold inline-flex items-center gap-1"
                      >
                        <CheckCircle2 size={12} /> Approve &amp; Publish
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {!loading && faqs.length === 0 && (
                <div className="text-xs text-secondary py-4 text-center">
                  উপরের যেকোনো নথি থেকে &ldquo;Generate Smart FAQs&rdquo; বাটনে ক্লিক করে খসড়া প্রশ্নোত্তর তৈরি করুন।
                </div>
              )}
            </div>
          </div>

          <div className="card card-body space-y-4">
            <h2 className="text-base font-bold flex items-center gap-2">
              <Wand2 size={17} className="text-primary" />
              <span>AI-Assisted Content Studio (Human Review Mandatory)</span>
            </h2>
            <form onSubmit={handleRunAssist} className="space-y-3 text-xs">
              <div>
                <label className="label text-xs" htmlFor="assist-title">
                  নোটিশ বা সংবাদের শিরোনাম
                </label>
                <input
                  id="assist-title"
                  className="input text-xs"
                  value={assistTitleBn}
                  onChange={(e) => setAssistTitleBn(e.target.value)}
                  placeholder="যেমন: বার্ষিক সাধারণ সভা ২০২৬ সংক্রান্ত বিজ্ঞপ্তি"
                  required
                />
              </div>
              <div>
                <label className="label text-xs" htmlFor="assist-body">
                  খসড়া বিবরণ
                </label>
                <textarea
                  id="assist-body"
                  rows={3}
                  className="input text-xs"
                  value={assistContentBn}
                  onChange={(e) => setAssistContentBn(e.target.value)}
                  placeholder="মূল বিবরণ লিখুন..."
                />
              </div>
              <button type="submit" className="btn btn-primary text-xs">
                Generate Wording, Translation, Summary &amp; SEO
              </button>
            </form>

            {assistResult && (
              <div className="p-3 rounded-xl bg-surface border border-border text-xs space-y-2">
                <div>
                  <strong>Improved Bangla:</strong> {assistResult.improved_wording?.content_bn}
                </div>
                <div>
                  <strong>English Translation:</strong> {assistResult.translation?.bn_to_en}
                </div>
                <div>
                  <strong>SEO Slug:</strong> <code>{assistResult.seo_metadata?.suggested_slug}</code>
                </div>
                <div className="text-[11px] text-amber-700 font-semibold">
                  * Assistive draft only — requires human editor/publisher approval before publication.
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
