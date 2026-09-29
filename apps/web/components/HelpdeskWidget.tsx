'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  MessageCircle,
  X,
  Send,
  Sparkles,
  BookOpen,
  Wrench,
  AlertCircle,
  RotateCcw,
  ArrowRight,
  FileText,
} from 'lucide-react';
import { useLanguage } from '@/lib/i18n';

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
  relevance?: number;
  score?: number;
  view_source_url: string;
}

interface AIToolCall {
  tool_name: string;
  authorized: boolean;
}

interface AIActionItem {
  type?: string;
  action?: string;
  label: string;
  label_bn?: string;
  url: string;
}

interface ChatMessage {
  role: 'assistant' | 'user';
  text_bn: string;
  text_en?: string;
  confidence?: number;
  confidence_state?: 'HIGH' | 'MEDIUM' | 'LOW';
  unanswered?: boolean;
  security_flagged?: boolean;
  sources?: AISourceCitation[];
  tools_used?: AIToolCall[];
  actions?: AIActionItem[];
  fallback_actions?: AIActionItem[];
  links?: SuggestedLink[];
}

interface QuickActionChip {
  id: string;
  label_bn: string;
  label_en: string;
  question_bn: string;
  question_en: string;
  targetMode?: 'PUBLIC' | 'MEMBER' | 'ADMIN';
}

const QUICK_ACTIONS: QuickActionChip[] = [
  {
    id: 'membership',
    label_bn: 'সদস্যপদ সম্পর্কে জানুন',
    label_en: 'Membership',
    question_bn: 'PGCB membership নিতে কী কী লাগবে?',
    question_en: 'What are the eligibility criteria and documents required for PGCB membership?',
    targetMode: 'PUBLIC',
  },
  {
    id: 'my_membership',
    label_bn: 'আমার সদস্যপদ',
    label_en: 'My Membership',
    question_bn: 'আমার সদস্যপদের অবস্থা কী?',
    question_en: 'What is my membership status and my id?',
    targetMode: 'MEMBER',
  },
  {
    id: 'payment_status',
    label_bn: 'Payment Status',
    label_en: 'Payment Status',
    question_bn: 'আমার শেষ payment কবে করেছি?',
    question_en: 'Show my payment history and receipts',
    targetMode: 'MEMBER',
  },
  {
    id: 'certificates',
    label_bn: 'Certificate যাচাই',
    label_en: 'Certificates',
    question_bn: 'আমার certificate কোথায়?',
    question_en: 'Where is my membership certificate?',
    targetMode: 'MEMBER',
  },
  {
    id: 'circulars',
    label_bn: 'Latest Circulars',
    label_en: 'Latest Circulars',
    question_bn: 'নতুন circular কী আছে?',
    question_en: 'What are the latest official circulars?',
    targetMode: 'PUBLIC',
  },
  {
    id: 'events',
    label_bn: 'Events',
    label_en: 'Events',
    question_bn: 'আসন্ন ইভেন্ট ও সভা কী কী আছে?',
    question_en: 'What upcoming events and meetings are scheduled?',
    targetMode: 'PUBLIC',
  },
  {
    id: 'documents',
    label_bn: 'Documents',
    label_en: 'Documents',
    question_bn: 'membership renewal-এর official document কোনটা?',
    question_en: 'Which official documents exist for membership renewal?',
    targetMode: 'PUBLIC',
  },
  {
    id: 'contact',
    label_bn: 'Contact Secretariat',
    label_en: 'Contact Secretariat',
    question_bn: 'সচিবালয়ে যোগাযোগের ঠিকানা ও ফোন নম্বর কী?',
    question_en: 'How can I contact the PGCB Secretariat?',
    targetMode: 'PUBLIC',
  },
];

