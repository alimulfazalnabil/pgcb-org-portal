import React from 'react';
import Link from 'next/link';

export default function PrivacyPage() {
  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-8">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
            PRIVACY & DATA PROTECTION POLICY
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
            গোপনীয়তা ও তথ্য সুরক্ষা নীতি
          </h1>
          <p className="text-slate-300 text-base">
            ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর সদস্য তথ্য সংগ্রহ, ব্যবহার ও সুরক্ষা নীতিমালা।
          </p>
        </div>

        <article className="bg-white rounded-3xl border border-slate-200/80 p-8 sm:p-12 shadow-sm space-y-6 text-slate-700 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">১. সংগৃহীত তথ্য</h2>
            <p>
              সদস্য নিবন্ধন, প্রোফাইল যাচাইকরণ, বার্ষিক নবায়ন, ইভেন্ট নিবন্ধন এবং ডিজিটাল আইডি কার্ড ইস্যুর জন্য প্রয়োজনীয় পেশাগত ও পরিচয়-সংক্রান্ত তথ্য (নাম, পদবি, এমপ্লয়ি আইডি, সার্কেল/দপ্তর, ইমেইল, ফোন নম্বর এবং সনদপত্র) সংরক্ষণ করা হয়।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">২. পাবলিক ও প্রাইভেট তথ্যের সীমা</h2>
            <p>
              পাবলিক ডিরেক্টরি এবং কিউআর ভেরিফিকেশন পেজে কেবল নাম, পদবি, গ্রিড সার্কেল/শাখা কমিটি, মেম্বারশিপ আইডি এবং সদস্যপদ স্ট্যাটাস প্রদর্শিত হয়। জাতীয় পরিচয়পত্র (NID), ব্যক্তিগত ঠিকানা, ফোন নম্বর ও আপলোডকৃত সনদপত্র কখনোই পাবলিক এপিআই বা কিউআর কোডে উন্মুক্ত করা হয় না।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">৩. তথ্য নিরাপত্তা ও অডিট লগ</h2>
            <p>
              সদস্যদের সকল সংবেদনশীল তথ্য রোল-বেইজড অ্যাক্সেস কন্ট্রোল (RBAC), এনক্রিপ্টেড সেশন ও অপরিবর্তনীয় অডিট লগের মাধ্যমে সুরক্ষিত রাখা হয়। কোনো তৃতীয় পক্ষের কাছে সদস্যদের তথ্য বিক্রি বা হস্তান্তর করা হয় না।
            </p>
          </section>

          <div className="pt-6 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4 text-sm">
            <span className="text-slate-500">সর্বশেষ হালনাগাদ: ২০২৬</span>
            <Link href="/contact" className="font-extrabold text-primary hover:underline">
              তথ্য সুরক্ষা বিষয়ে যোগাযোগ করুন →
            </Link>
          </div>
        </article>
      </div>
    </div>
  );
}
