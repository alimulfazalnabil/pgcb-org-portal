'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MessageCircle, X, Send, Sparkles, BookOpen, ShieldCheck, Wrench, AlertCircle } from 'lucide-react';

interface SuggestedLink {
  label_bn: string;
  label_en?: string;
  url: string;
}

interface AISourceCitation {
  document_id: number;
  title: string;
  title_bn?: string;
  category?: string;
  version?: string;
  section?: string | null;
  page?: number | null;
  view_source_url: string;
}

interface AIToolCall {
  tool_name: string;
  authorized: boolean;
}

interface AIFallbackAction {
  action: string;
  label: string;
  label_bn?: string;
  url: string;
}

interface ChatMessage {
  role: 'assistant' | 'user';
  text_bn: string;
  text_en?: string;
  unanswered?: boolean;
  security_flagged?: boolean;
  sources?: AISourceCitation[];
  tools_used?: AIToolCall[];
  fallback_actions?: AIFallbackAction[];
  links?: SuggestedLink[];
}

const SAMPLE_QUESTIONS_BY_MODE: Record<'PUBLIC' | 'MEMBER' | 'ADMIN', string[]> = {
  PUBLIC: [
    'How do I renew my membership and how much is the fee?',
    'Who is eligible for membership?',
    'কিভাবে সদস্যপদ আবেদন করব?',
    'ডিজিটাল আইডি কার্ড ও সনদপত্র কিভাবে যাচাই করা যায়?',
  ],
  MEMBER: [
    'What is my membership status and my id?',
    'Show my payment history and receipts',
    'What is my application status?',
  ],
  ADMIN: [
    'How many active members are currently registered?',
    'Which Circles have the highest number of pending applications?',
    'Show pending applications',
  ],
};

