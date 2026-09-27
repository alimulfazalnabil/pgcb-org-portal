'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageCircle, X, Send, Sparkles, Home, Bell, Calendar, CreditCard, UserCheck } from 'lucide-react';

interface SuggestedLink {
  label_bn: string;
  label_en: string;
  url: string;
}

interface ChatMessage {
  role: 'assistant' | 'user';
  text_bn: string;
  text_en?: string;
  links?: SuggestedLink[];
}

const SAMPLE_QUESTIONS = [
  'কিভাবে সদস্যপদ আবেদন করব?',
  'সদস্যপদ ফি ও বার্ষিক নবায়ন চার্জ কত?',
  'ডিজিটাল আইডি কার্ড ও সনদপত্র কিভাবে যাচাই করা যায়?',
  'সর্বশেষ সার্কুলার ও আসন্ন ইভেন্ট কী কী?',
];

export function HelpdeskWidget() {
  const pathname = usePathname() || '/';
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      text_bn:
        'স্বাগতম! আমি পিজিসিবি সহায়তা সহকারী (PGCB Assistant)। গঠনতন্ত্র, সদস্যপদ আবেদন, ফি ও রসিদ, সার্কুলার, ইভেন্ট অথবা সনদ যাচাই বিষয়ে যেকোনো প্রশ্ন করুন।',
      links: [
        { label_bn: 'সদস্যপদ আবেদন', label_en: 'Apply', url: '/apply' },
        { label_bn: 'সনদ যাচাই', label_en: 'Verify Certificate', url: '/verify-certificate' },
      ],
    },
  ]);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);

  const askQuestion = async (qText: string) => {
    const trimmed = qText.trim();
    if (!trimmed || loading) return;
    setMessages((prev) => [...prev, { role: 'user', text_bn: trimmed }]);
    setQuestion('');
    setLoading(true);
    try {
      const res = await fetch('/backend/api/v1/public/helpdesk/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed, language: 'bn' }),
      });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn: data.answer_bn || 'আপনার প্রশ্নের উত্তর পাওয়া গেছে।',
          text_en: data.answer_en,
          links: data.suggested_links || [],
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text_bn:
            'দুঃখিত, এই মুহূর্তে সার্ভারে সংযোগ দেওয়া যাচ্ছে না। অনুগ্রহ করে `/apply`, `/circulars`, অথবা `/contact` পেজ দেখুন।',
          links: [{ label_bn: 'যোগাযোগ', label_en: 'Contact', url: '/contact' }],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const isAdminRoute = pathname.startsWith('/admin');

  return (
    <>
      {/* Mobile Bottom Navigation Bar (PWA / Mobile Portal) */}
      {!isAdminRoute && (
        <nav
          aria-label="মোবাইল নেভিগেশন"
          className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-card/95 backdrop-blur border-t border-border px-2 py-1.5 flex items-center justify-around text-[11px] font-semibold shadow-lg"
        >
          <Link
            href="/"
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg ${
              pathname === '/' ? 'text-primary font-bold' : 'text-secondary'
            }`}
          >
            <Home size={16} />
            <span>হোম</span>
          </Link>
          <Link
            href="/notices"
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg ${
              pathname.startsWith('/notices') ? 'text-primary font-bold' : 'text-secondary'
            }`}
          >
            <Bell size={16} />
            <span>নোটিশ</span>
          </Link>
          <Link
            href="/events"
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg ${
              pathname.startsWith('/events') ? 'text-primary font-bold' : 'text-secondary'
            }`}
          >
            <Calendar size={16} />
            <span>ইভেন্ট</span>
          </Link>
          <Link
            href="/portal/id-card"
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg ${
              pathname.startsWith('/portal/id-card') ? 'text-primary font-bold' : 'text-secondary'
            }`}
          >
            <CreditCard size={16} />
            <span>আইডি কার্ড</span>
          </Link>
          <Link
            href="/portal"
            className={`flex flex-col items-center gap-0.5 px-2 py-1 rounded-lg ${
              pathname === '/portal' ? 'text-primary font-bold' : 'text-secondary'
            }`}
          >
            <UserCheck size={16} />
            <span>পোর্টাল</span>
          </Link>
        </nav>
      )}

      {/* Floating PGCB Assistant Helpdesk Button */}
      <div className="fixed bottom-16 md:bottom-6 right-4 md:right-6 z-50">
        {open ? (
          <div
            role="dialog"
            aria-label="PGCB সহায়তা সহকারী"
            className="w-[340px] sm:w-[380px] bg-card border border-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[520px]"
          >
            <div className="bg-primary text-white px-4 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={16} />
                <div>
                  <div className="text-xs font-bold">পিজিসিবি সহায়তা সহকারী</div>
                  <div className="text-[10px] opacity-80">PGCB Institutional AI Helpdesk</div>
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

            <div className="p-3 space-y-3 overflow-y-auto flex-1 bg-surface/40 text-xs max-h-[310px]">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`rounded-2xl px-3.5 py-2.5 max-w-[90%] whitespace-pre-line leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-primary text-white'
                        : 'bg-card border border-border text-foreground shadow-sm'
                    }`}
                  >
                    {m.text_bn}
                  </div>
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
                <div className="text-[11px] text-secondary italic px-2">উত্তর প্রস্তুত হচ্ছে...</div>
              )}
            </div>

            <div className="px-3 py-2 border-t border-border bg-card flex flex-wrap gap-1">
              {SAMPLE_QUESTIONS.map((sq, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => askQuestion(sq)}
                  className="text-[10px] px-2 py-1 rounded-md bg-surface border border-border text-secondary hover:text-foreground hover:border-primary transition"
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
                placeholder="আপনার প্রশ্ন লিখুন..."
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
            aria-label="পিজিসিবি সহায়তা সহকারী খুলুন"
            className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-primary text-white text-xs font-bold shadow-lg hover:opacity-95 transition"
          >
            <MessageCircle size={16} />
            <span className="hidden sm:inline">পিজিসিবি সহায়তা</span>
          </button>
        )}
      </div>
    </>
  );
}
