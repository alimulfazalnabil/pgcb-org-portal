'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  LifeBuoy,
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Filter,
  Sparkles,
  RefreshCw,
  Search,
  MessageSquare,
  X,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { SupportTicketItem } from '@/lib/api/types';

export default function MemberSupportTicketsPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [tickets, setTickets] = useState<SupportTicketItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Create Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('MEMBERSHIP');
  const [priority, setPriority] = useState('NORMAL');
  const [submitting, setSubmitting] = useState(false);

  const isEn = lang === 'en';

  const loadTickets = async () => {
    try {
      setLoading(true);
      const res = await membersApi.getMemberSupportTickets();
      setTickets(res || []);
    } catch {
      // Non-blocking
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim() || submitting) return;

    try {
      setSubmitting(true);
      await membersApi.createMemberAISupportTicket({
        subject: subject.trim(),
        description: description.trim(),
        category,
        priority,
      });
      setShowCreateModal(false);
      setSubject('');
      setDescription('');
      loadTickets();
    } catch (err: any) {
      alert(err?.message || (isEn ? 'Failed to create ticket' : 'টিকিট তৈরিতে ব্যর্থ হয়েছে'));
    } finally {
      setSubmitting(false);
    }
  };

  const filteredTickets = tickets.filter((t) => {
    const matchesStatus =
      statusFilter === 'ALL'
        ? true
        : statusFilter === 'OPEN_GROUP'
        ? ['OPEN', 'IN_PROGRESS', 'WAITING_FOR_MEMBER'].includes(t.status)
        : t.status === statusFilter;

    const matchesSearch =
      !searchQuery.trim() ||
      t.ticket_no.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.description.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-blue-50 text-blue-700 border border-blue-200">
            {isEn ? 'Open' : 'খোলা'}
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-700 border border-amber-200">
            {isEn ? 'In Progress' : 'প্রক্রিয়াধীন'}
          </span>
        );
      case 'WAITING_FOR_MEMBER':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-50 text-purple-700 border border-purple-200">
            {isEn ? 'Action Required' : 'সদস্যের তথ্য প্রয়োজন'}
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            {isEn ? 'Resolved' : 'সমাধানকৃত'}
          </span>
        );
      case 'CLOSED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {isEn ? 'Closed' : 'বন্ধ'}
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-100 text-slate-700 border border-slate-200">
            {status}
          </span>
        );
    }
  };

  const getPriorityBadge = (priorityVal: string) => {
    switch (priorityVal) {
      case 'URGENT':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded uppercase bg-rose-50 text-rose-700 border border-rose-200">
            {isEn ? 'Urgent' : 'জরুরি'}
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded uppercase bg-orange-50 text-orange-700 border border-orange-200">
            {isEn ? 'High' : 'উচ্চ'}
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-medium rounded uppercase bg-slate-50 text-slate-600 border border-slate-200">
            {isEn ? 'Normal' : 'সাধারণ'}
          </span>
        );
    }
  };

  return (
    <MemberLayout title={isEn ? 'Support Center' : 'সাপোর্ট সেন্টার'}>
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="p-6 bg-gradient-to-r from-emerald-800 to-teal-900 rounded-2xl text-white shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <LifeBuoy className="w-6 h-6 text-emerald-300" />
              <h1 className="text-xl font-bold tracking-tight">
                {isEn ? 'Member Support Center' : 'মেম্বার সাপোর্ট সেন্টার'}
              </h1>
            </div>
            <p className="text-xs text-emerald-100 max-w-xl">
              {isEn
                ? 'Track your inquiries, request official assistance from the Secretariat, or escalate complex matters.'
                : 'আপনার সাপোর্ট টিকিট ট্র্যাক করুন এবং সচিবালয় থেকে প্রাতিষ্ঠানিক সহায়তা গ্রহণ করুন।'}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/member/ai-assistant"
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-emerald-700/60 hover:bg-emerald-700 text-emerald-100 border border-emerald-500/30 flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-emerald-300" />
              <span>{isEn ? 'Ask AI Assistant' : 'এআই সহকারী'}</span>
            </Link>

            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 text-xs font-bold rounded-xl bg-emerald-500 hover:bg-emerald-400 text-emerald-950 flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>{isEn ? 'New Support Ticket' : 'নতুন সাপোর্ট টিকিট'}</span>
            </button>
          </div>
        </div>

        {/* Filters and Search Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
            {[
              { id: 'ALL', en: 'All Tickets', bn: 'সকল টিকিট' },
              { id: 'OPEN_GROUP', en: 'Active', bn: 'চলমান' },
              { id: 'RESOLVED', en: 'Resolved', bn: 'সমাধানকৃত' },
              { id: 'CLOSED', en: 'Closed', bn: 'বন্ধ' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                  statusFilter === tab.id
                    ? 'bg-emerald-700 text-white shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {isEn ? tab.en : tab.bn}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={isEn ? 'Search ticket # or subject...' : 'টিকিট নম্বর বা বিষয় খুঁজুন...'}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
            />
          </div>
        </div>

        {/* Tickets List */}
        {loading ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto mb-2" />
            <p className="text-xs text-slate-500">
              {isEn ? 'Loading support tickets...' : 'সাপোর্ট টিকিট লোড হচ্ছে...'}
            </p>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <LifeBuoy className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800 mb-1">
              {isEn ? 'No Support Tickets Found' : 'কোনো সাপোর্ট টিকিট পাওয়া যায়নি'}
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
              {isEn
                ? 'You do not have any open or previous inquiries matching the current criteria.'
                : 'বর্তমান ফিল্টারের সাথে মিলে এমন কোনো সাপোর্ট টিকিট নেই।'}
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm"
            >
              <Plus className="w-4 h-4" />
              <span>{isEn ? 'Create Ticket' : 'টিকিট তৈরি করুন'}</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTickets.map((t) => (
              <div
                key={t.id}
                className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-emerald-300 hover:shadow-md transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      {t.ticket_no}
                    </span>
                    {getStatusBadge(t.status)}
                    {getPriorityBadge(t.priority)}
                    <span className="text-[11px] text-slate-400">
                      {t.created_at
                        ? new Date(t.created_at).toLocaleDateString([], {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                          })
                        : ''}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 mb-1 leading-snug">
                    {t.subject}
                  </h3>
                  <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                    {t.description}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-center">
                  <Link
                    href={`/member/support/${t.id}`}
                    className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-100 hover:bg-emerald-700 hover:text-white text-slate-700 flex items-center gap-1.5 transition-colors"
                  >
                    <span>{isEn ? 'View Ticket' : 'বিস্তারিত দেখুন'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Support Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 bg-emerald-800 text-white flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <LifeBuoy className="w-5 h-5 text-emerald-200" />
                <h3 className="font-bold text-base">
                  {isEn ? 'Create Support Ticket' : 'নতুন সাপোর্ট টিকিট তৈরি করুন'}
                </h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-1 rounded-lg hover:bg-emerald-700 text-emerald-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {isEn ? 'Category' : 'ক্যাটেগরি'}
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
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
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder={isEn ? 'e.g. Inconsistency in certificate issuance date' : 'যেমন: সনদের তারিখ সংক্রান্ত তথ্য'}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {isEn ? 'Detailed Description' : 'বিস্তারিত বিবরণ'}
                </label>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={isEn ? 'Please describe your request in detail...' : 'দয়া করে আপনার সমস্যার বিস্তারিত বিবরণ লিখুন...'}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-800"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {isEn ? 'Priority' : 'অগ্রাধিকার'}
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
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
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                >
                  {isEn ? 'Cancel' : 'বাতিল'}
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white transition-colors shadow-sm flex items-center gap-1.5"
                >
                  {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>{isEn ? 'Submit Ticket' : 'টিকিট জমা দিন'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </MemberLayout>
  );
}