const SAMPLE_QUESTIONS_BY_MODE: Record<'PUBLIC' | 'MEMBER' | 'ADMIN', { bn: string; en: string }[]> = {
  PUBLIC: [
    {
      bn: 'সদস্যপদ নবায়ন কীভাবে করব এবং ফি কত?',
      en: 'How do I renew my membership and how much is the fee?',
    },
    {
      bn: 'PGCB membership নিতে কী লাগে?',
      en: 'Who is eligible for PGCB membership?',
    },
    {
      bn: 'সর্বশেষ circular কী?',
      en: 'What are the latest circulars?',
    },
  ],
  MEMBER: [
    {
      bn: 'আমার সদস্যপদের অবস্থা কী?',
      en: 'What is my membership status and my id?',
    },
    {
      bn: 'আমার শেষ payment কত ছিল?',
      en: 'Show my payment history and receipts',
    },
    {
      bn: 'আমার certificate দেখাও।',
      en: 'Where is my membership certificate?',
    },
  ],
  ADMIN: [
    {
      bn: 'এই মাসে কতগুলো membership application এসেছে?',
      en: 'How many membership applications arrived this month?',
    },
    {
      bn: 'কোন circle-এ pending application সবচেয়ে বেশি?',
      en: 'Which Circles have the highest number of pending applications?',
    },
    {
      bn: 'বর্তমানে মোট কতজন সক্রিয় সদস্য নিবন্ধিত আছেন?',
      en: 'How many active members are currently registered?',
    },
  ],
};

function getInitialGreeting(): ChatMessage {
  return {
    role: 'assistant',
    text_bn:
      '👋 আসসালামু আলাইকুম!\nআমি PGCB Institutional Assistant. গঠনতন্ত্র, সদস্যপদ নির্দেশিকা ২০২৬, বার্ষিক নবায়ন ফি, সার্কুলার বা আপনার সদস্যপদ স্ট্যাটাস বিষয়ে কীভাবে সাহায্য করতে পারি?',
    text_en:
      '👋 Assalamu Alaikum!\nI am the PGCB Institutional Assistant. How can I help you with membership guidelines, circulars, renewals, certificates, or your personal status today?',
    links: [
      { label_bn: 'সদস্যপদ আবেদন', label_en: 'Apply for Membership', url: '/membership/apply' },
      { label_bn: 'এআই নথি অনুসন্ধান', label_en: 'AI Document Search', url: '/search' },
    ],
  };
}

