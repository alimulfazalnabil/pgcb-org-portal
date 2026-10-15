'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Calendar,
  MapPin,
  Users,
  Clock,
  Ticket,
  Search,
  Filter,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ArrowRight,
  ShieldAlert,
  Award,
  Video,
  ChevronRight,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { MemberEventItem, MemberEventsResponse } from '@/lib/api/types';

export default function MemberEventsPage() {
  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'upcoming' | 'registered' | 'past'>('all');
  const [eventsData, setEventsData] = useState<MemberEventsResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [locationQuery, setLocationQuery] = useState('');

  const isEn = lang === 'en';

  const loadEvents = async (tab = activeTab, cat = selectedCategory, search = searchQuery) => {
    try {
      setLoading(true);
      setError(null);
      const params: any = { tab };
      if (cat && cat !== 'ALL') params.category = cat;
      if (search) params.search = search;
      if (locationQuery) params.location = locationQuery;

      const res = await membersApi.getMemberEvents(params);
      setEventsData(res);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Failed to load events. Please verify connection.'
            : 'ইভেন্ট তালিকা লোড করতে সমস্যা হয়েছে। দয়া করে পুনঃচেষ্টা করুন।')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents(activeTab, selectedCategory, searchQuery);
  }, [activeTab, selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadEvents(activeTab, selectedCategory, searchQuery);
  };

  const counts = eventsData?.counts || { all: 0, upcoming: 0, registered: 0, past: 0 };
  const items = eventsData?.items || [];

  const categoryLabels: Record<string, { en: string; bn: string }> = {
    ALL: { en: 'All Categories', bn: 'সকল বিভাগ' },
    AGM: { en: 'Annual General Meeting', bn: 'বার্ষিক সাধারণ সভা (AGM)' },
    SEMINAR: { en: 'Seminar', bn: 'সেমিনার' },
    WORKSHOP: { en: 'Workshop', bn: 'কর্মশালা' },
    TRAINING: { en: 'Training', bn: 'প্রশিক্ষণ' },
    CONFERENCE: { en: 'Conference', bn: 'সম্মেলন' },
    WEBINAR: { en: 'Webinar', bn: 'ওয়েবিনার' },
    MEETING: { en: 'Meeting', bn: 'সভা' },
    SOCIAL: { en: 'Social & Cultural', bn: 'সামাজিক ও সাংস্কৃতিক' },
    PROFESSIONAL_DEVELOPMENT: { en: 'Professional Development', bn: 'পেশাগত উন্নয়ন' },
    OTHER: { en: 'Special Program', bn: 'বিশেষ কার্যক্রম' },
  };

  return (
    <MemberLayout
      title={isEn ? 'Events & Conferences' : 'ইভেন্টস ও সম্মেলন'}
      lang={lang}
      onLangChange={setLang}
      activeTab="events"
    >
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                <Calendar className="w-3.5 h-3.5" />
                <span>{isEn ? 'Institutional Events & Training' : 'প্রাতিষ্ঠানিক ইভেন্ট ও প্রশিক্ষণ'}</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
                {isEn ? 'PGCB Member Events Center' : 'পিজিসিবি সদস্য ইভেন্ট সেন্টার'}
              </h1>
              <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
                {isEn
                  ? 'Discover official PGCB annual general meetings, technical symposiums, and professional capacity development workshops.'
                  : 'পিজিসিবি প্রকৌশলীদের জন্য বার্ষিক সাধারণ সভা, কারিগরি কর্মশালা ও পেশাগত প্রশিক্ষণ কার্যক্রমে অংশগ্রহণ করুন।'}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => loadEvents(activeTab, selectedCategory, searchQuery)}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-white/10 hover:bg-white/20 text-white backdrop-blur border border-white/10 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>{isEn ? 'Refresh' : 'রিফ্রেশ'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="bg-white border border-slate-200 rounded-2xl p-2 shadow-sm flex flex-wrap gap-2">
          {(
            [
              { key: 'all', label_en: 'All Events', label_bn: 'সকল ইভেন্ট', count: counts.all },
              { key: 'upcoming', label_en: 'Upcoming', label_bn: 'আসন্ন ইভেন্ট', count: counts.upcoming },
              { key: 'registered', label_en: 'My Registered', label_bn: 'আমার নিবন্ধিত', count: counts.registered },
              { key: 'past', label_en: 'Past Events', label_bn: 'পূর্ববর্তী ইভেন্ট', count: counts.past },
            ] as const
          ).map((tab) => {
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 min-w-[140px] flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-md'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <span>{isEn ? tab.label_en : tab.label_bn}</span>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search & Category Filter Bar */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 md:grid-cols-12 gap-3">
            <div className="md:col-span-5 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={isEn ? 'Search events by title or venue...' : 'শিরোনাম বা স্থান দিয়ে ইভেন্ট খুঁজুন...'}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent text-slate-800"
              />
            </div>

            <div className="md:col-span-4 relative">
              <Filter className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent text-slate-800 bg-white"
              >
                {Object.entries(categoryLabels).map(([code, lbl]) => (
                  <option key={code} value={code}>
                    {isEn ? lbl.en : lbl.bn}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-3 flex gap-2">
              <button
                type="submit"
                className="flex-1 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold transition-colors"
              >
                {isEn ? 'Apply Filter' : 'অনুসন্ধান'}
              </button>
              {(searchQuery || selectedCategory !== 'ALL') && (
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedCategory('ALL');
                    loadEvents(activeTab, 'ALL', '');
                  }}
                  className="px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-sm font-medium transition-colors"
                >
                  {isEn ? 'Reset' : 'রিসেট'}
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Error State */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => loadEvents()}
              className="text-xs font-bold underline hover:text-rose-950"
            >
              {isEn ? 'Retry' : 'পুনরায় চেষ্টা করুন'}
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 animate-pulse space-y-4">
                <div className="h-5 bg-slate-200 rounded w-1/3" />
                <div className="h-7 bg-slate-200 rounded w-3/4" />
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-12 bg-slate-100 rounded-xl" />
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!loading && items.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <Calendar className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">
                {isEn ? 'No events found' : 'কোনো ইভেন্ট পাওয়া যায়নি'}
              </h3>
              <p className="text-slate-500 text-sm max-w-md mx-auto">
                {isEn
                  ? 'There are currently no events matching your selected filter or criteria. Check back soon for announcements.'
                  : 'আপনার নির্বাচিত ফিল্টারে কোনো ইভেন্ট পাওয়া যায়নি। নতুন ইভেন্টের বিজ্ঞপ্তির জন্য চোখ রাখুন।'}
              </p>
            </div>
          </div>
        )}

        {/* Events Grid */}
        {!loading && items.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {items.map((event) => {
              const reg = event.my_registration;
              const isRegistered = Boolean(reg);
              const isWaitlisted = reg?.registration_status === 'WAITLISTED';
              const isConfirmed = reg?.registration_status === 'CONFIRMED' || reg?.registration_status === 'ATTENDED';
              const confirmedCount = event.confirmed_count || 0;
              const capacity = event.capacity || 0;
              const capacityPercent = capacity > 0 ? Math.min(100, Math.round((confirmedCount / capacity) * 100)) : 0;
              const isFull = capacity > 0 && confirmedCount >= capacity;

              const eventDateStr = event.event_date || event.start_date;
              const formattedDate = eventDateStr
                ? new Date(eventDateStr).toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })
                : (isEn ? 'Date TBA' : 'তারিখ নির্ধারিত হয়নি');

              return (
                <div
                  key={event.id}
                  className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-5"
                >
                  <div className="space-y-4">
                    {/* Top Row: Category & Badges */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                        {categoryLabels[event.category]?.[isEn ? 'en' : 'bn'] || event.category}
                      </span>

                      <div className="flex items-center gap-2">
                        {event.certificate_eligible && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <Award className="w-3.5 h-3.5" />
                            <span>{isEn ? 'Certificate' : 'সনদপত্র'}</span>
                          </span>
                        )}

                        {isConfirmed && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-500 text-white shadow-sm">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{isEn ? 'Confirmed' : 'নিবন্ধিত'}</span>
                          </span>
                        )}

                        {isWaitlisted && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-500 text-white shadow-sm">
                            <Clock className="w-3.5 h-3.5" />
                            <span>
                              {isEn
                                ? `Waitlist #${reg.waitlist_position || 1}`
                                : `ওয়েটিং লিস্ট #${reg.waitlist_position || 1}`}
                            </span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Title & Description */}
                    <div>
                      <h2 className="text-xl font-bold text-slate-900 leading-snug hover:text-blue-900 transition-colors">
                        <Link href={`/member/events/${event.id}`}>
                          {isEn && event.title_en ? event.title_en : event.title_bn}
                        </Link>
                      </h2>
                      <p className="text-slate-600 text-sm mt-2 line-clamp-2 leading-relaxed">
                        {isEn && event.description_en ? event.description_en : event.description_bn}
                      </p>
                    </div>

                    {/* Schedule & Venue Meta */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-600 pt-2 border-t border-slate-100">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                        <span className="font-medium text-slate-800">{formattedDate}</span>
                        {event.start_time && (
                          <span className="text-slate-500">({event.start_time})</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {event.is_online ? (
                          <>
                            <Video className="w-4 h-4 text-blue-500 shrink-0" />
                            <span className="text-blue-700 font-medium">{isEn ? 'Online Webinar' : 'অনলাইন সেশন'}</span>
                          </>
                        ) : (
                          <>
                            <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                            <span className="truncate">{event.venue}</span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Capacity Indicator */}
                    {capacity > 0 && (
                      <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 space-y-1.5">
                        <div className="flex items-center justify-between text-xs font-semibold">
                          <span className="text-slate-600 flex items-center gap-1.5">
                            <Users className="w-3.5 h-3.5 text-slate-400" />
                            {isEn ? 'Capacity & Seats' : 'আসন সংখ্যা'}
                          </span>
                          <span className={isFull ? 'text-amber-600 font-bold' : 'text-slate-900 font-bold'}>
                            {confirmedCount} / {capacity} {isEn ? 'seats' : 'আসন'}
                            {isFull && ` (${isEn ? 'Full' : 'পূর্ণ'})`}
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full transition-all duration-500 ${
                              isFull ? 'bg-amber-500' : capacityPercent > 80 ? 'bg-indigo-600' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${capacityPercent}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer & Action Buttons */}
                  <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-3">
                    <div className="text-xs">
                      <div className="text-slate-400 font-medium">{isEn ? 'Registration Fee' : 'নিবন্ধন ফি'}</div>
                      <div className="font-bold text-slate-900 text-sm">
                        {event.is_free
                          ? isEn
                            ? 'Free of Charge'
                            : 'বিনামূল্যে'
                          : `৳ ${event.fee_amount.toLocaleString()} ${event.fee_currency}`}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {isConfirmed ? (
                        <Link
                          href={`/member/events/${event.id}/pass`}
                          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
                        >
                          <Ticket className="w-3.5 h-3.5" />
                          <span>{isEn ? 'Event Pass' : 'ইভেন্ট পাস'}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      ) : (
                        <Link
                          href={`/member/events/${event.id}`}
                          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition-all"
                        >
                          <span>
                            {isRegistered
                              ? isEn
                                ? 'View Registration'
                                : 'নিবন্ধন দেখুন'
                              : isFull
                              ? isEn
                                ? 'Join Waitlist'
                                : 'ওয়েটিং লিস্ট'
                              : isEn
                              ? 'View & Register'
                              : 'বিস্তারিত ও নিবন্ধন'}
                          </span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
