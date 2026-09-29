'use client';

import Link from 'next/link';
import { ShieldCheck, Target, HeartHandshake, ArrowRight } from 'lucide-react';
import { useLanguage } from '../../lib/i18n';

export default function AboutPage() {
  const { t } = useLanguage();

  return (
    <div className="py-12 px-4 md:px-8 max-w-6xl mx-auto min-h-screen">
      {/* Title */}
      <div className="text-center mb-12">
        <span className="inline-block px-3.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 mb-3">
          {t('পরিচিতি ও রূপরেখা · PGCB Engineers Association', 'Institutional Profile · PGCB Engineers Association')}
        </span>
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-slate-900 mb-3">
          {t('আমাদের সম্পর্কে', 'About Us')}
        </h1>
        <p className="text-slate-600 max-w-3xl mx-auto text-sm sm:text-base md:text-lg leading-relaxed">
          {t(
            'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের পেশাগত উৎকর্ষ, সাংগঠনিক ঐক্য ও জাতীয় বিদ্যুৎ সঞ্চালন সেবায় নিবেদিত প্রাতিষ্ঠানিক প্ল্যাটফর্ম।',
            'The dedicated institutional platform for professional excellence, organizational unity, and national power transmission service of engineers at Power Grid Company of Bangladesh (PGCB).'
          )}
        </p>
      </div>

      {/* History & Foundation */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 md:p-10 shadow-sm mb-10">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span>📜</span> {t('পটভূমি ও প্রাতিষ্ঠানিক ইতিহাস', 'Background & Institutional History')}
        </h2>
        <div className="space-y-4 text-slate-700 leading-relaxed text-sm md:text-base">
          <p>
            {t(
              'বাংলাদেশ বিদ্যুৎ উন্নয়ন বোর্ড (বিউবো) হতে গ্রিড সঞ্চালন ব্যবস্থা পৃথকীকরণের মাধ্যমে ১৯৯৬ সালে পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি) গঠিত হয়। দেশের প্রত্যন্ত অঞ্চলে উচ্চ ভোল্টেজের ৪০০ কেভি, ২৩০ কেভি ও ১৩২ কেভি বিদ্যুৎ সঞ্চালন লাইন ও সাব-স্টেশন পরিচালনায় ডিপ্লোমা প্রকৌশলীবৃন্দ শুরু থেকেই অগ্রণী ভূমিকা পালন করে আসছেন।',
              'Power Grid Company of Bangladesh (PGCB) was established in 1996 by unbundling the power transmission system from the Bangladesh Power Development Board (BPDB). From the very beginning, diploma engineers have played a pioneering role in operating and maintaining high-voltage 400kV, 230kV, and 132kV transmission lines and grid substations across Bangladesh.'
            )}
          </p>
          <p>
            {t(
              'কর্মরত প্রকৌশলীদের পেশাগত অধিকার রক্ষা, কারিগরি সক্ষমতা বৃদ্ধি, প্রশিক্ষণ কর্মসূচি পরিচালনা এবং সদস্য ও তাদের পরিবারের পারস্পরিক কল্যাণ নিশ্চিত করার লক্ষ্য নিয়ে সমিতি গঠিত হয়। বর্তমান ডিজিটাল যুগে সকল সদস্যকে একটি একক নেটওয়ার্কে যুক্ত করতে এই ডিজিটাল পোর্টাল বাস্তবায়িত হয়েছে।',
              'The association was formed to safeguard professional rights, enhance technical capacity, conduct training programs, and ensure the mutual welfare of member engineers and their families. This digital portal connects all members nationwide under one unified institutional network.'
            )}
          </p>
        </div>
      </div>

      {/* Core Values / Vision Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-10">
        <div className="bg-emerald-50/50 p-6 rounded-xl border border-emerald-100 shadow-sm">
          <div className="w-11 h-11 bg-emerald-700 text-white rounded-lg flex items-center justify-center mb-4">
            <Target size={22} />
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2">
            {t('আমাদের লক্ষ্য ও উদ্দেশ্য', 'Our Vision & Mission')}
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            {t(
              'জাতীয় গ্রিড ব্যবস্থার আধুনিকায়ন, প্রকৌশলীদের কারিগরি জ্ঞান বিনিময় এবং সর্বোচ্চ পেশাদারিত্বের সাথে স্মার্ট বাংলাদেশ বিনির্মাণে অবদান রাখা।',
              'Modernizing the national power grid, fostering technical knowledge exchange among engineers, and contributing to national development with the highest professionalism.'
            )}
          </p>
        </div>

        <div className="bg-blue-50/50 p-6 rounded-xl border border-blue-100 shadow-sm">
          <div className="w-11 h-11 bg-blue-700 text-white rounded-lg flex items-center justify-center mb-4">
            <HeartHandshake size={22} />
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2">
            {t('সদস্য কল্যাণ ও সহযোগিতা', 'Member Welfare & Support')}
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            {t(
              'সদস্য প্রকৌশলী ও তাদের পরিবারের চিকিৎসাগত সহায়তা, আকস্মিক দুর্ঘটনাজনিত সহযোগিতা এবং শিক্ষাবৃত্তি প্রদান সংক্রান্ত কার্যক্রম।',
              'Providing medical assistance, emergency support, and educational scholarships for member engineers and their families.'
            )}
          </p>
        </div>

        <div className="bg-amber-50/50 p-6 rounded-xl border border-amber-100 shadow-sm">
          <div className="w-11 h-11 bg-amber-700 text-white rounded-lg flex items-center justify-center mb-4">
            <ShieldCheck size={22} />
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-2">
            {t('অধিকার ও পেশাগত মর্যাদা', 'Rights & Professional Dignity')}
          </h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            {t(
              'ন্যায্য পদোন্নতি, পদমর্যাদা ও চাকরিকালীন সুযোগ-সুবিধা সংরক্ষণ এবং কর্তৃপক্ষের সাথে পারস্পরিক গঠনমূলক আলোচনার মাধ্যমে দাবি পূরণ।',
              'Safeguarding fair promotion, professional dignity, and service benefits through constructive institutional dialogue with management.'
            )}
          </p>
        </div>
      </div>

      {/* Organizational Structure */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8 md:p-10 mb-10 shadow-md">
        <div className="max-w-3xl">
          <h2 className="text-xl sm:text-2xl font-bold mb-3">
            {t('সাংগঠনিক কাঠামো ও বিস্তৃতি', 'Organizational Structure & Reach')}
          </h2>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed mb-6">
            {t(
              'সমিতির কার্যক্রম কেন্দ্রীয় নির্বাহী কমিটি এবং আঞ্চলিক গ্রিড সার্কেল সমূহের সমন্বয়ে গণতান্ত্রিক নীতিমালার আলোকে পরিচালিত হয়।',
              'The association operates democratically through coordination between the Central Executive Committee and regional Grid Circle committees.'
            )}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs md:text-sm">
            <div className="bg-white/10 p-4 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-sm sm:text-base mb-1">
                {t('কেন্দ্রীয় পরিষদ', 'Central Council')}
              </span>
              {t('নির্বাহী নীতিনির্ধারণী ফোরাম', 'Executive policy-making forum')}
            </div>
            <div className="bg-white/10 p-4 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-sm sm:text-base mb-1">
                {t('আঞ্চলিক সার্কেল', 'Regional Circles')}
              </span>
              {t('দেশব্যাপী মাঠপর্যায়ের শাখা', 'Nationwide field-level branches')}
            </div>
            <div className="bg-white/10 p-4 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-sm sm:text-base mb-1">
                {t('ডিজিটাল সেবা', 'Digital Services')}
              </span>
              {t('আইডি ভেরিফিকেশন ও ট্র্যাকিং', 'ID verification & application tracking')}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap justify-center gap-3 pt-2">
        <Link
          href="/leadership"
          className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm"
        >
          {t('নির্বাহী কমিটি দেখুন', 'View Executive Committee')} <ArrowRight size={16} />
        </Link>
        <Link
          href="/documents"
          className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-800 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all"
        >
          {t('গঠনতন্ত্র ও নীতিমালা ডাউনলোড', 'Download Constitution & Policies')}
        </Link>
        <Link
          href="/membership/apply"
          className="inline-flex items-center gap-2 bg-white border border-slate-300 hover:border-emerald-600 text-emerald-800 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all"
        >
          {t('সদস্যপদ আবেদন করুন', 'Apply for Membership')}
        </Link>
      </div>
    </div>
  );
}