export function HelpdeskWidget() {
  const { language, setLanguage, t } = useLanguage();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<'PUBLIC' | 'MEMBER' | 'ADMIN'>('PUBLIC');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<ChatMessage[]>([getInitialGreeting()]);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
      }
      let sid = window.localStorage.getItem('pgcb_ai_session_id');
      if (!sid) {
        sid = `sess-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        window.localStorage.setItem('pgcb_ai_session_id', sid);
      }
      setSessionId(sid);
      const savedConv = window.localStorage.getItem('pgcb_ai_conversation_id');
      if (savedConv && !Number.isNaN(Number(savedConv))) {
        setConversationId(Number(savedConv));
      }
    }
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading, open]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  const handleResetConversation = async () => {
    if (conversationId) {
      fetch(`/backend/api/v1/ai/conversations/${conversationId}?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'DELETE',
        credentials: 'include',
      }).catch(() => {});
    }
    setConversationId(null);
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('pgcb_ai_conversation_id');
    }
    setMessages([getInitialGreeting()]);
  };

  const askQuestion = async (qText: string, overrideMode?: 'PUBLIC' | 'MEMBER' | 'ADMIN') => {
    const trimmed = qText.trim();
    if (!trimmed || loading) return;
    const activeMode = overrideMode || mode;
    if (overrideMode && overrideMode !== mode) {
      setMode(overrideMode);
    }

    setMessages((prev) => [...prev, { role: 'user', text_bn: trimmed, text_en: trimmed }]);
    setQuestion('');
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/ai/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: trimmed,
          mode: activeMode,
          language,
          conversation_id: conversationId,
          session_id: sessionId,
        }),
      });

      if (res.status === 401 || res.status === 403) {
        const errData = await res.json().catch(() => ({}));
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text_bn:
              errData.detail ||
              (activeMode === 'MEMBER'
                ? 'সদস্য-নির্দিষ্ট তথ্য (সদস্যপদ স্ট্যাটাস, পেমেন্ট রসিদ, সনদপত্র) দেখতে অনুগ্রহ করে প্রথমে লগইন করুন।'
                : 'অ্যাডমিন এআই মোড শুধুমাত্র অনুমোদিত প্রশাসকদের জন্য সংরক্ষিত।'),
            text_en:
              errData.detail ||
              (activeMode === 'MEMBER'
                ? 'Please sign in to access personal member tools (membership status, payment receipts, and certificates).'
                : 'Admin AI mode is restricted to authorized administrators.'),
            links: [{ label_bn: 'লগইন করুন', label_en: 'Login to Portal', url: '/login' }],
          },
        ]);
        return;
      }

      if (!res.ok) throw new Error('Failed');
      const data = await res.json();

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('pgcb_ai_conversation_id', String(data.conversation_id));
        }
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn: data.answer_bn || data.answer || 'আপনার প্রশ্নের উত্তর পাওয়া গেছে।',
          text_en: data.answer_en || data.answer,
          confidence: typeof data.confidence === 'number' ? data.confidence : undefined,
          confidence_state: data.confidence_state,
          unanswered: data.unanswered,
          security_flagged: data.security_flagged,
          sources: data.sources || [],
          tools_used: data.tools_used || [],
          actions: data.actions || (data.action ? [data.action] : []),
          fallback_actions: data.fallback_actions || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn:
            'দুঃখিত, এই মুহূর্তে এআই সার্ভিসে সংযোগ দেওয়া যাচ্ছে না। অনুগ্রহ করে সার্কুলার, ডকুমেন্টস বা যোগাযোগ পেজ দেখুন।',
          text_en:
            'Sorry, the AI Assistant service is temporarily unreachable. Please check Circulars, Documents, or Contact Secretariat.',
          links: [
            { label_bn: 'সার্কুলার দেখুন', label_en: 'View Circulars', url: '/circulars' },
            { label_bn: 'ডকুমেন্টস দেখুন', label_en: 'Browse Documents', url: '/documents' },
            { label_bn: 'যোগাযোগ', label_en: 'Contact Secretariat', url: '/contact' },
          ],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderConfidenceBadge = (m: ChatMessage) => {
    if (m.role !== 'assistant' || m.confidence === undefined) return null;
    const pct = Math.round(m.confidence * 100);
    const state = m.confidence_state || (m.unanswered || pct < 35 ? 'LOW' : pct >= 70 ? 'HIGH' : 'MEDIUM');

    if (state === 'HIGH') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 text-[10px] font-bold">
          <span>🟢</span>
          <span>{language === 'en' ? `High Confidence · ${pct}%` : `নির্ভরযোগ্য সূত্র · ${pct}%`}</span>
        </span>
      );
    }
    if (state === 'MEDIUM') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 border border-amber-500/20 text-[10px] font-bold">
          <span>🟡</span>
          <span>{language === 'en' ? `Medium Confidence · ${pct}%` : `আংশিক নিশ্চিত · ${pct}%`}</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-700 border border-rose-500/20 text-[10px] font-bold">
        <span>🔴</span>
        <span>{language === 'en' ? 'No Verified Match' : 'প্রামাণ্য তথ্য পাওয়া যায়নি'}</span>
      </span>
    );
  };

  return (
    <div className="fixed bottom-16 md:bottom-6 right-4 md:right-6 z-50">
      {open ? (
        <div
          role="dialog"
          aria-modal="false"
          aria-label="PGCB AI Assistant"
          className="w-[355px] sm:w-[430px] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[630px]"
        >
          {/* Top Header */}
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-400/30 text-emerald-300">
                <Sparkles size={16} />
                <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 ring-2 ring-slate-900" />
              </div>
              <div>
                <div className="text-xs font-extrabold tracking-tight flex items-center gap-1.5">
                  <span>PGCB AI Assistant</span>
                </div>
                <div className="text-[10px] text-slate-300">
                  {t('প্রাতিষ্ঠানিক এআই সহকারী', 'Institutional Assistant')}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {/* Bangla | English Language Switcher inside Chat Window */}
              <div className="inline-flex rounded-lg bg-slate-800 p-0.5 border border-slate-700 text-[10px] font-bold">
                <button
                  type="button"
                  onClick={() => setLanguage('bn')}
                  className={`px-2 py-0.5 rounded-md transition ${
                    language === 'bn' ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  বাংলা
                </button>
                <button
                  type="button"
                  onClick={() => setLanguage('en')}
                  className={`px-2 py-0.5 rounded-md transition ${
                    language === 'en' ? 'bg-emerald-600 text-white' : 'text-slate-300 hover:text-white'
                  }`}
                >
                  EN
                </button>
              </div>

              <button
                type="button"
                title={t('নতুন কথোপকথন শুরু করুন', 'Start New Conversation')}
                onClick={handleResetConversation}
                className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition"
              >
                <RotateCcw size={14} />
              </button>

              <button
                type="button"
                aria-label="চ্যাট বন্ধ করুন"
                onClick={() => setOpen(false)}
                className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* 3-Mode Selector: Public | Member | Admin */}
          <div className="px-3.5 py-2 bg-surface border-b border-border flex items-center justify-between gap-2 text-[11px]">
            <span className="text-secondary font-semibold">
              {t('মোড:', 'Mode:')}
            </span>
            <div className="flex gap-1">
              {(['PUBLIC', 'MEMBER', 'ADMIN'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`px-2.5 py-0.5 rounded-lg font-bold transition ${
                    mode === m
                      ? 'bg-primary text-white shadow-sm'
                      : 'bg-card border border-border text-secondary hover:text-foreground'
                  }`}
                >
                  {m === 'PUBLIC'
                    ? t('সাধারণ (Public)', 'Public')
                    : m === 'MEMBER'
                    ? t('সদস্য (Member)', 'Member')
                    : t('অ্যাডমিন (Admin)', 'Admin')}
                </button>
              ))}
            </div>
          </div>

          {/* Quick Actions Bar */}
          <div className="px-3 py-2 bg-slate-50/80 border-b border-border">
            <div className="text-[10px] font-bold text-secondary mb-1.5 uppercase tracking-wider">
              {t('দ্রুত সেবা (Quick Actions)', 'Quick Actions')}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_ACTIONS.map((qa) => (
                <button
                  key={qa.id}
                  type="button"
                  onClick={() =>
                    askQuestion(
                      language === 'en' ? qa.question_en : qa.question_bn,
                      qa.targetMode
                    )
                  }
                  className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 hover:border-primary hover:text-primary font-semibold text-[11px] shadow-2xs transition"
                >
                  {language === 'en' ? qa.label_en : qa.label_bn}
                </button>
              ))}
            </div>
          </div>

          {/* Messages Feed */}
          <div
            ref={scrollRef}
            className="p-3.5 space-y-3.5 overflow-y-auto flex-1 bg-surface/40 text-xs max-h-[320px]"
          >
            {messages.map((m, idx) => {
              const displayMsg =
                language === 'en' ? m.text_en || m.text_bn : m.text_bn || m.text_en;
              return (
                <div
                  key={idx}
                  className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  {/* Confidence & Tool Badges */}
                  {m.role === 'assistant' &&
                    (m.confidence !== undefined || (m.tools_used && m.tools_used.length > 0)) && (
                      <div className="flex flex-wrap items-center gap-1.5 mb-1">
                        {renderConfidenceBadge(m)}
                        {m.tools_used &&
                          m.tools_used.slice(0, 2).map((tItem, tIdx) => (
                            <span
                              key={tIdx}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-700 border border-blue-500/20 text-[10px] font-semibold"
                            >
                              <Wrench size={10} />
                              <span>{tItem.tool_name}</span>
                            </span>
                          ))}
                      </div>
                    )}

                  <div
                    className={`rounded-2xl px-3.5 py-2.5 max-w-[94%] whitespace-pre-line leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-primary text-white'
                        : m.security_flagged
                        ? 'bg-red-50 border border-red-300 text-red-900'
                        : 'bg-card border border-border text-foreground shadow-sm'
                    }`}
                  >
                    {displayMsg}
                  </div>

                  {/* Authoritative Document Citations */}
                  {m.sources && m.sources.length > 0 && (
                    <div className="mt-1.5 w-[94%] rounded-xl bg-card border border-border p-2.5 space-y-2 shadow-2xs">
                      <div className="flex items-center gap-1.5 text-[10px] font-bold text-primary uppercase tracking-wide">
                        <BookOpen size={11} />
                        <span>{t('প্রামাণ্য নথির সূত্র (Source Citations)', 'Official Source Citations')}</span>
                      </div>
                      {m.sources.map((src, sIdx) => (
                        <div
                          key={sIdx}
                          className="text-[11px] flex items-start justify-between gap-2 border-t border-border/50 pt-1.5 first:border-0 first:pt-0"
                        >
                          <div className="space-y-0.5">
                            <div className="font-bold text-foreground flex items-center gap-1">
                              <FileText size={11} className="text-primary shrink-0" />
                              <span>{language === 'en' ? src.title : src.title_bn || src.title}</span>
                            </div>
                            <div className="text-[10px] text-secondary">
                              {src.section ? `${src.section}` : 'Official Section'}
                              {src.page ? ` · ${t('পৃষ্ঠা', 'Page')} ${src.page}` : ''}
                              {src.version ? ` · v${src.version}` : ''}
                            </div>
                          </div>
                          <a
                            href={`/backend${src.view_source_url}`}
                            target="_blank"
                            rel="noreferrer"
                            className="shrink-0 px-2 py-1 rounded-lg bg-primary/10 text-primary font-bold text-[10px] hover:bg-primary/20 transition"
                          >
                            {t('সূত্র দেখুন', 'Open Source')}
                          </a>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Structured Actions / Navigation Buttons */}
                  {m.actions && m.actions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {m.actions.map((act, aIdx) => (
                        <Link
                          key={aIdx}
                          href={act.url}
                          onClick={() => setOpen(false)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-emerald-600 text-white font-bold text-[11px] hover:bg-emerald-700 shadow-sm transition"
                        >
                          <span>{language === 'en' ? act.label : act.label_bn || act.label}</span>
                          <ArrowRight size={12} />
                        </Link>
                      ))}
                    </div>
                  )}

                  {/* Safe "No Answer" Fallback Actions */}
                  {m.unanswered && m.fallback_actions && m.fallback_actions.length > 0 && (
                    <div className="mt-1.5 w-[94%] rounded-xl bg-amber-500/10 border border-amber-500/30 p-2.5 space-y-1.5">
                      <div className="flex items-center gap-1 text-[10px] font-bold text-amber-800">
                        <AlertCircle size={11} />
                        <span>{t('বিকল্প প্রামাণ্য মাধ্যম:', 'Authoritative Fallback Options:')}</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.fallback_actions.map((fb, fIdx) => (
                          <Link
                            key={fIdx}
                            href={fb.url}
                            onClick={() => setOpen(false)}
                            className="px-2.5 py-1 rounded-lg bg-card border border-amber-500/40 text-foreground font-semibold text-[11px] hover:border-primary"
                          >
                            {language === 'en' ? fb.label : fb.label_bn || fb.label} →
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
                          {language === 'en' ? lnk.label_en || lnk.label_bn : lnk.label_bn} →
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
            {loading && (
              <div className="text-[11px] text-secondary italic px-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
                <span>
                  {t(
                    'প্রামাণ্য নথিপত্র ও ডাটাবেজ যাচাই করে উত্তর প্রস্তুত হচ্ছে...',
                    'Verifying authoritative PGCB documents and records...'
                  )}
                </span>
              </div>
            )}
          </div>

          {/* Sample Questions for Active Mode */}
          <div className="px-3 py-2 border-t border-border bg-card flex flex-wrap gap-1">
            {SAMPLE_QUESTIONS_BY_MODE[mode].map((sq, i) => {
              const qLabel = language === 'en' ? sq.en : sq.bn;
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => askQuestion(qLabel)}
                  className="text-[10px] px-2 py-1 rounded-md bg-surface border border-border text-secondary hover:text-foreground hover:border-primary transition text-left"
                >
                  {qLabel}
                </button>
              );
            })}
          </div>

          {/* Input Form */}
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
              placeholder={t(
                'PGCB Assistant-কে প্রশ্ন করুন (বাংলা বা English)...',
                'Ask PGCB Assistant (Bangla or English)...'
              )}
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
          <span className="hidden sm:inline">
            {t('PGCB AI সহায়তা', 'PGCB AI Assistant')}
          </span>
        </button>
      )}
    </div>
  );
}
