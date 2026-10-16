'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Bot,
  Sparkles,
  Send,
  Mic,
  MicOff,
  User,
  Plus,
  Trash2,
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  CreditCard,
  FileText,
  Calendar,
  Award,
  ArrowRight,
  ExternalLink,
  MessageSquare,
  History,
  X,
  RefreshCw,
  LifeBuoy,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import {
  MemberAIChatResponse,
  MemberAIChatAction,
  MemberAIChatSource,
  MemberAIConfirmationPayload,
  MemberAIConversation,
} from '@/lib/api/types';

interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  actions?: MemberAIChatAction[];
  sources?: MemberAIChatSource[];
  confirmation?: MemberAIConfirmationPayload | null;
  requires_confirmation?: boolean;
  security_flagged?: boolean;
  is_unanswered?: boolean;
  tools_used?: string[];
}

export default function MemberAIAssistantPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<MemberAIConversation[]>([]);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);

  // Escalation Modal
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [ticketSubject, setTicketSubject] = useState('');
  const [ticketDescription, setTicketDescription] = useState('');
  const [ticketCategory, setTicketCategory] = useState('MEMBERSHIP');
  const [ticketPriority, setTicketPriority] = useState('NORMAL');
  const [escalating, setEscalating] = useState(false);
  const [escalateSuccess, setEscalateSuccess] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  const isEn = lang === 'en';

  const defaultPrompts = [
    {
      en: 'What is my membership status?',
      bn: 'আমার সদস্যপদের অবস্থা কী?',
      icon: Sparkles,
    },
    {
      en: 'Do I have any pending documents?',
      bn: 'আমার কোন documents এখনও pending?',
      icon: FileText,
    },
    {
      en: 'Show my recent payments',
      bn: 'আমার শেষ payment ও রসিদ দেখাও',
      icon: CreditCard,
    },
    {
      en: 'Check profile completion',
      bn: 'আমার প্রোফাইল কতটুকু সম্পন্ন?',
      icon: CheckCircle2,
    },
    {
      en: 'My registered events & pass',
      bn: 'আমার ইভেন্ট রেজিস্ট্রেশন ও পাস',
      icon: Calendar,
    },
  ];

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        setSpeechSupported(true);
        const recog = new SpeechRecognition();
        recog.continuous = false;
        recog.interimResults = false;
        recog.lang = lang === 'bn' ? 'bn-BD' : 'en-US';

        recog.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          if (transcript) {
            setInputMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
          }
          setIsListening(false);
        };

        recog.onerror = () => {
          setIsListening(false);
        };

        recog.onend = () => {
          setIsListening(false);
        };

        recognitionRef.current = recog;
      }
    }
  }, [lang]);

  // Load conversation history list
  const loadConversations = async () => {
    try {
      const list = await membersApi.getMemberAIConversations();
      setConversations(list || []);
    } catch {
      // Non-blocking
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const toggleVoiceInput = () => {
    if (!speechSupported || !recognitionRef.current) {
      alert(
        isEn
          ? 'Voice speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge.'
          : 'এই ব্রাউজারে ভয়েস রিকগনিশন সমর্থন করে না। গুগল ক্রোম বা এজ ব্যবহার করুন।'
      );
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.lang = lang === 'bn' ? 'bn-BD' : 'en-US';
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        setIsListening(false);
      }
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    setInputMessage('');
    const nowIso = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Append user message immediately
    const userTurn: ChatTurn = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: nowIso,
    };
    setMessages((prev) => [...prev, userTurn]);
    setLoading(true);

    try {
      const res: MemberAIChatResponse = await membersApi.sendMemberAIChat({
        message: query,
        conversation_id: activeConversationId,
        language: lang,
      });

      if (res.conversation_id && res.conversation_id !== activeConversationId) {
        setActiveConversationId(res.conversation_id);
        loadConversations();
      }

      const botTurn: ChatTurn = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: isEn ? (res.answer_en || res.message) : (res.answer_bn || res.message),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        actions: res.actions || [],
        sources: res.sources || [],
        confirmation: res.confirmation || null,
        requires_confirmation: !!res.requires_confirmation,
        security_flagged: !!res.security_flagged,
        is_unanswered: res.status === 'UNANSWERED',
        tools_used: res.tools_used || [],
      };

      setMessages((prev) => [...prev, botTurn]);
    } catch (err: any) {
      const errorMsg =
        err?.message ||
        (isEn
          ? 'An error occurred while connecting to PGCB AI Assistant. Please try again.'
          : 'পিজিসিবি এআই সহকারীর সাথে সংযোগে সমস্যা হয়েছে। আবার চেষ্টা করুন।');

      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: errorMsg,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          security_flagged: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleStartNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setShowHistoryDrawer(false);
  };

  const handleSelectConversation = async (convId: number) => {
    try {
      setLoading(true);
      setShowHistoryDrawer(false);
      setActiveConversationId(convId);
      const detail = await membersApi.getMemberAIConversationDetail(convId);

      const restored: ChatTurn[] = (detail.messages || []).map((m) => ({
        id: `m-${m.id}`,
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: isEn ? (m.content_en || m.content) : (m.content_bn || m.content),
        timestamp: m.created_at
          ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : '',
        actions: m.actions || [],
        sources: m.sources || [],
      }));
      setMessages(restored);
    } catch (err) {
      // Failed to load conversation detail
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, convId: number) => {
    e.stopPropagation();
    if (
      !confirm(
        isEn
          ? 'Are you sure you want to delete this conversation?'
          : 'আপনি কি নিশ্চিত যে এই কথোপকথনটি মুছে ফেলতে চান?'
      )
    )
      return;

    try {
      await membersApi.deleteMemberAIConversation(convId);
      if (activeConversationId === convId) {
        handleStartNewChat();
      }
      loadConversations();
    } catch {
      // handle error
    }
  };

  const handleOpenEscalation = (initialSubject = '') => {
    setTicketSubject(initialSubject || (isEn ? 'AI Assistance Support Request' : 'এআই সহায়তার অনুরোধ'));
    setTicketDescription(
      messages.length > 0
        ? `${isEn ? 'Recent Question:' : 'সাম্প্রতিক প্রশ্ন:'} ${
            messages[messages.length - 2]?.content || ''
          }\n\n${isEn ? 'Details:' : 'বিস্তারিত বিবরণ:'} `
        : ''
    );
    setEscalateSuccess(null);
    setShowEscalateModal(true);
  };

  const handleSubmitEscalation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticketSubject.trim() || !ticketDescription.trim()) return;

    try {
      setEscalating(true);
      const res = await membersApi.createMemberAISupportTicket({
        conversation_id: activeConversationId,
        subject: ticketSubject.trim(),
        description: ticketDescription.trim(),
        category: ticketCategory,
        priority: ticketPriority,
      });

      setEscalateSuccess(
        isEn
          ? `Support ticket created successfully (#${res.ticket.ticket_no}). The Secretariat will review it shortly.`
          : `সাপোর্ট টিকিট সফলভাবে খোলা হয়েছে (#${res.ticket.ticket_no})। সচিবালয় শীঘ্রই এটি পর্যালোচনা করবে।`
      );

      // Append confirmation turn in chat
      setMessages((prev) => [
        ...prev,
        {
          id: `asst-esc-${Date.now()}`,
          role: 'assistant',
          content: isEn
            ? `A human support ticket **#${res.ticket.ticket_no}** has been registered with the PGCB Secretariat.\n\nYou can track the progress in your Support Center.`
            : `পিজিসিবি সচিবালয়ে আপনার সাপোর্ট টিকিট **#${res.ticket.ticket_no}** নিবন্ধিত হয়েছে।\n\nআপনি সাপোর্ট সেন্টার থেকে অগ্রগতি ট্র্যাক করতে পারেন।`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          actions: [
            {
              action: 'VIEW_SUPPORT_TICKETS',
              label: 'View Support Tickets',
              label_bn: 'সাপোর্ট টিকিটসমূহ দেখুন',
              url: '/member/support',
              is_primary: true,
            },
          ],
        },
      ]);

      setTimeout(() => {
        setShowEscalateModal(false);
      }, 2500);
    } catch (err: any) {
      alert(err?.message || (isEn ? 'Failed to create ticket' : 'টিকিট তৈরিতে ব্যর্থ হয়েছে'));
    } finally {
      setEscalating(false);
    }
  };

  return (
    <MemberLayout title={isEn ? 'AI Assistant' : 'এআই সহকারী'}>
      <div className="flex flex-col h-[calc(100vh-140px)] max-h-[920px] bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Header Bar */}
        <div className="px-6 py-4 bg-gradient-to-r from-emerald-800 to-teal-900 text-white flex items-center justify-between shadow-sm shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-700/80 border border-emerald-500/30 flex items-center justify-center text-emerald-100 shadow-inner">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight">PGCB AI ASSISTANT</h1>
                <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 rounded-full">
                  Member Aware
                </span>
              </div>
              <p className="text-xs text-emerald-200/90 font-medium">
                {isEn
                  ? 'Your intelligent member support assistant'
                  : 'আপনার বুদ্ধিমান মেম্বার সাপোর্ট সহকারী'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Toggle */}
            <button
              onClick={() => setLang(isEn ? 'bn' : 'en')}
              className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-emerald-700/50 hover:bg-emerald-700 text-emerald-100 border border-emerald-600/40 transition-colors"
            >
              {isEn ? 'বাংলা' : 'English'}
            </button>

            {/* Support Ticket Quick Link */}
            <Link
              href="/member/support"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-700/50 hover:bg-emerald-700 text-emerald-100 border border-emerald-600/40 transition-colors"
            >
              <LifeBuoy className="w-3.5 h-3.5" />
              <span>{isEn ? 'Support' : 'সাপোর্ট'}</span>
            </Link>

            {/* Conversation History Drawer Toggle */}
            <button
              onClick={() => setShowHistoryDrawer(!showHistoryDrawer)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-700/50 hover:bg-emerald-700 text-emerald-100 border border-emerald-600/40 transition-colors"
              title={isEn ? 'Chat History' : 'কথোপকথন ইতিহাস'}
            >
              <History className="w-3.5 h-3.5" />
              <span className="hidden md:inline">{isEn ? 'History' : 'ইতিহাস'}</span>
            </button>

            {/* New Chat Button */}
            <button
              onClick={handleStartNewChat}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500 hover:bg-emerald-400 text-emerald-950 transition-colors shadow-sm"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{isEn ? 'New Chat' : 'নতুন চ্যাট'}</span>
            </button>
          </div>
        </div>

        {/* Main Chat Body & Sidebar Drawer */}
        <div className="flex flex-1 overflow-hidden relative">
          {/* Messages Area */}
          <div className="flex-1 flex flex-col justify-between overflow-hidden bg-slate-50/50">
            {/* Messages Scroll Container */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
              {messages.length === 0 ? (
                /* Welcome Greeting & Quick Prompt Chips */
                <div className="max-w-2xl mx-auto py-8 sm:py-12 flex flex-col items-center text-center">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-100 border border-emerald-200 text-emerald-700 flex items-center justify-center mb-4 shadow-sm">
                    <Bot className="w-9 h-9" />
                  </div>
                  <h2 className="text-xl font-bold text-slate-800 mb-2">
                    {isEn ? 'Hello! How can I help you today?' : 'নমস্কার! আজ আপনাকে কীভাবে সহায়তা করতে পারি?'}
                  </h2>
                  <p className="text-sm text-slate-500 max-w-md mb-8">
                    {isEn
                      ? 'Ask questions about your membership status, dues, certificates, documents, or general PGCB policies.'
                      : 'আপনার সদস্যপদের অবস্থা, ফি, সনদ, পেন্ডিং ডকুমেন্টস বা পিজিসিবি নীতি সংক্রান্ত যেকোনো তথ্য জানতে পারেন।'}
                  </p>

                  {/* Prompt Action Chips */}
                  <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                    {defaultPrompts.map((p, idx) => {
                      const IconComponent = p.icon;
                      return (
                        <button
                          key={idx}
                          onClick={() => handleSendMessage(isEn ? p.en : p.bn)}
                          className="flex items-center gap-3 p-3.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-500 hover:shadow-md transition-all group text-slate-700 hover:text-emerald-700"
                        >
                          <div className="w-9 h-9 rounded-lg bg-slate-100 group-hover:bg-emerald-50 text-slate-600 group-hover:text-emerald-600 flex items-center justify-center shrink-0 transition-colors">
                            <IconComponent className="w-5 h-5" />
                          </div>
                          <span className="text-sm font-medium leading-snug">
                            {isEn ? p.en : p.bn}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                /* Chat Messages Stream */
                <div className="space-y-6 max-w-3xl mx-auto">
                  {messages.map((turn) => {
                    const isUser = turn.role === 'user';
                    return (
                      <div
                        key={turn.id}
                        className={`flex gap-3 sm:gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
                      >
                        {/* Avatar */}
                        {!isUser && (
                          <div className="w-8 h-8 rounded-lg bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-1 shadow-sm">
                            <Bot className="w-4 h-4" />
                          </div>
                        )}

                        <div className={`max-w-[85%] sm:max-w-[78%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                          {/* Bubble */}
                          <div
                            className={`p-4 rounded-2xl text-sm leading-relaxed ${
                              isUser
                                ? 'bg-emerald-700 text-white rounded-br-none shadow-sm'
                                : turn.security_flagged
                                ? 'bg-amber-50 text-amber-900 border border-amber-300 rounded-bl-none'
                                : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                            }`}
                          >
                            {/* Security Notice Warning */}
                            {turn.security_flagged && (
                              <div className="flex items-center gap-2 mb-2 pb-2 border-b border-amber-200 text-amber-800 font-semibold text-xs">
                                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
                                <span>{isEn ? 'Security Notice' : 'নিরাপত্তা বিজ্ঞপ্তি'}</span>
                              </div>
                            )}

                            {/* Markdown/Text Body */}
                            <div className="whitespace-pre-wrap">{turn.content}</div>

                            {/* Safe Confirmation Card (e.g. Renewal confirmation before payment) */}
                            {turn.requires_confirmation && turn.confirmation && (
                              <div className="mt-4 p-3.5 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-950">
                                <div className="flex items-center gap-2 font-semibold text-xs mb-1.5">
                                  <AlertTriangle className="w-4 h-4 text-emerald-700" />
                                  <span>{isEn ? 'Action Confirmation Required' : 'নিশ্চিতকরণ প্রয়োজন'}</span>
                                </div>
                                <p className="text-xs text-slate-700 mb-3">
                                  {isEn ? turn.confirmation.message_en : turn.confirmation.message_bn}
                                </p>
                                <div className="flex items-center gap-2">
                                  <Link
                                    href={turn.confirmation.target_url}
                                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white flex items-center gap-1.5 transition-colors shadow-sm"
                                  >
                                    <span>{isEn ? 'Proceed to Payment' : 'পেমেন্ট সম্পন্ন করুন'}</span>
                                    <ArrowRight className="w-3.5 h-3.5" />
                                  </Link>
                                </div>
                              </div>
                            )}

                            {/* Interactive Action Buttons */}
                            {turn.actions && turn.actions.length > 0 && !turn.requires_confirmation && (
                              <div className="mt-3.5 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                                {turn.actions.map((act, actIdx) => (
                                  act.url ? (
                                    <Link
                                      key={actIdx}
                                      href={act.url}
                                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                                        act.is_primary
                                          ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm'
                                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300'
                                      }`}
                                    >
                                      <span>{isEn ? act.label : (act.label_bn || act.label)}</span>
                                      <ArrowRight className="w-3 h-3" />
                                    </Link>
                                  ) : (
                                    <button
                                      key={actIdx}
                                      onClick={() => {
                                        if (act.action === 'ESCALATE_SUPPORT') {
                                          handleOpenEscalation();
                                        }
                                      }}
                                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 transition-colors"
                                    >
                                      <span>{isEn ? act.label : (act.label_bn || act.label)}</span>
                                      <LifeBuoy className="w-3 h-3" />
                                    </button>
                                  )
                                ))}
                              </div>
                            )}

                            {/* Human Escalation Action for Unanswered queries */}
                            {turn.is_unanswered && (
                              <div className="mt-3 pt-3 border-t border-slate-100">
                                <button
                                  onClick={() => handleOpenEscalation()}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white transition-colors shadow-sm"
                                >
                                  <LifeBuoy className="w-3.5 h-3.5" />
                                  <span>{isEn ? 'Open Support Ticket' : 'সাপোর্ট টিকিট খুলুন'}</span>
                                </button>
                              </div>
                            )}

                            {/* Grounded Source Citations */}
                            {turn.sources && turn.sources.length > 0 && (
                              <div className="mt-3 pt-2.5 border-t border-slate-100 text-xs text-slate-500 space-y-1">
                                {turn.sources.slice(0, 2).map((s, sIdx) => (
                                  <div key={sIdx} className="flex items-center gap-1.5 text-slate-600">
                                    <span className="font-semibold text-emerald-700">📚 {isEn ? 'Source:' : 'সূত্র:'}</span>
                                    <span>
                                      {isEn ? s.title : (s.title_bn || s.title)} (
                                      {s.version ? `v${s.version}, ` : ''}
                                      {s.section ? `${s.section}, ` : ''}
                                      {s.page ? `Page ${s.page}` : ''})
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Timestamp */}
                          <span className="text-[10px] text-slate-400 mt-1 px-1">
                            {turn.timestamp}
                          </span>
                        </div>

                        {/* User Avatar */}
                        {isUser && (
                          <div className="w-8 h-8 rounded-lg bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 mt-1">
                            <User className="w-4 h-4" />
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Loading Indicator Turn */}
                  {loading && (
                    <div className="flex gap-3 items-start">
                      <div className="w-8 h-8 rounded-lg bg-emerald-700 text-white flex items-center justify-center shrink-0 mt-1">
                        <Bot className="w-4 h-4 animate-pulse" />
                      </div>
                      <div className="p-4 rounded-2xl bg-white border border-slate-200 rounded-bl-none shadow-sm flex items-center gap-2 text-slate-500 text-xs">
                        <RefreshCw className="w-4 h-4 animate-spin text-emerald-600" />
                        <span>{isEn ? 'Consulting PGCB institutional tools...' : 'প্রাতিষ্ঠানিক রেকর্ড যাচাই করা হচ্ছে...'}</span>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Input Bar Section */}
            <div className="p-3 sm:p-4 bg-white border-t border-slate-200">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="max-w-3xl mx-auto flex items-center gap-2"
              >
                {/* Voice Input Button */}
                <button
                  type="button"
                  onClick={toggleVoiceInput}
                  className={`p-2.5 rounded-xl border transition-all ${
                    isListening
                      ? 'bg-rose-500 text-white border-rose-600 animate-pulse shadow-md'
                      : 'bg-slate-50 hover:bg-slate-100 text-slate-600 border-slate-300'
                  }`}
                  title={
                    isListening
                      ? (isEn ? 'Listening... click to stop' : 'শুনছি... বন্ধ করতে ক্লিক করুন')
                      : (isEn ? 'Click to speak' : 'কথা বলতে ক্লিক করুন')
                  }
                >
                  {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                {/* Text Input */}
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={
                    isListening
                      ? (isEn ? 'Listening... speak now' : 'শুনছি... এখন কথা বলুন')
                      : (isEn ? 'Ask PGCB AI...' : 'পিজিসিবি এআই-কে জিজ্ঞাসা করুন...')
                  }
                  disabled={loading}
                  className="flex-1 px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white text-slate-900 placeholder-slate-400 disabled:opacity-60 transition-all"
                />

                {/* Send Button */}
                <button
                  type="submit"
                  disabled={!inputMessage.trim() || loading}
                  className="p-2.5 rounded-xl bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-200 text-white disabled:text-slate-400 transition-colors shadow-sm disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </form>
              <div className="max-w-3xl mx-auto mt-1.5 flex items-center justify-between text-[11px] text-slate-400 px-1">
                <span>
                  {isEn
                    ? '🔒 Strict security active. AI uses member-permission backend tools only.'
                    : '🔒 কঠোর নিরাপত্তা নিশ্চিত। এআই শুধুমাত্র অনুমোদিত ব্যাকএন্ড টুল ব্যবহার করে।'}
                </span>
                <button
                  type="button"
                  onClick={() => handleOpenEscalation()}
                  className="text-emerald-700 hover:underline flex items-center gap-1 font-medium"
                >
                  <LifeBuoy className="w-3 h-3" />
                  <span>{isEn ? 'Need Secretariat Help?' : 'সচিবালয়ের সহায়তা প্রয়োজন?'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Chat History Drawer / Sidebar */}
          {showHistoryDrawer && (
            <div className="absolute inset-y-0 right-0 w-80 bg-white border-l border-slate-200 shadow-xl z-20 flex flex-col transition-all">
              <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center gap-2">
                  <History className="w-4 h-4 text-emerald-700" />
                  <h3 className="text-sm font-bold text-slate-800">
                    {isEn ? 'Past Conversations' : 'পূর্ববর্তী কথোপকথন'}
                  </h3>
                </div>
                <button
                  onClick={() => setShowHistoryDrawer(false)}
                  className="p-1 rounded-lg hover:bg-slate-200 text-slate-500"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {conversations.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-400">
                    {isEn ? 'No previous conversations found.' : 'কোনো কথোপকথন পাওয়া যায়নি।'}
                  </div>
                ) : (
                  conversations.map((c) => {
                    const isActive = c.id === activeConversationId;
                    return (
                      <div
                        key={c.id}
                        onClick={() => handleSelectConversation(c.id)}
                        className={`group p-3 rounded-xl border text-left cursor-pointer transition-all flex items-start justify-between ${
                          isActive
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-950 font-medium'
                            : 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700'
                        }`}
                      >
                        <div className="flex-1 min-w-0 pr-2">
                          <p className="text-xs truncate font-medium">{c.title || 'Conversation'}</p>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-1">
                            <span>{c.message_count} messages</span>
                            <span>•</span>
                            <span>
                              {c.updated_at
                                ? new Date(c.updated_at).toLocaleDateString([], {
                                    month: 'short',
                                    day: 'numeric',
                                  })
                                : ''}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e) => handleDeleteConversation(e, c.id)}
                          className="p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-rose-100 hover:text-rose-600 text-slate-400 transition-opacity"
                          title={isEn ? 'Delete' : 'মুছে ফেলুন'}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Human Escalation Modal */}
      {showEscalateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 bg-emerald-800 text-white flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <LifeBuoy className="w-5 h-5 text-emerald-200" />
                <h3 className="font-bold text-base">
                  {isEn ? 'Open Human Support Ticket' : 'সাপোর্ট টিকিট খুলুন'}
                </h3>
              </div>
              <button
                onClick={() => setShowEscalateModal(false)}
                className="p-1 rounded-lg hover:bg-emerald-700 text-emerald-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {escalateSuccess ? (
              <div className="p-6 text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto mb-3">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <p className="text-sm font-medium text-emerald-900 mb-4">{escalateSuccess}</p>
                <Link
                  href="/member/support"
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-sm"
                >
                  <span>{isEn ? 'View My Support Tickets' : 'আমার সাপোর্ট টিকিটসমূহ দেখুন'}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            ) : (
              <form onSubmit={handleSubmitEscalation} className="p-6 space-y-4">
                <p className="text-xs text-slate-500">
                  {isEn
                    ? 'Our AI assistant could not resolve your inquiry, or you require official intervention from the PGCB Secretariat.'
                    : 'আমাদের এআই সহকারী আপনার অনুসন্ধান সমাধান করতে পারেনি, অথবা আপনার সচিবালয়ের প্রাতিষ্ঠানিক সহায়তা প্রয়োজন।'}
                </p>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {isEn ? 'Category' : 'ক্যাটেগরি'}
                  </label>
                  <select
                    value={ticketCategory}
                    onChange={(e) => setTicketCategory(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                  >
                    <option value="MEMBERSHIP">{isEn ? 'Membership & Renewals' : 'সদস্যপদ ও নবায়ন'}</option>
                    <option value="PAYMENT">{isEn ? 'Payments & Receipts' : 'পেমেন্ট ও রসিদ'}</option>
                    <option value="DOCUMENTS">{isEn ? 'Document Verification' : 'কাগজপত্র যাচাই'}</option>
                    <option value="CERTIFICATES">{isEn ? 'Certificates' : 'সনদপত্র'}</option>
                    <option value="EVENTS">{isEn ? 'Events & Registrations' : 'ইভেন্ট ও নিবন্ধন'}</option>
                    <option value="GENERAL">{isEn ? 'General Inquiry' : 'সাধারণ অনুসন্ধান'}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {isEn ? 'Subject' : 'বিষয়'}
                  </label>
                  <input
                    type="text"
                    required
                    value={ticketSubject}
                    onChange={(e) => setTicketSubject(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {isEn ? 'Description of Issue' : 'সমস্যার বিস্তারিত বিবরণ'}
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={ticketDescription}
                    onChange={(e) => setTicketDescription(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {isEn ? 'Priority' : 'অগ্রাধিকার'}
                  </label>
                  <select
                    value={ticketPriority}
                    onChange={(e) => setTicketPriority(e.target.value)}
                    className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                  >
                    <option value="NORMAL">{isEn ? 'Normal' : 'সাধারণ'}</option>
                    <option value="HIGH">{isEn ? 'High' : 'উচ্চ'}</option>
                    <option value="URGENT">{isEn ? 'Urgent' : 'জরুরি'}</option>
                  </select>
                </div>

                <div className="pt-2 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowEscalateModal(false)}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    {isEn ? 'Cancel' : 'বাতিল'}
                  </button>
                  <button
                    type="submit"
                    disabled={escalating}
                    className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-colors shadow-sm flex items-center gap-1.5"
                  >
                    {escalating && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                    <span>{isEn ? 'Submit Ticket' : 'টিকিট জমা দিন'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </MemberLayout>
  );
}
