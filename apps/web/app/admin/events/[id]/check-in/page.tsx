'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  QrCode,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowLeft,
  Users,
  Award,
  Download,
  RefreshCw,
  Search,
  Sparkles,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { AdminHeader } from '@/components/admin/AdminHeader';
import { membersApi } from '@/lib/api/members';
import { AdminEventAttendanceResponse, AdminCheckInResult } from '@/lib/api/types';

export default function AdminEventCheckInPage() {
  const params = useParams();
  const eventId = Number(params?.id);
  const inputRef = useRef<HTMLInputElement>(null);

  const [attendanceData, setAttendanceData] = useState<AdminEventAttendanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingIn, setCheckingIn] = useState(false);
  const [ticketInput, setTicketInput] = useState('');
  const [checkInMethod, setCheckInMethod] = useState<'QR' | 'MANUAL'>('QR');
  const [lastResult, setLastResult] = useState<{
    status: 'SUCCESS' | 'ALREADY_CHECKED_IN' | 'ERROR';
    message: string;
    data?: any;
  } | null>(null);

  const loadAttendance = async () => {
    if (!eventId) return;
    try {
      setLoading(true);
      const res = await membersApi.getAdminEventAttendance(eventId);
      setAttendanceData(res);
    } catch (err: any) {
      console.error('Failed to load attendance:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttendance();
    // Auto-focus input on load
    inputRef.current?.focus();
  }, [eventId]);

  const handleCheckInSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = ticketInput.trim();
    if (!token) return;

    try {
      setCheckingIn(true);
      setLastResult(null);

      const res = await membersApi.adminEventCheckIn(eventId, {
        qr_token: token.includes('.') ? token : undefined,
        ticket_code: !token.includes('.') ? token : undefined,
        method: checkInMethod,
      });

      setLastResult({
        status: 'SUCCESS',
        message: res.message || 'চেক-ইন সফল হয়েছে!',
        data: res,
      });
      setTicketInput('');
      await loadAttendance();
    } catch (err: any) {
      const errMsg = err?.message || 'চেক-ইন ব্যর্থ হয়েছে।';
      if (err?.status === 409 || errMsg.includes('ALREADY CHECKED IN') || errMsg.includes('পূর্বে চেক-ইন')) {
        setLastResult({
          status: 'ALREADY_CHECKED_IN',
          message: errMsg,
        });
      } else {
        setLastResult({
          status: 'ERROR',
          message: errMsg,
        });
      }
    } finally {
      setCheckingIn(false);
      inputRef.current?.focus();
    }
  };

  const totalRegistered = attendanceData?.total_registered || 0;
  const totalCheckedIn = attendanceData?.total_checked_in || 0;
  const checkInRate = attendanceData?.check_in_rate_percent || 0;
  const records = attendanceData?.attendance || [];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <AdminHeader
        title={attendanceData ? `${attendanceData.title_bn} — চেক-ইন ডেক্স` : 'ইভেন্ট উপস্থিতি চেক-ইন'}
        subtitle="ডিজিটাল পাস স্ক্যান ও স্বয়ংক্রিয় সনদপত্র প্রদান গেটওয়ে"
      >
        <Link
          href={`/api/v1/admin/events/${eventId}/registrations?format=csv`}
          download
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
        >
          <Download className="w-3.5 h-3.5" />
          <span>CSV Export</span>
        </Link>
      </AdminHeader>

      <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link
            href="/admin/events"
            className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>ইভেন্ট তালিকায় ফিরুন</span>
          </Link>

          <button
            onClick={loadAttendance}
            disabled={loading}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>লাইভ রিফ্রেশ</span>
          </button>
        </div>

        {/* Live Attendance Stats Header */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-slate-400">মোট নিবন্ধিত</div>
            <div className="text-2xl font-black text-slate-900">{totalRegistered} জন</div>
            <div className="text-[11px] text-slate-500">অনুমোদিত অংশগ্রহণকারী</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-emerald-600">উপস্থিতি নিশ্চিত</div>
            <div className="text-2xl font-black text-emerald-600">{totalCheckedIn} জন</div>
            <div className="text-[11px] text-slate-500">সফলভাবে কিউআর ভেরিফাইড</div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-1">
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-400">
              <span>উপস্থিতির হার</span>
              <span className="text-blue-600 font-black">{checkInRate}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden mt-2">
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${checkInRate}%` }}
              />
            </div>
            <div className="text-[11px] text-slate-500">নিবন্ধিত সদস্যদের মধ্যে</div>
          </div>
        </div>

        {/* SCANNER INPUT CARD & FEEDBACK */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Scanner Input (7 cols) */}
          <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center font-bold">
                  <QrCode className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">দ্রুত কিউআর / টিকিট চেক-ইন</h2>
                  <p className="text-xs text-slate-500">স্ক্যানার দিয়ে কিউআর টোকেন অথবা টিকিট কোড ইনপুট করুন</p>
                </div>
              </div>

              {/* Method Switch */}
              <div className="flex items-center bg-slate-100 p-1 rounded-xl text-xs font-bold">
                <button
                  type="button"
                  onClick={() => setCheckInMethod('QR')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    checkInMethod === 'QR' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  কিউআর স্ক্যান
                </button>
                <button
                  type="button"
                  onClick={() => setCheckInMethod('MANUAL')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    checkInMethod === 'MANUAL' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
                  }`}
                >
                  ম্যানুয়াল কোড
                </button>
              </div>
            </div>

            <form onSubmit={handleCheckInSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-2">
                  {checkInMethod === 'QR' ? 'কিউআর টোকেন বা টিকিট কোড' : 'টিকিট রেফারেন্স কোড'}
                </label>
                <div className="relative">
                  <input
                    ref={inputRef}
                    type="text"
                    value={ticketInput}
                    onChange={(e) => setTicketInput(e.target.value)}
                    placeholder={
                      checkInMethod === 'QR'
                        ? 'কিউআর স্ক্যানার দিয়ে স্ক্যান করুন (বা কোড পেস্ট করুন)...'
                        : 'যেমন: TCK-10B5E05F'
                    }
                    className="w-full px-4 py-3.5 rounded-xl border-2 border-slate-300 focus:border-blue-600 focus:ring-4 focus:ring-blue-100 text-base font-mono font-semibold text-slate-900 outline-none transition-all placeholder:font-sans placeholder:text-sm placeholder:text-slate-400"
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={checkingIn || !ticketInput.trim()}
                    className="absolute right-2 top-2 bottom-2 px-5 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-bold text-xs rounded-lg transition-all flex items-center gap-1.5"
                  >
                    {checkingIn ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    <span>যাচাই ও প্রবেশ</span>
                  </button>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                <span>HMAC-SHA256 ক্রিপ্টোগ্রাফিক সুরক্ষা এবং ডাবল চেক-ইন প্রতিরোধ সক্রিয় রয়েছে।</span>
              </div>
            </form>

            {/* Check-In Result Banner */}
            {lastResult && (
              <div
                className={`p-5 rounded-2xl border transition-all animate-in fade-in zoom-in-95 ${
                  lastResult.status === 'SUCCESS'
                    ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                    : lastResult.status === 'ALREADY_CHECKED_IN'
                    ? 'bg-amber-50 border-amber-300 text-amber-900'
                    : 'bg-rose-50 border-rose-300 text-rose-900'
                }`}
              >
                <div className="flex items-start gap-3">
                  {lastResult.status === 'SUCCESS' && (
                    <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
                  )}
                  {lastResult.status === 'ALREADY_CHECKED_IN' && (
                    <AlertCircle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                  )}
                  {lastResult.status === 'ERROR' && (
                    <XCircle className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
                  )}

                  <div className="space-y-1.5 flex-1">
                    <div className="text-base font-black">
                      {lastResult.status === 'SUCCESS' && '✓ চেক-ইন সফল ও প্রবেশ অনুমোদিত'}
                      {lastResult.status === 'ALREADY_CHECKED_IN' && '⚠ পূর্বে চেক-ইন সম্পন্ন (Already Checked In)'}
                      {lastResult.status === 'ERROR' && '✕ চেক-ইন ব্যর্থ হয়েছে'}
                    </div>

                    <p className="text-xs font-semibold leading-relaxed">{lastResult.message}</p>

                    {lastResult.data?.registration && (
                      <div className="bg-white/80 rounded-xl p-3 border border-emerald-200 mt-2 space-y-1 text-xs">
                        <div className="font-bold text-slate-900 text-sm">
                          {lastResult.data.registration.attendee_name}
                        </div>
                        {lastResult.data.registration.membership_id && (
                          <div className="text-slate-600 font-mono">
                            সদস্যপদ নং: {lastResult.data.registration.membership_id}
                          </div>
                        )}
                        <div className="text-slate-500 font-mono">
                          টিকিট কোড: {lastResult.data.registration.ticket_code}
                        </div>
                      </div>
                    )}

                    {lastResult.data?.certificate && (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-100 text-emerald-800 text-xs font-bold mt-1">
                        <Award className="w-4 h-4 text-emerald-700" />
                        <span>
                          সনদপত্র ওয়ালেটে ইস্যু সম্পন্ন হয়েছে! ({lastResult.data.certificate.certificate_no})
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Recent Live Attendance Log (5 cols) */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4 flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-slate-500" />
                  <h3 className="text-sm font-bold text-slate-900">সাম্প্রতিক চেক-ইন লগ</h3>
                </div>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                  {records.length} জন
                </span>
              </div>

              {records.length === 0 ? (
                <div className="text-center py-12 text-slate-400 space-y-2">
                  <Clock className="w-8 h-8 mx-auto stroke-1" />
                  <p className="text-xs">এখনো কোনো উপস্থিতি রেকর্ড পাওয়া যায়নি।</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                  {records.slice(0, 15).map((att) => {
                    const timeStr = att.checked_in_at
                      ? new Date(att.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : '';
                    return (
                      <div
                        key={att.id}
                        className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100/80 border border-slate-100 transition-colors flex items-center justify-between gap-3 text-xs"
                      >
                        <div className="space-y-0.5">
                          <div className="font-bold text-slate-900">{att.attendee_name}</div>
                          {att.ticket_code && (
                            <div className="font-mono text-[10px] text-slate-500">{att.ticket_code}</div>
                          )}
                        </div>

                        <div className="text-right space-y-0.5">
                          <div className="font-bold text-slate-800">{timeStr}</div>
                          <div className="text-[10px] font-semibold text-blue-600">{att.method}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400 text-center">
              উপস্থিতি তালিকা স্বয়ংক্রিয়ভাবে সংরক্ষিত হচ্ছে
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
