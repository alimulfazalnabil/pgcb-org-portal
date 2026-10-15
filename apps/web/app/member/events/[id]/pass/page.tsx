'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Ticket,
  Printer,
  Download,
  ArrowLeft,
  CheckCircle2,
  Calendar,
  MapPin,
  Clock,
  User,
  ShieldCheck,
  Award,
  AlertCircle,
  Copy,
  Check,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberEventPass } from '@/lib/api/types';

export default function MemberEventPassPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [passData, setPassData] = useState<MemberEventPass | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  const isEn = lang === 'en';

  useEffect(() => {
    async function loadPass() {
      if (!eventId) return;
      try {
        setLoading(true);
        setError(null);
        const res = await membersApi.getMemberEventPass(eventId);
        setPassData(res.pass);
      } catch (err: any) {
        setError(
          err?.message ||
            (isEn
              ? 'Failed to generate event pass. Please verify your registration status.'
              : 'ইভেন্ট পাস লোড করা সম্ভব হয়নি। আপনার নিবন্ধন স্ট্যাটাস যাচাই করুন।')
        );
      } finally {
        setLoading(false);
      }
    }
    loadPass();
  }, [eventId]);

  const handlePrint = () => {
    if (typeof window !== 'undefined') {
      window.print();
    }
  };

  const handleCopyCode = () => {
    if (passData?.ticket_code && typeof window !== 'undefined') {
      navigator.clipboard.writeText(passData.ticket_code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  if (loading) {
    return (
      <MemberLayout title={isEn ? 'Digital Event Pass' : 'ডিজিটাল ইভেন্ট পাস'} lang={lang} onLangChange={setLang} activeTab="events">
        <div className="max-w-md mx-auto py-16 text-center space-y-4">
          <div className="w-12 h-12 border-4 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-medium text-slate-500">
            {isEn ? 'Generating tamper-proof signed pass...' : 'ডিজিটাল ইভেন্ট পাস প্রস্তুত হচ্ছে...'}
          </p>
        </div>
      </MemberLayout>
    );
  }

  if (error || !passData) {
    return (
      <MemberLayout title={isEn ? 'Digital Event Pass' : 'ডিজিটাল ইভেন্ট পাস'} lang={lang} onLangChange={setLang} activeTab="events">
        <div className="max-w-lg mx-auto py-12 text-center space-y-4 bg-white p-8 rounded-2xl border border-slate-200">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900">{isEn ? 'Pass Not Available' : 'পাস উপলব্ধ নয়'}</h2>
          <p className="text-slate-600 text-sm">{error || (isEn ? 'No confirmed registration found.' : 'কোনো নিশ্চিত নিবন্ধন পাওয়া যায়নি।')}</p>
          <div className="flex justify-center gap-3 pt-2">
            <Link
              href={`/member/events/${eventId}`}
              className="px-5 py-2.5 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800 transition-colors"
            >
              {isEn ? 'View Event Details' : 'ইভেন্ট বিবরণী দেখুন'}
            </Link>
          </div>
        </div>
      </MemberLayout>
    );
  }

  const { event, attendee } = passData;
  const isCheckedIn = Boolean(passData.checked_in_at);

  const formattedDate = event.event_date || event.start_date
    ? new Date(event.event_date || event.start_date || '').toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : (isEn ? 'Date TBA' : 'তারিখ নির্ধারিত হয়নি');

  return (
    <MemberLayout title={isEn ? 'Digital Event Pass' : 'ডিজিটাল ইভেন্ট পাস'} lang={lang} onLangChange={setLang} activeTab="events">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Top Control Bar (Hidden on print) */}
        <div className="flex items-center justify-between gap-4 print:hidden">
          <Link
            href={`/member/events/${eventId}`}
            className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Event' : 'ইভেন্টে ফিরুন'}</span>
          </Link>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handlePrint}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold shadow-sm transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>{isEn ? 'Print Pass' : 'প্রিন্ট করুন'}</span>
            </button>
            <a
              href={membersApi.getMemberEventQrUrl(eventId)}
              download={`pgcb_event_${eventId}_qr.png`}
              className="inline-flex items-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{isEn ? 'Download QR' : 'কিউআর ডাউনলোড'}</span>
            </a>
          </div>
        </div>

        {/* PRINTABLE PASS CARD */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden print:border-none print:shadow-none">
          {/* Header Strip */}
          <div className="bg-slate-900 text-white p-6 sm:p-8 relative overflow-hidden">
            <div className="relative z-10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-[10px] sm:text-xs font-bold tracking-widest uppercase text-blue-400">
                  POWER GRID COMPANY OF BANGLADESH LTD.
                </div>
                <h1 className="text-xl sm:text-2xl font-black tracking-tight">
                  {isEn ? 'OFFICIAL DIGITAL EVENT PASS' : 'অফিশিয়াল ডিজিটাল ইভেন্ট পাস'}
                </h1>
                <p className="text-slate-400 text-xs">
                  {isEn ? 'Institutional Entry & Check-In Credential' : 'প্রাতিষ্ঠানিক প্রবেশ ও হাজিরা যাচাইকরণ পাস'}
                </p>
              </div>

              <div className="flex sm:flex-col items-end justify-between sm:justify-center">
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  {event.category}
                </span>
                <div className="text-[11px] text-slate-400 mt-1 font-mono">
                  {passData.ticket_code}
                </div>
              </div>
            </div>
          </div>

          {/* Pass Body with Ticket Notch Effect */}
          <div className="p-6 sm:p-8 space-y-8">
            {/* Event Header Info */}
            <div className="border-b border-slate-100 pb-6 space-y-2">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-tight">
                {isEn && event.title_en ? event.title_en : event.title_bn}
              </h2>
              {event.certificate_eligible && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  <Award className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{isEn ? 'Certificate of Participation Included' : 'অংশগ্রহণ সনদপত্র অন্তর্ভুক্ত'}</span>
                </div>
              )}
            </div>

            {/* Split Grid: Details Left, QR Right */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
              {/* Left Details (8 cols) */}
              <div className="md:col-span-7 space-y-6">
                {/* Attendee Details */}
                <div className="bg-slate-50 rounded-2xl p-4 sm:p-5 border border-slate-100 space-y-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    <span>{isEn ? 'Attendee Details' : 'অংশগ্রহণকারীর তথ্য'}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="text-lg font-bold text-slate-900">{attendee.name}</div>
                    {attendee.designation && (
                      <div className="text-xs text-slate-600 font-medium">{attendee.designation}</div>
                    )}
                    {attendee.membership_id && (
                      <div className="text-xs font-mono font-bold text-blue-900">
                        {isEn ? 'Membership ID' : 'সদস্যপদ নং'}: {attendee.membership_id}
                      </div>
                    )}
                    {attendee.circle_name && (
                      <div className="text-xs text-slate-500">{attendee.circle_name}</div>
                    )}
                  </div>
                </div>

                {/* Logistics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1">
                    <div className="text-slate-400 font-medium flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{isEn ? 'Date & Time' : 'তারিখ ও সময়'}</span>
                    </div>
                    <div className="font-bold text-slate-900 text-sm">{formattedDate}</div>
                    {event.start_time && (
                      <div className="text-slate-600 font-medium">
                        {event.start_time} {event.end_time ? `- ${event.end_time}` : ''}
                      </div>
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="text-slate-400 font-medium flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>{isEn ? 'Venue' : 'স্থান'}</span>
                    </div>
                    <div className="font-bold text-slate-900 text-sm">{event.venue}</div>
                  </div>
                </div>

                {/* Status Indicator */}
                <div className="pt-2">
                  {isCheckedIn ? (
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-xs font-bold">
                      <CheckCircle2 className="w-4 h-4 text-blue-600" />
                      <span>
                        {isEn
                          ? `Checked-in at ${new Date(passData.checked_in_at || '').toLocaleTimeString()}`
                          : `উপস্থিতি যাচাইকৃত (${new Date(passData.checked_in_at || '').toLocaleTimeString()})`}
                      </span>
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>{isEn ? 'Authorized & Confirmed' : 'অনুমোদিত ও নিবন্ধিত'}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Right QR Section (5 cols) */}
              <div className="md:col-span-5 flex flex-col items-center justify-center p-6 bg-slate-50/70 border border-slate-100 rounded-2xl text-center space-y-4">
                <div className="p-3 bg-white rounded-2xl shadow-sm border border-slate-200">
                  {passData.qr_image_data_url ? (
                    <img
                      src={passData.qr_image_data_url}
                      alt="Event Pass QR Code"
                      className="w-44 h-44 object-contain"
                    />
                  ) : (
                    <div className="w-44 h-44 flex items-center justify-center bg-slate-100 text-slate-400 text-xs">
                      QR Unavailable
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-slate-900 font-mono">
                    <span>{passData.ticket_code}</span>
                    <button
                      onClick={handleCopyCode}
                      className="text-slate-400 hover:text-slate-600 p-1"
                      title="Copy ticket code"
                    >
                      {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  <div className="inline-flex items-center gap-1 text-[10px] font-semibold text-slate-500">
                    <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                    <span>{isEn ? 'HMAC-SHA256 Signed' : 'ডিজিটাল সিলমোহরযুক্ত'}</span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-500 max-w-[200px] leading-tight">
                  {isEn
                    ? 'Scan this QR code at the registration reception for instant venue access.'
                    : 'প্রবেশদ্বারে রেজিস্ট্রেশন ডেস্কে এই কিউআর কোডটি প্রদর্শন করুন।'}
                </div>
              </div>
            </div>
          </div>

          {/* Institutional Security Footer */}
          <div className="bg-slate-100 border-t border-slate-200 px-6 py-4 flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-500 gap-2">
            <div>
              {isEn ? 'Issued by PGCB Central Secretariat' : 'পিজিসিবি কেন্দ্রীয় সচিবালয় কর্তৃক ইস্যুকৃত'}
            </div>
            <div className="font-mono text-slate-400">
              Pass ID: {passData.registration_id} | Ref: {passData.ticket_code}
            </div>
          </div>
        </div>
      </div>
    </MemberLayout>
  );
}
