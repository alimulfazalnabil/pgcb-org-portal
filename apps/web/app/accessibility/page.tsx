import React from 'react';
import Link from 'next/link';

export default function AccessibilityPage() {
  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 rounded-3xl p-8 sm:p-12 text-white shadow-xl mb-8">
          <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
            ACCESSIBILITY STATEMENT
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
            অ্যাক্সেসিবিলিটি ও সর্বজনীন ব্যবহারযোগ্যতা
          </h1>
          <p className="text-slate-300 text-base">
            সকল ডিভাইস, স্ক্রিন রিডার ও কিবোর্ড ব্যবহারকারীদের জন্য পোর্টালটি সহজলভ্য রাখার অঙ্গীকার।
          </p>
        </div>

        <article className="bg-white rounded-3xl border border-slate-200/80 p-8 sm:p-12 shadow-sm space-y-6 text-slate-700 leading-relaxed">
          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">১. সমর্থিত মানদণ্ড</h2>
            <p>
              পোর্টালটিতে সেমান্টিক HTML5 ল্যান্ডমার্ক, স্কিপ-টু-কনটেন্ট লিংক, স্পষ্ট বাংলা ও ইংরেজি টাইপোগ্রাফি (Hind Siliguri ও Plus Jakarta Sans), পর্যাপ্ত রঙের কনট্রাস্ট এবং মোবাইল-ফার্স্ট রেসপনসিভ লেআউট অনুসরণ করা হয়েছে।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">২. কিবোর্ড নেভিগেশন</h2>
            <p>
              প্রধান মেনু, অনুসন্ধান ক্ষেত্র, আবেদন ফর্ম এবং ডায়ালগসমূহ কিবোর্ড ট্যাব ও এন্টার/এস্কেপ কমান্ডের মাধ্যমে পরিচালনাযোগ্য।
            </p>
          </section>

          <section className="space-y-2">
            <h2 className="text-xl font-extrabold text-slate-900">৩. সহায়তা ও মতামত</h2>
            <p>
              পোর্টাল ব্যবহারে কোনো অ্যাক্সেসিবিলিটি প্রতিবন্ধকতা পরিলক্ষিত হলে অনুগ্রহ করে আমাদের{' '}
              <Link href="/contact" className="font-bold text-primary underline">
                যোগাযোগ ফর্ম
              </Link>{' '}
              ব্যবহার করে জানান।
            </p>
          </section>
        </article>
      </div>
    </div>
  );
}
