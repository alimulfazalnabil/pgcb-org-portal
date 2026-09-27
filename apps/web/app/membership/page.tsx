'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  UserPlus,
  Search,
  Award,
  CheckCircle2,
  Building2,
  FileText,
  ArrowRight,
  Users,
  Sparkles,
  BookOpen,
} from 'lucide-react';

export default function MembershipOverviewPage() {
  const [circlesCount, setCirclesCount] = useState<number>(8);
  const [activeMembers, setActiveMembers] = useState<number | null>(null);

  useEffect(() => {
    fetch('/backend/api/v1/public/stats')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) {
          if (typeof data.circles === 'number' && data.circles > 0) setCirclesCount(data.circles);
          if (typeof data.active_members === 'number') setActiveMembers(data.active_members);
        }
      })
      .catch(() => {});
  }, []);

  const categories = [
    {
      title: 'সাধারণ সদস্য (General Member)',
      badge: 'GENERAL',
      fee: '৳ ৫০০ (ভর্তি ফি) + ৳ ১০০/মাস',
      eligibility: 'পিজিসিবি-তে কর্মরত সকল ডিপ্লোমা প্রকৌশলী (উপ-সহকারী প্রকৌশলী হতে তদূর্ধ্ব পদমর্যাদা)।',
      features: [
        'ডিজিটাল ভেরিফায়েড সদস্য কার্ড ও কিউআর প্রোফাইল',
        'কেন্দ্রীয় ও সার্কেল নির্বাচনে ভোটাধিকার ও প্রার্থিতার সুযোগ',
        'কল্যাণ তহবিল ও পেশাগত সুরক্ষা সহায়তা',
        'বার্ষিক কারিগরি জার্নাল ও সম্মেলনে অংশগ্রহণ',
      ],
    },
    {
      title: 'আজীবন সদস্য (Life Member)',
      badge: 'LIFE',
      fee: '৳ ১০,০০০ (এককালীন)',
      eligibility: 'পিজিসিবি-তে ন্যূনতম ৫ বছর চাকরিকাল পূর্ণকারী নিবন্ধিত ডিপ্লোমা প্রকৌশলী।',
      features: [
        'আজীবন নবায়নমুক্ত সক্রিয় সদস্যপদ ও বিশেষ সম্মাননা সনদ',
        'জাতীয় ও আন্তর্জাতিক কারিগরি সেমিনারে অগ্রাধিকার',
        'কেন্দ্রীয় উপদেষ্টা ও কারিগরি কমিটিতে অন্তর্ভুক্তির সুযোগ',
        'সকল সাধারণ সদস্য সুবিধা আজীবন বলবৎ',
      ],
    },
    {
      title: 'সম্মানিত / অবসরপ্রাপ্ত সদস্য (Associate / Retired)',
      badge: 'ASSOCIATE',
      fee: '৳ ১,০০০ (এককালীন নিবন্ধন)',
      eligibility: 'পিজিসিবি হতে অবসরপ্রাপ্ত ডিপ্লোমা প্রকৌশলী অথবা গ্রিড প্রকৌশলে বিশেষ অবদান রাখা ব্যক্তিত্ব।',
      features: [
        'বার্ষিক পুনর্মিলনী ও কেন্দ্রীয় অনুষ্ঠানে বিশেষ আমন্ত্রণ',
        'গবেষণা ও কারিগরি প্রকাশনায় প্রবন্ধ প্রকাশের সুযোগ',
        'সমিতির ডিজিটাল ডিরেক্টরি ও আর্কাইভ অ্যাক্সেস',
      ],
    },
  ];

  const steps = [
    {
      step: '০১',
      title: 'অনলাইন আবেদন ফরম পূরণ',
      desc: 'আপনার প্রাতিষ্ঠানিক তথ্য, পিজিসিবি এমপ্লয়ি আইডি, ডিপ্লোমা সনদ ও এনআইডি তথ্য দিয়ে আবেদন করুন।',
    },
    {
      step: '০২',
      title: 'ডকুমেন্ট ও সার্কেল যাচাই',
      desc: 'সংশ্লিষ্ট গ্রিড সার্কেল ও কেন্দ্রীয় সদস্যপদ কর্মকর্তা আপনার সনদ ও প্রাতিষ্ঠানিক পদবী যাচাই করবেন।',
    },
    {
      step: '০৩',
      title: 'কেন্দ্রীয় অনুমোদন ও আইডি ইস্যু',
      desc: 'অনুমোদনের পর স্বয়ংক্রিয়ভাবে PGD-YYYY-XXXX ফরম্যাটে সদস্য আইডি ও কিউআর কার্ড জেনারেট হবে।',
    },
  ];

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Hero Header */}
        <div className="bg-gradient-to-br from-primary via-primary/95 to-slate-900 rounded-3xl p-8 sm:p-12 text-white shadow-xl relative overflow-hidden">
          <div className="max-w-3xl space-y-5 relative z-10">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/15 backdrop-blur-sm text-xs font-bold uppercase tracking-wider">
              <ShieldCheck size={16} /> INSTITUTIONAL MEMBERSHIP PORTAL
            </div>
            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
              পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির সদস্যপদ
            </h1>
            <p className="text-sm sm:text-base text-white/85 leading-relaxed">
              জাতীয় পাওয়ার গ্রিড পরিচালনা, রক্ষণাবেক্ষণ ও উন্নয়নে নিয়োজিত ডিপ্লোমা প্রকৌশলীদের ঐক্যবদ্ধ পেশাজীবী প্ল্যাটফর্ম। আপনার পেশাগত অধিকার, কারিগরি উৎকর্ষ এবং প্রাতিষ্ঠানিক কল্যাণ নিশ্চিত করতে আজই যুক্ত হোন।
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <Link
                href="/membership/apply"
                className="px-6 py-3.5 rounded-xl bg-accent text-slate-950 font-extrabold text-sm hover:opacity-95 transition-all inline-flex items-center gap-2 shadow-lg"
              >
                <UserPlus size={18} /> নতুন সদস্যপদের আবেদন করুন
              </Link>
              <Link
                href="/membership/track"
                className="px-5 py-3.5 rounded-xl bg-white/15 hover:bg-white/25 text-white font-bold text-sm transition-all inline-flex items-center gap-2 border border-white/20"
              >
                <Search size={17} /> আবেদনের অবস্থান জানুন
              </Link>
              <Link
                href="/membership/benefits"
                className="px-5 py-3.5 rounded-xl bg-transparent hover:bg-white/10 text-white font-semibold text-sm transition-all inline-flex items-center gap-2 border border-white/25"
              >
                <Sparkles size={17} /> সদস্য সুবিধা দেখুন <ArrowRight size={15} />
              </Link>
            </div>
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-2xl p-6 flex items-center gap-4 shadow-sm">
            <div className="p-3.5 rounded-2xl bg-primary/10 text-primary">
              <Building2 size={26} />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-foreground">{circlesCount}+ গ্রিড সার্কেল</div>
              <div className="text-xs text-secondary">সারাদেশে বিস্তৃত সাংগঠনিক নেটওয়ার্ক</div>
            </div>
          </div>
          <div className="bg-card border border-border rounded-2xl p-6 flex items-center gap-4 shadow-sm">
            <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-600">
              <Users size={26} />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-foreground">
                {activeMembers !== null ? `${activeMembers} জন` : 'যাচাইকৃত ডাটাবেস'}
              </div>
              <div className="text-xs text-secondary">কেন্দ্রীয় ডিজিটাল রোস্টারভুক্ত প্রকৌশলী</div>
            </div>
          </div>
          <div className="bg-card border border-border rounded-2xl p-6 flex items-center gap-4 shadow-sm">
            <div className="p-3.5 rounded-2xl bg-amber-500/10 text-amber-600">
              <Award size={26} />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-foreground">HMAC-SHA256</div>
              <div className="text-xs text-secondary">ক্রিপ্টোগ্রাফিক ডিজিটাল আইডি ও সনদ যাচাই</div>
            </div>
          </div>
        </div>

        {/* Membership Categories */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-primary">MEMBERSHIP TIERS</span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-foreground mt-1">
                সদস্যপদের ধরন ও যোগ্যতা
              </h2>
            </div>
            <Link
              href="/membership/benefits"
              className="text-xs font-bold text-primary hover:underline inline-flex items-center gap-1"
            >
              বিস্তারিত সদস্য সুবিধা ও কল্যাণ তহবিল দেখুন <ArrowRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {categories.map((cat) => (
              <div
                key={cat.badge}
                className="bg-card border border-border rounded-2xl p-6 flex flex-col justify-between space-y-6 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="px-2.5 py-1 rounded-md bg-primary/10 text-primary font-mono text-[11px] font-bold">
                      {cat.badge}
                    </span>
                    <span className="text-xs font-bold text-emerald-600">{cat.fee}</span>
                  </div>
                  <h3 className="text-lg font-extrabold text-foreground">{cat.title}</h3>
                  <p className="text-xs text-secondary leading-relaxed bg-surface p-3 rounded-xl border border-border/60">
                    <strong className="text-foreground">যোগ্যতা:</strong> {cat.eligibility}
                  </p>
                  <ul className="space-y-2.5 pt-2">
                    {cat.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-secondary">
                        <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <Link
                  href={`/membership/apply?type=${cat.badge}`}
                  className="w-full py-2.5 px-4 rounded-xl bg-primary text-white text-xs font-bold text-center hover:opacity-95 transition-all"
                >
                  এই ক্যাটাগরিতে আবেদন করুন
                </Link>
              </div>
            ))}
          </div>
        </div>

        {/* 3-Step Application Workflow */}
        <div className="bg-card border border-border rounded-3xl p-8 space-y-6 shadow-sm">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl font-extrabold text-foreground">আবেদন ও অনুমোদন প্রক্রিয়া</h2>
            <p className="text-xs text-secondary">
              সম্পূর্ণ কাগজবিহীন ও স্বচ্ছ পদ্ধতিতে ৩টি ধাপে সদস্যপদ নিবন্ধন সম্পন্ন হয়
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            {steps.map((s) => (
              <div key={s.step} className="p-5 rounded-2xl bg-surface border border-border space-y-2">
                <div className="w-10 h-10 rounded-xl bg-primary text-white font-mono font-bold text-sm flex items-center justify-center">
                  {s.step}
                </div>
                <h3 className="font-bold text-sm text-foreground pt-1">{s.title}</h3>
                <p className="text-xs text-secondary leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-border flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs text-secondary">
              <FileText size={16} className="text-primary" />
              <span>প্রয়োজনীয় ডকুমেন্ট: পিজিসিবি আইডি কার্ড, ডিপ্লোমা সনদ, জাতীয় পরিচয়পত্র ও পাসপোর্ট সাইজ ছবি।</span>
            </div>
            <div className="flex items-center gap-3">
              <Link
                href="/verify"
                className="px-4 py-2 rounded-xl border border-border text-xs font-bold text-foreground hover:bg-surface"
              >
                সদস্য কার্ড যাচাই
              </Link>
              <Link
                href="/membership/apply"
                className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90"
              >
                এখনই আবেদন শুরু করুন
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
