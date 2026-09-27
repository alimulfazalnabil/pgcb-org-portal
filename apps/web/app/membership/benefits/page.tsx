'use client';

import React from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  HeartHandshake,
  GraduationCap,
  Award,
  Scale,
  BookOpen,
  QrCode,
  Users,
  ArrowRight,
  CheckCircle2,
  UserPlus,
} from 'lucide-react';

export default function MembershipBenefitsPage() {
  const pillars = [
    {
      icon: HeartHandshake,
      title: 'কল্যাণ তহবিল ও জরুরি সহায়তা (Welfare & Mutual Aid)',
      description:
        'সদস্যদের অসুস্থতা, দুর্ঘটনা বা জরুরি পারিবারিক সংকটে কেন্দ্রীয় কল্যাণ তহবিল হতে দ্রুত আর্থিক অনুদান ও চিকিৎসা সহায়তা প্রদান।',
      items: [
        'গুরুতর অসুস্থতা ও জরুরি অস্ত্রোপচারে বিশেষ চিকিৎসা সহায়তা',
        'অবসরগ্রহণকারী সদস্যদের আনুষ্ঠানিক সম্মাননা ও ক্রেস্ট প্রদান',
        'সদস্যদের মেধাবী সন্তানদের বার্ষিক শিক্ষাবৃত্তি ও সংবর্ধনা',
      ],
    },
    {
      icon: GraduationCap,
      title: 'কারিগরি প্রশিক্ষণ ও পেশাগত উন্নয়ন (Technical Excellence)',
      description:
        'স্মার্ট গ্রিড, স্ক্যাডা (SCADA), সাবস্টেশন অটোমেশন ও উচ্চ ভোল্টেজ ট্রান্সমিশন প্রযুক্তির ওপর বিশেষায়িত কর্মশালা ও সেমিনার।',
      items: [
        'জাতীয় ও আন্তর্জাতিক পর্যায়ের পাওয়ার সিস্টেম সেমিনারে অংশগ্রহণ',
        'কারিগরি জার্নাল ও গবেষণা প্রকাশনায় প্রবন্ধ প্রকাশের সুযোগ',
        'অংশগ্রহণকারীদের ডিজিটাল ভেরিফায়েড প্রশিক্ষণ সনদ প্রদান',
      ],
    },
    {
      icon: Scale,
      title: 'পেশাগত অধিকার ও প্রাতিষ্ঠানিক প্রতিনিধিত্ব (Advocacy & Rights)',
      description:
        'পিজিসিবি কর্তৃপক্ষ ও আইডিইবি (IDEB)-এর সাথে সমন্বয়ের মাধ্যমে ডিপ্লোমা প্রকৌশলীদের পদোন্নতি, বেতন কাঠামো ও পেশাগত মর্যাদা সুরক্ষা।',
      items: [
        'প্রাতিষ্ঠানিক নীতিনির্ধারণী সভায় প্রকৌশলীদের যৌক্তিক দাবি উপস্থাপন',
        'পেশাগত দায়িত্ব পালনে উদ্ভূত জটিলতায় সাংগঠনিক ও আইনি পরামর্শ',
        'সার্কেল ও কেন্দ্রীয় কমিটির মাধ্যমে সরাসরি মতামত প্রদানের সুযোগ',
      ],
    },
    {
      icon: QrCode,
      title: 'ডিজিটাল সেবা ও স্মার্ট পরিচয়পত্র (Digital Member Services)',
      description:
        'প্রত্যেক অনুমোদিত সদস্যের জন্য ক্রিপ্টোগ্রাফিক কিউআর কোড সংবলিত ডিজিটাল পরিচয়পত্র ও সেলফ-সার্ভিস মেম্বার পোর্টাল।',
      items: [
        'তাৎক্ষণিক অনলাইন ভেরিফিকেশনযোগ্য ডিজিটাল মেম্বারশিপ কার্ড',
        'অভ্যন্তরীণ সার্কুলার, গেজেট ও মিটিং রেজোলিউশন আর্কাইভে প্রবেশাধিকার',
        'অনলাইনে ইভেন্ট রেজিস্ট্রেশন, পেমেন্ট রিসিট ও সনদ ডাউনলোড',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-surface/30 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider">
            <Award size={15} /> MEMBER PRIVILEGES & WELFARE
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight">
            সদস্যপদের সুবিধাসমূহ ও প্রাতিষ্ঠানিক কল্যাণ
          </h1>
          <p className="text-sm sm:text-base text-secondary leading-relaxed">
            পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির নিবন্ধিত সদস্য হিসেবে আপনি পাচ্ছেন পেশাগত সুরক্ষা, কারিগরি দক্ষতা উন্নয়ন এবং ডিজিটাল প্রাতিষ্ঠানিক সেবার পূর্ণাঙ্গ নিশ্চয়তা।
          </p>
        </div>

        {/* Benefit Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {pillars.map((pillar, index) => {
            const Icon = pillar.icon;
            return (
              <div
                key={index}
                className="bg-card border border-border rounded-2xl p-6 sm:p-8 space-y-5 shadow-sm hover:shadow-md transition-all"
              >
                <div className="flex items-start gap-4">
                  <div className="p-3.5 rounded-2xl bg-primary/10 text-primary shrink-0">
                    <Icon size={26} />
                  </div>
                  <div className="space-y-1.5">
                    <h2 className="text-lg font-extrabold text-foreground">{pillar.title}</h2>
                    <p className="text-xs text-secondary leading-relaxed">{pillar.description}</p>
                  </div>
                </div>

                <div className="pt-3 border-t border-border/60">
                  <ul className="space-y-2.5">
                    {pillar.items.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs text-foreground/90 font-medium">
                        <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA Banner */}
        <div className="bg-card border-2 border-primary/20 rounded-3xl p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
          <div className="space-y-2 max-w-xl">
            <h3 className="text-xl font-extrabold text-foreground">
              আজই আপনার সদস্যপদ নিবন্ধন বা নবায়ন সম্পন্ন করুন
            </h3>
            <p className="text-xs text-secondary leading-relaxed">
              অনলাইনে আবেদন জমা দেওয়ার পর ট্র্যাকিং আইডির মাধ্যমে যেকোনো সময় আপনার আবেদনের সর্বশেষ অগ্রগতি যাচাই করতে পারবেন।
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Link
              href="/membership"
              className="px-4 py-2.5 rounded-xl border border-border text-xs font-bold text-foreground hover:bg-surface"
            >
              সদস্যপদের ক্যাটাগরি দেখুন
            </Link>
            <Link
              href="/membership/apply"
              className="px-6 py-3 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 inline-flex items-center gap-2 shadow-sm"
            >
              <UserPlus size={16} /> সদস্যপদের আবেদন করুন <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