export function HelpdeskWidget() {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<'PUBLIC' | 'MEMBER' | 'ADMIN'>('PUBLIC');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text_bn:
        'স্বাগতম! আমি পিজিসিবি প্রাতিষ্ঠানিক এআই সহকারী (PGCB Institutional AI Assistant)। গঠনতন্ত্র, সদস্যপদ নির্দেশিকা ২০২৬, বার্ষিক নবায়ন ফি, সার্কুলার বা আপনার সদস্যপদ স্ট্যাটাস বিষয়ে প্রশ্ন করুন। প্রতিটি উত্তর প্রামাণ্য নথির সূত্রসহ প্রদান করা হয়।',
      links: [
        { label_bn: 'সদস্যপদ আবেদন', label_en: 'Apply', url: '/apply' },
        { label_bn: 'এআই নথি অনুসন্ধান', label_en: 'AI Document Search', url: '/search' },
      ],
    },
  ]);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  const askQuestion = async (qText: string) => {
    const trimmed = qText.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: 'user', text_bn: trimmed }]);
    setQuestion('');
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/ai/ask', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed, mode, language: 'bn' }),
      });

      if (res.status === 401 || res.status === 403) {
        const errData = await res.json().catch(() => ({}));
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text_bn:
              errData.detail ||
              (mode === 'MEMBER'
                ? 'সদস্য মোড ব্যবহারের জন্য অনুগ্রহ করে প্রথমে লগইন করুন।'
                : 'অ্যাডমিন এআই মোড শুধুমাত্র অনুমোদিত প্রশাসকদের জন্য সংরক্ষিত।'),
            links: [{ label_bn: 'লগইন করুন', label_en: 'Login', url: '/login' }],
          },
        ]);
        return;
      }

      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn: data.answer_bn || data.answer || 'আপনার প্রশ্নের উত্তর পাওয়া গেছে।',
          text_en: data.answer_en,
          unanswered: data.unanswered,
          security_flagged: data.security_flagged,
          sources: data.sources || [],
          tools_used: data.tools_used || [],
          fallback_actions: data.fallback_actions || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn:
            'দুঃখিত, এই মুহূর্তে এআই সার্ভিসে সংযোগ দেওয়া যাচ্ছে না। অনুগ্রহ করে `/search`, `/circulars`, অথবা `/contact` পেজ দেখুন।',
          links: [
            { label_bn: 'নথি অনুসন্ধান', label_en: 'Search Documents', url: '/search' },
            { label_bn: 'যোগাযোগ', label_en: 'Contact Secretariat', url: '/contact' },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-16 md:bottom-6 right-4 md:right-6 z-50">
      {open ? (
        <div
          role="dialog"
          aria-modal="false"
          aria-label="PGCB প্রাতিষ্ঠানিক এআই সহকারী"
          className="w-[350px] sm:w-[410px] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[580px]"
        >
          <div className="bg-primary text-white px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles size={16} />
              <div>
                <div className="text-xs font-bold">পিজিসিবি প্রাতিষ্ঠানিক এআই সহকারী</div>
                <div className="text-[10px] opacity-85">Authoritative Knowledge &amp; Citation Engine</div>
              </div>
            </div>
            <button
              type="button"
              aria-label="চ্যাট বন্ধ করুন"
              onClick={() => setOpen(false)}
              className="p-1 rounded-lg hover:bg-white/10"
            >
              <X size={16} />
            </button>
          </div>

          {/* 3-Mode Selector: Public | Member | Admin */}
          <div className="px-3 py-1.5 bg-surface border-b border-border flex items-center justify-between gap-1 text-[11px]">
            <span className="text-secondary font-semibold">মোড (Mode):</span>
            <div className="flex gap-1">
              {(['PUBLIC', 'MEMBER', 'ADMIN'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`px-2.5 py-0.5 rounded-md font-bold transition ${
                    mode === m
                      ? 'bg-primary text-white'
                      : 'bg-card border border-border text-secondary hover:text-foreground'
                  }`}
                >
                  {m === 'PUBLIC' ? 'Public' : m === 'MEMBER' ? 'Member' : 'Admin'}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 space-y-3 overflow-y-auto flex-1 bg-surface/40 text-xs max-h-[340px]">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`rounded-2xl px-3.5 py-2.5 max-w-[92%] whitespace-pre-line leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-primary text-white'
                      : m.security_flagged
                      ? 'bg-red-50 border border-red-300 text-red-900'
                      : 'bg-card border border-border text-foreground shadow-sm'
                  }`}
                >
                  {m.text_bn}
                  {m.text_en && m.text_en !== m.text_bn && (
                    <div className="mt-1.5 pt-1.5 border-t border-border/60 text-[11px] text-secondary">
                      {m.text_en}
                    </div>
                  )}
                </div>

                {/* Controlled Backend Tools Executed */}
                {m.tools_used && m.tools_used.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {m.tools_used.map((t, tIdx) => (
                      <span
                        key={tIdx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 text-[10px] font-semibold"
                      >
                        <Wrench size={10} />
                        Verified Tool: {t.tool_name}
                      </span>
                    ))}
                  </div>
                )}

                {/* Authoritative Document Citations */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-1.5 w-[92%] rounded-xl bg-card border border-border p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-primary uppercase tracking-wide">
                      <BookOpen size={11} />
                      <span>Sources (প্রামাণ্য সূত্র)</span>
                    </div>
                    {m.sources.map((src, sIdx) => (
                      <div
                        key={sIdx}
                        className="text-[11px] flex items-start justify-between gap-2 border-t border-border/50 pt-1 first:border-0 first:pt-0"
                      >
                        <div>
                          <div className="font-semibold text-foreground">• {src.title}</div>
                          <div className="text-[10px] text-secondary">
                            {src.section ? `${src.section}` : 'Official Section'}
                            {src.page ? ` (Page ${src.page})` : ''}
                          </div>
                        </div>
                        <a
                          href={`/backend${src.view_source_url}`}
                          target="_blank"
                          rel="noreferrer"
                          className="shrink-0 px-2 py-0.5 rounded bg-primary/10 text-primary font-semibold text-[10px] hover:bg-primary/20"
                        >
                          [View source]
                        </a>
                      </div>
                    ))}
                  </div>
                )}

                {/* Safe "No Answer" Fallback Actions */}
                {m.unanswered && m.fallback_actions && m.fallback_actions.length > 0 && (
                  <div className="mt-1.5 w-[92%] rounded-xl bg-amber-500/10 border border-amber-500/30 p-2.5 space-y-1.5">
                    <div className="flex items-center gap-1 text-[10px] font-bold text-amber-800">
                      <AlertCircle size={11} />
                      <span>Authoritative Fallback Options:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {m.fallback_actions.map((fb, fIdx) => (
                        <Link
                          key={fIdx}
                          href={fb.url}
                          onClick={() => setOpen(false)}
                          className="px-2.5 py-1 rounded-lg bg-card border border-amber-500/40 text-foreground font-semibold text-[11px] hover:border-primary"
                        >
                          {fb.label} →
                        </Link>
                      ))}
                    </div>
                  </div>
                )}

                {m.links && m.links.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {m.links.map((lnk, lIdx) => (
                      <Link
                        key={lIdx}
                        href={lnk.url}
                        onClick={() => setOpen(false)}
                        className="px-2.5 py-1 rounded-lg bg-primary/10 text-primary font-semibold text-[11px] hover:bg-primary/20"
                      >
                        {lnk.label_bn} →
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="text-[11px] text-secondary italic px-2">
                প্রামাণ্য নথিপত্র যাচাই করে উত্তর প্রস্তুত হচ্ছে...
              </div>
            )}
          </div>

          <div className="px-3 py-2 border-t border-border bg-card flex flex-wrap gap-1">
            {SAMPLE_QUESTIONS_BY_MODE[mode].map((sq, i) => (
              <button
                key={i}
                type="button"
                onClick={() => askQuestion(sq)}
                className="text-[10px] px-2 py-1 rounded-md bg-surface border border-border text-secondary hover:text-foreground hover:border-primary transition text-left"
              >
                {sq}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              askQuestion(question);
            }}
            className="p-2.5 border-t border-border bg-card flex items-center gap-2"
          >
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="আপনার প্রশ্ন লিখুন (Bangla বা English)..."
              aria-label="এআই সহকারীর কাছে প্রশ্ন লিখুন"
              className="flex-1 px-3 py-2 rounded-xl border border-border bg-surface text-xs text-foreground focus:outline-none focus:border-primary"
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              aria-label="প্রশ্ন পাঠান"
              className="p-2 rounded-xl bg-primary text-white disabled:opacity-50 hover:opacity-90"
            >
              <Send size={14} />
            </button>
          </form>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="পিজিসিবি প্রাতিষ্ঠানিক এআই সহকারী খুলুন"
          className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-primary text-white text-xs font-bold shadow-lg hover:opacity-95 transition"
        >
          <MessageCircle size={16} />
          <span className="hidden sm:inline">PGCB AI সহায়তা</span>
        </button>
      )}
    </div>
  );
}
