'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Calendar,
  MapPin,
  Users,
  Clock,
  Ticket,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  Award,
  Video,
  XCircle,
  HelpCircle,
  Share2,
  Check,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberEventItem } from '@/lib/api/types';

export default function MemberEventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [event, setEvent] = useState<MemberEventItem | null>(null);
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [copiedLink, setCopiedLink] = useState(false);

  const isEn = lang === 'en';

  const loadEventDetail = async () => {
    if (!eventId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getMemberEventDetail(eventId);
      setEvent(data);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load event details.'
            : 'ইভেন্টের বিস্তারিত তথ্য লোড করতে সমস্যা হয়েছে।')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEventDetail();
  }, [eventId]);

  const handleRegister = async () => {
    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);
      const res = await membersApi.registerMemberEvent(eventId, {});
      setSuccessMsg(res?.message || (isEn ? 'Successfully registered!' : 'সফলভাবে নিবন্ধিত হয়েছে!'));
      await loadEventDetail();
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Registration failed. Please check capacity or eligibility.'
            : 'নিবন্ধন সম্পন্ন করা সম্ভব হয়নি। দয়া করে পুনঃচেষ্টা করুন।')
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCancelling(true);
      setError(null);
      await membersApi.cancelMemberEvent(eventId, cancelReason);
      setCancelModalOpen(false);
      setSuccessMsg(
        isEn
          ? 'Registration cancelled. Your seat has been offered to the next waitlisted member.'
          : 'নিবন্ধন বাতিল করা হয়েছে। আসনটি ওয়েটিং লিস্টের পরবর্তী সদস্যকে বরাদ্দ দেওয়া হয়েছে।'
      );
      await loadEventDetail();
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn ? 'Cancellation failed. Please try again.' : 'বাতিলকরণ সম্পন্ন করা সম্ভব হয়নি।')
      );
    } finally {
      setCancelling(false);
    }
  };

  const handleCopyLink = () => {
    if (typeof window !== 'undefined') {
      navigator.clipboard.writeText(window.location.href);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    }
  };

  if (loading) {
    return (
      <MemberLayout title={isEn ? 'Event Details' : 'ইভেন্টের বিস্তারিত'} lang={lang} onLangChange={setLang} activeTab="events">
        <div className="max-w-4xl mx-auto py-12 text-center space-y-4">
          <div className="w-12 h-12 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium text-slate-500">
            {isEn ? 'Loading event information...' : 'ইভেন্টের তথ্য লোড হচ্ছে...'}
          </p>
        </div>
      </MemberLayout>
    );
  }

  if (error && !event) {
    return (
      <MemberLayout title={isEn ? 'Event Details' : 'ইভেন্টের বিস্তারিত'} lang={lang} onLangChange={setLang} activeTab="events">
        <div className="max-w-xl mx-auto py-12 text-center space-y-4 bg-white p-8 rounded-2xl border border-slate-200">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900">{isEn ? 'Event Not Found' : 'ইভেন্ট পাওয়া যায়নি'}</h2>
          <p className="text-slate-600 text-sm">{error}</p>
          <Link
            href="/member/events"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-xl text-sm font-semibold hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Events' : 'ইভেন্ট তালিকায় ফিরুন'}</span>
          </Link>
        </div>
      </MemberLayout>
    );
  }

  if (!event) return null;

  const reg = event.my_registration;
  const isRegistered = Boolean(reg);
  const isWaitlisted = reg?.registration_status === 'WAITLISTED';
  const isConfirmed = reg?.registration_status === 'CONFIRMED' || reg?.registration_status === 'ATTENDED';

  const confirmedCount = event.confirmed_count || 0;
  const capacity = event.capacity || 0;
  const capacityPercent = capacity > 0 ? Math.min(100, Math.round((confirmedCount / capacity) * 100)) : 0;
  const isFull = Boolean(event.is_full || (capacity > 0 && confirmedCount >= capacity));

  const eventDateStr = event.event_date || event.start_date;
  const formattedDate = eventDateStr
    ? new Date(eventDateStr).toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      })
    : (isEn ? 'Date TBA' : 'তারিখ নির্ধারিত হয়নি');

  return (
    <MemberLayout
      title={isEn ? (event.title_en || event.title_bn) : event.title_bn}
      lang={lang}
      onLangChange={setLang}
      activeTab="events"
    >
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
          <Link
            href="/member/events"
            className="inline-flex items-center gap-1.5 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to All Events' : 'সকল ইভেন্টে ফিরুন'}</span>
          </Link>

          <button
            onClick={handleCopyLink}
            className="inline-flex items-center gap-1.5 text-slate-600 hover:text-slate-900 transition-colors"
          >
            {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Share2 className="w-3.5 h-3.5" />}
            <span>{copiedLink ? (isEn ? 'Copied!' : 'কপি হয়েছে!') : (isEn ? 'Share Event' : 'শেয়ার করুন')}</span>
          </button>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center gap-2 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-2 text-sm font-medium">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Member Registration Status Banner */}
        {isConfirmed && (
          <div className="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-7 h-7 text-white" />
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-emerald-100">
                  {isEn ? 'Registration Confirmed' : 'নিবন্ধন নিশ্চিত'}
                </div>
                <div className="text-lg font-bold">
                  {isEn ? `Ticket Code: ${reg?.ticket_code}` : `টিকিট কোড: ${reg?.ticket_code}`}
                </div>
                <div className="text-xs text-emerald-100">
                  {isEn
                    ? 'Your seat has been reserved. Please carry your digital event pass for rapid entry.'
                    : 'আপনার আসন সংরক্ষিত। দ্রুত প্রবেশের জন্য ডিজিটাল ইভেন্ট পাসটি সাথে রাখুন।'}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              <Link
                href={`/member/events/${event.id}/pass`}
                className="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white text-emerald-900 hover:bg-emerald-50 shadow-md transition-all flex items-center gap-2"
              >
                <Ticket className="w-4 h-4" />
                <span>{isEn ? 'View Digital Pass' : 'ডিজিটাল পাস দেখুন'}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <button
                onClick={() => setCancelModalOpen(true)}
                className="px-3 py-2.5 rounded-xl font-semibold text-xs text-emerald-100 hover:text-white hover:bg-white/10 transition-colors"
              >
                {isEn ? 'Cancel' : 'বাতিল'}
              </button>
            </div>
          </div>
        )}

        {isWaitlisted && (
          <div className="bg-gradient-to-r from-amber-600 to-orange-600 rounded-2xl p-6 text-white shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-center sm:text-left">
              <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shrink-0">
                <Clock className="w-7 h-7 text-white" />
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-amber-100">
                  {isEn ? 'Waitlist Status' : 'অপেক্ষমাণ তালিকা'}
                </div>
                <div className="text-lg font-bold">
                  {isEn
                    ? `Queue Position: #${reg?.waitlist_position || 1}`
                    : `তালিকায় অবস্থান: #${reg?.waitlist_position || 1}`}
                </div>
                <div className="text-xs text-amber-100">
                  {isEn
                    ? 'The event reached capacity. When another member cancels, your pass will be confirmed automatically.'
                    : 'ইভেন্টের নির্ধারিত আসন পূর্ণ। কোনো সদস্য নিবন্ধন বাতিল করলে স্বয়ংক্রিয়ভাবে আপনার আসন নিশ্চিত হবে।'}
                </div>
              </div>
            </div>

            <button
              onClick={() => setCancelModalOpen(true)}
              className="px-4 py-2.5 rounded-xl font-semibold text-xs sm:text-sm bg-white/20 hover:bg-white/30 text-white backdrop-blur border border-white/20 transition-colors shrink-0"
            >
              {isEn ? 'Withdraw from Waitlist' : 'ওয়েটিং লিস্ট প্রত্যাহার'}
            </button>
          </div>
        )}

        {/* Main Event Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Information */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
              <div className="space-y-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-3 py-1 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-800">
                    {event.category}
                  </span>
                  {event.certificate_eligible && (
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <Award className="w-4 h-4" />
                      <span>{isEn ? 'Official Certificate' : 'অফিশিয়াল সনদপত্র'}</span>
                    </span>
                  )}
                  <span className="px-3 py-1 rounded-lg text-xs font-bold bg-slate-900 text-white">
                    {event.is_free ? (isEn ? 'Free Entry' : 'বিনামূল্যে') : `৳ ${event.fee_amount} ${event.fee_currency}`}
                  </span>
                </div>

                <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-snug">
                  {isEn && event.title_en ? event.title_en : event.title_bn}
                </h1>
              </div>

              {/* Description Body */}
              <div className="prose prose-slate max-w-none text-slate-700 text-sm sm:text-base leading-relaxed whitespace-pre-line border-t border-slate-100 pt-6">
                {isEn && event.description_en ? event.description_en : event.description_bn}
              </div>

              {/* Eligibility Criteria */}
              {event.eligibility_criteria && (
                <div className="bg-blue-50/70 border border-blue-200 rounded-2xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-blue-900 font-bold text-sm">
                    <ShieldCheck className="w-4 h-4 text-blue-700" />
                    <span>{isEn ? 'Eligibility & Requirements' : 'যোগ্যতা ও শর্তাবলী'}</span>
                  </div>
                  <p className="text-blue-800 text-xs sm:text-sm leading-relaxed">
                    {event.eligibility_criteria}
                  </p>
                </div>
              )}

              {/* Certificate Issuance Notice */}
              {event.certificate_eligible && (
                <div className="bg-emerald-50/70 border border-emerald-200 rounded-2xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                    <Award className="w-4 h-4 text-emerald-700" />
                    <span>{isEn ? 'Certificate of Participation' : 'অংশগ্রহণ সনদপত্র'}</span>
                  </div>
                  <p className="text-emerald-800 text-xs sm:text-sm leading-relaxed">
                    {isEn
                      ? 'Attendance at this event will be verified via QR check-in. Upon check-in, an institutional Certificate of Participation will be instantly issued into your PGCB Certificate Wallet.'
                      : 'এই ইভেন্টে উপস্থিতির কিউআর কোড স্ক্যান সম্পন্ন হলে স্বয়ংক্রিয়ভাবে আপনার ডিজিটাল সনদপত্র ওয়ালেটে অংশগ্রহণের অফিশিয়াল সার্টিফিকেট যুক্ত হবে।'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Event Meta & Registration Card */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6 sticky top-6">
              <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3">
                {isEn ? 'Event Logistics' : 'ইভেন্ট বিবরণী'}
              </h3>

              <div className="space-y-4 text-sm">
                {/* Date & Time */}
                <div className="flex items-start gap-3">
                  <Calendar className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs text-slate-500 font-medium">{isEn ? 'Date' : 'তারিখ'}</div>
                    <div className="font-bold text-slate-900">{formattedDate}</div>
                    {event.start_time && (
                      <div className="text-xs text-slate-600 mt-0.5">
                        {event.start_time} {event.end_time ? `- ${event.end_time}` : ''}
                      </div>
                    )}
                  </div>
                </div>

                {/* Venue */}
                <div className="flex items-start gap-3">
                  {event.is_online ? (
                    <Video className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                  ) : (
                    <MapPin className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <div className="text-xs text-slate-500 font-medium">
                      {event.is_online ? (isEn ? 'Webinar Platform' : 'অনলাইন মাধ্যম') : (isEn ? 'Venue' : 'স্থান')}
                    </div>
                    <div className="font-bold text-slate-900">{event.venue}</div>
                    {event.meeting_link && isConfirmed && (
                      <a
                        href={event.meeting_link}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-600 font-semibold hover:underline mt-1"
                      >
                        <span>{isEn ? 'Join Virtual Session' : 'ভার্চুয়াল সেশনে যুক্ত হন'}</span>
                        <ArrowRight className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Capacity Counter */}
                {capacity > 0 && (
                  <div className="space-y-2 pt-2 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs font-semibold">
                      <span className="text-slate-600 flex items-center gap-1.5">
                        <Users className="w-4 h-4 text-slate-400" />
                        {isEn ? 'Capacity' : 'আসন বিবরণী'}
                      </span>
                      <span className={isFull ? 'text-amber-600 font-bold' : 'text-slate-900 font-bold'}>
                        {confirmedCount} / {capacity}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          isFull ? 'bg-amber-500' : capacityPercent > 80 ? 'bg-indigo-600' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${capacityPercent}%` }}
                      />
                    </div>
                    <div className="text-[11px] text-slate-500 flex justify-between">
                      <span>{isFull ? (isEn ? 'Fully Booked' : 'আসন পূর্ণ') : `${event.seats_available} seats remaining`}</span>
                      <span>{event.waitlist_count > 0 ? `${event.waitlist_count} on waitlist` : ''}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Button Section */}
              <div className="pt-4 border-t border-slate-100 space-y-3">
                {isConfirmed ? (
                  <Link
                    href={`/member/events/${event.id}/pass`}
                    className="w-full py-3 px-4 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-bold transition-all shadow-md flex items-center justify-center gap-2"
                  >
                    <Ticket className="w-4 h-4" />
                    <span>{isEn ? 'View Digital Event Pass' : 'ডিজিটাল ইভেন্ট পাস দেখুন'}</span>
                  </Link>
                ) : isWaitlisted ? (
                  <div className="text-center p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
                    {isEn
                      ? `You are #${reg?.waitlist_position || 1} on the waiting list.`
                      : `আপনি ওয়েটিং লিস্টের #${reg?.waitlist_position || 1} অবস্থানে রয়েছেন।`}
                  </div>
                ) : (
                  <button
                    onClick={handleRegister}
                    disabled={submitting || !event.registration_enabled}
                    className={`w-full py-3 px-4 rounded-xl text-sm font-bold transition-all shadow-md flex items-center justify-center gap-2 ${
                      isFull
                        ? 'bg-amber-600 hover:bg-amber-700 text-white'
                        : 'bg-slate-900 hover:bg-slate-800 text-white'
                    } ${submitting ? 'opacity-70 cursor-not-allowed' : ''}`}
                  >
                    {submitting ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Ticket className="w-4 h-4" />
                    )}
                    <span>
                      {isFull
                        ? isEn
                          ? 'Join Waitlist Queue'
                          : 'ওয়েটিং লিস্টে যুক্ত হন'
                        : isEn
                        ? 'Confirm Free Registration'
                        : 'বিনামূল্যে নিবন্ধন নিশ্চিত করুন'}
                    </span>
                  </button>
                )}

                <div className="text-[11px] text-center text-slate-400">
                  {isEn
                    ? 'Registration is bound to your verified member profile.'
                    : 'নিবন্ধনটি আপনার যাচাইকৃত সদস্য প্রোফাইলের সাথে সংযুক্ত।'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cancellation Modal */}
        {cancelModalOpen && (
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2 text-rose-600 font-bold text-base">
                  <XCircle className="w-5 h-5" />
                  <span>{isEn ? 'Cancel Registration' : 'নিবন্ধন বাতিল'}</span>
                </div>
                <button
                  onClick={() => setCancelModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600 text-sm font-bold"
                >
                  ✕
                </button>
              </div>

              <p className="text-sm text-slate-600 leading-relaxed">
                {isEn
                  ? 'Are you sure you want to cancel your event registration? Your reserved seat will be immediately reassigned to the next member on the waitlist.'
                  : 'আপনি কি নিশ্চিত যে আপনার নিবন্ধন বাতিল করতে চান? আসনটি তাৎক্ষণিকভাবে ওয়েটিং লিস্টে থাকা পরবর্তী সদস্যকে বরাদ্দ দেওয়া হবে।'}
              </p>

              <form onSubmit={handleCancelRegistration} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    {isEn ? 'Reason for Cancellation (Optional)' : 'বাতিলের কারণ (ঐচ্ছিক)'}
                  </label>
                  <textarea
                    value={cancelReason}
                    onChange={(e) => setCancelReason(e.target.value)}
                    rows={3}
                    placeholder={isEn ? 'e.g. Official grid duty or urgent travel...' : 'যেমন: অফিশিয়াল জরুরি দায়িত্ব বা ভ্রমণ...'}
                    className="w-full p-3 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setCancelModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
                  >
                    {isEn ? 'Keep Registration' : 'নিবন্ধন বহাল রাখুন'}
                  </button>
                  <button
                    type="submit"
                    disabled={cancelling}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    {cancelling ? (isEn ? 'Cancelling...' : 'বাতিল হচ্ছে...') : (isEn ? 'Confirm Cancellation' : 'বাতিল নিশ্চিত করুন')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
