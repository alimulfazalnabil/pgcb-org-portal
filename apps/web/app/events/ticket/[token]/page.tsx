'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

export default function EventTicketPage() {
  const params = useParams<{ token: string }>();
  const token = decodeURIComponent(String(params?.token || ''));

  return (
    <div className="bg-slate-50 min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-xl mx-auto">
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xl overflow-hidden">
          <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-emerald-950 p-8 text-white text-center">
            <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-extrabold uppercase tracking-widest bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 mb-3">
              VERIFIED E-TICKET • DELEGATE PASS
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-1">
              ইভেন্ট প্রবেশপত্র ও ডেলিগেট পাস
            </h1>
            <p className="text-slate-300 text-xs">
              ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)
            </p>
          </div>

          <div className="p-8 text-center space-y-6">
            <div className="w-36 h-36 mx-auto rounded-2xl border-2 border-dashed border-emerald-500/50 bg-emerald-50/50 flex flex-col items-center justify-center p-4">
              <img src="/brand/pgcb-logo.svg" alt="PGCB QR Pass" className="w-16 h-16 object-contain mb-2" />
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-emerald-800">
                QR VERIFIED PASS
              </span>
            </div>

            <div>
              <div className="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-1">
                টিকেট রেফারেন্স কোড
              </div>
              <div className="inline-block font-mono text-lg font-extrabold px-4 py-1.5 rounded-xl bg-slate-100 text-slate-900 border border-slate-200">
                {token}
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs font-semibold leading-relaxed">
              চেক-ইন কাউন্টারে এই ডিজিটাল টিকেট কোডটি প্রদর্শন করুন। প্রিন্ট করার জন্য নিচের বাটনে ক্লিক করুন।
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-center gap-3 flex-wrap">
              <button
                type="button"
                onClick={() => typeof window !== 'undefined' && window.print()}
                className="px-6 py-2.5 rounded-xl bg-primary text-white text-xs font-extrabold hover:bg-emerald-800 transition-colors"
              >
                টিকেট প্রিন্ট / পিডিএফ সংরক্ষণ করুন
              </button>
              <Link
                href="/events"
                className="px-6 py-2.5 rounded-xl bg-slate-100 text-slate-800 text-xs font-extrabold hover:bg-slate-200 transition-colors"
              >
                ইভেন্ট তালিকায় ফিরুন
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
