'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  LifeBuoy,
  ArrowLeft,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  Calendar,
  Sparkles,
  RefreshCw,
  Building2,
  Mail,
  Phone,
  MessageSquare,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { SupportTicketDetail } from '@/lib/api/types';

export default function MemberSupportTicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [ticket, setTicket] = useState<SupportTicketDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isEn = lang === 'en';

  useEffect(() => {
    if (!ticketId) return;

    const loadTicket = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await membersApi.getMemberSupportTicketDetail(ticketId);
        setTicket(data);
      } catch (err: any) {
        setError(
          err?.message ||
            (isEn ? 'Failed to load support ticket details.' : 'সাপোর্ট টিকিটের তথ্য লোড করা যায়নি।')
        );
      } finally {
        setLoading(false);
      }
    };

    loadTicket();
  }, [ticketId]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            {isEn ? 'Open' : 'খোলা'}
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            {isEn ? 'In Progress' : 'প্রক্রিয়াধীন'}
          </span>
        );
      case 'WAITING_FOR_MEMBER':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            {isEn ? 'Waiting for Member' : 'সদস্যের তথ্য প্রয়োজন'}
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {isEn ? 'Resolved' : 'সমাধানকৃত'}
          </span>
        );
      case 'CLOSED':
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {isEn ? 'Closed' : 'বন্ধ'}
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  return (
    <MemberLayout title={isEn ? 'Support Ticket' : 'সাপোর্ট টিকিট'}>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation & Header */}
        <div className="flex items-center justify-between">
          <Link
            href="/member/support"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-emerald-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Support Tickets' : 'সাপোর্ট টিকিট তালিকায় ফিরে যান'}</span>
          </Link>

          <Link
            href="/member/ai-assistant"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>{isEn ? 'AI Assistant' : 'এআই সহকারী'}</span>
          </Link>
        </div>

        {loading ? (
          <div className="p-16 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto mb-2" />
            <p className="text-xs text-slate-500">
              {isEn ? 'Loading ticket details...' : 'টিকিট তথ্য লোড হচ্ছে...'}
            </p>
          </div>
        ) : error || !ticket ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
            <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-800 mb-2">{error || 'Ticket not found'}</p>
            <Link
              href="/member/support"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 text-white"
            >
              <span>{isEn ? 'Return to Support' : 'সাপোর্ট সেন্টারে ফিরুন'}</span>
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Ticket Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-6 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-sm font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                    {ticket.ticket_no}
                  </span>
                  {getStatusBadge(ticket.status)}
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>
                    {ticket.created_at
                      ? new Date(ticket.created_at).toLocaleDateString([], {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : ''}
                  </span>
                </div>
              </div>

              {/* Title and Meta */}
              <div className="mt-6 mb-6">
                <h1 className="text-xl font-bold text-slate-900 mb-3">{ticket.subject}</h1>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-medium">
                    {isEn ? 'Category:' : 'ক্যাটেগরি:'} {ticket.category}
                  </span>
                  <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-medium">
                    {isEn ? 'Priority:' : 'অগ্রাধিকার:'} {ticket.priority}
                  </span>
                </div>
              </div>

              {/* Description Section */}
              <div className="space-y-2 mb-8">
                <h3 className="text-xs uppercase font-bold tracking-wider text-slate-400">
                  {isEn ? 'Inquiry Details' : 'অনুসন্ধানের বিবরণ'}
                </h3>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                  {ticket.description}
                </div>
              </div>

              {/* Resolution Notes Section */}
              {ticket.resolution_notes ? (
                <div className="p-5 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-950 mb-6">
                  <div className="flex items-center gap-2 font-bold text-sm mb-2 text-emerald-900">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <span>{isEn ? 'Secretariat Official Resolution' : 'সচিবালয়ের অফিসিয়াল সমাধান'}</span>
                  </div>
                  <div className="text-xs text-slate-700 whitespace-pre-wrap leading-relaxed mb-3">
                    {ticket.resolution_notes}
                  </div>
                  {ticket.resolved_at && (
                    <p className="text-[11px] text-emerald-700 font-medium">
                      {isEn ? 'Resolved on:' : 'সমাধানের তারিখ:'}{' '}
                      {new Date(ticket.resolved_at).toLocaleString()}
                    </p>
                  )}
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center gap-3 text-xs mb-6">
                  <Clock className="w-5 h-5 text-amber-600 shrink-0" />
                  <span>
                    {isEn
                      ? 'This ticket is currently queued for institutional review by the PGCB Secretariat. Updates will appear here.'
                      : 'এই টিকিটটি বর্তমানে পিজিসিবি সচিবালয়ের প্রাতিষ্ঠানিক পর্যালোচনায় রয়েছে। হালনাগাদ তথ্য এখানে প্রদর্শিত হবে।'}
                  </span>
                </div>
              )}
            </div>

            {/* Secretariat Contact Box */}
            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-emerald-700" />
                  <span>{isEn ? 'PGCB Central Secretariat' : 'পিজিসিবি কেন্দ্রীয় সচিবালয়'}</span>
                </h3>
                <p className="text-xs text-slate-500">
                  {isEn
                    ? 'For urgent escalations or physical inquiries during office hours (Sun–Thu 9am–5pm).'
                    : 'জরুরি প্রয়োজনে অফিস চলাকালীন সময়ে সরাসরি যোগাযোগ করুন (রবি–বৃহঃ সকাল ৯টা–বিকেল ৫টা)।'}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200">
                  <Phone className="w-3.5 h-3.5 text-emerald-600" />
                  <span>+880-2-9555123</span>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200">
                  <Mail className="w-3.5 h-3.5 text-emerald-600" />
                  <span>support@pgcb.org.bd</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
