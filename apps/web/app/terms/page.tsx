import React from 'react';
import Link from 'next/link';

export default function TermsPage() {
  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-8">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
            TERMS OF USE
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
            ব্যবহারের শর্তাবলি
          </h1>
          <p className="text-slate-300 text-base">
            অফিসিয়াল ওয়েবসাইট, সদস্য পোর্টাল, ডিজিটাল আইডি যাচাইকরণ ও অনলাইন সেবার ব্যবহারবিধি।
          </p>
        </div>

        <article className="bg-white rounded-3xl border border-slate-200/80 p-8 sm:p-12 shadow-sm space-y-6 text-slate-700 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">১. সদস্য অ্যাকাউন্ট ও তথ্যের সত্যতা</h2>
            <p>
              সদস্যপদ আবেদন ও প্রোফাইল হালনাগাদের সময় সঠিক, প্রামাণ্য ও হালনাগাদ দাপ্তরিক তথ্য প্রদান করতে হবে। অ্যাকাউন্টের পাসওয়ার্ড ও সেশনের গোপনীয়তা রক্ষা করার দায়িত্ব ব্যবহারকারীর নিজের।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">২. অফিসিয়াল প্রকাশনা ও মেধাস্বত্ব</h2>
            <p>
              পোর্টালে প্রকাশিত সকল নোটিশ, সার্কুলার, গঠনতন্ত্র, কারিগরি জার্নাল ও ডিজিটাল সনদপত্র ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর অনুমোদিত দাপ্তরিক প্রকাশনা হিসেবে বিবেচিত হবে।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">৩. ডিজিটাল আইডি ও কিউআর যাচাইকরণ</h2>
            <p>
              সদস্য যাচাইকরণ সেবা কেবল সদস্যপদের বৈধতা নিশ্চিত করার উদ্দেশ্যে ব্যবহার করা যাবে। স্বয়ংক্রিয় স্ক্র্যাপিং বা তথ্যের অননুমোদিত বাণিজ্যিক ব্যবহার সম্পূর্ণ নিষিদ্ধ।
            </p>
          </section>

          <div className="pt-6 border-t border-slate-100 flex items-center justify-between flex-wrap gap-4 text-sm">
            <span className="text-slate-500">সর্বশেষ হালনাগাদ: ২০২৬</span>
            <Link href="/privacy" className="font-extrabold text-primary hover:underline">
              গোপনীয়তা নীতি দেখুন →
            </Link>
          </div>
        </article>
      </div>
    </div>
  );
}
