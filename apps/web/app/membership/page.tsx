import type { Metadata } from 'next';
import Link from 'next/link';
import { UserPlus, CheckCircle2, CreditCard, ShieldCheck, Users, Award } from 'lucide-react';

export const metadata: Metadata = {
  title: 'সদস্যপদ তথ্য ও নির্দেশিকা | পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশল সমিতি (PGCB)',
  description:
    'পিজিসিবি ডিপ্লোমা প্রকৌশল সমিতির সদস্যপদ যোগ্যতা, বার্ষিক নবায়ন ফি, সুবিধা, ডিজিটাল আইডি কার্ড এবং অনলাইন আবেদন প্রক্রিয়া।',
  alternates: { canonical: '/membership' },
  openGraph: {
    title: 'সদস্যপদ তথ্য ও নির্দেশিকা | PGCB Diploma Engineers Association',
    description:
      'Official membership eligibility, benefits, fee structure, digital ID verification, and online application portal for PGCB engineers.',
    type: 'website',
    url: '/membership',
  },
};

export default function MembershipOverviewPage() {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: 'PGCB Membership Overview & Guidelines',
    description:
      'Official membership guidelines, eligibility criteria, fee structure, and online application portal for Power Grid Company of Bangladesh (PGCB) Diploma Engineers.',
  };

  return (
    <section className="section">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="container space-y-8">
        <div className="card card-body bg-gradient-to-br from-primary/10 via-card to-card border border-border p-6 md:p-8">
          <span className="badge badge-primary mb-3">PGCB Membership Portal 2.0</span>
          <h1 className="text-2xl md:text-4xl font-extrabold text-foreground">
            পিজিসিবি ডিপ্লোমা প্রকৌশল সমিতি — সদস্যপদ নির্দেশিকা ২০২৬
          </h1>
          <p className="text-sm md:text-base text-secondary mt-2 max-w-3xl">
            পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এ কর্মরত ডিপ্লোমা প্রকৌশলীদের পেশাগত মানোন্নয়ন, কল্যাণ তহবিল,
            ডিজিটাল আইডি কার্ড এবং ৯টি গ্রিড সার্কেলের সমন্বিত সদস্য সেবা।
          </p>
          <div className="flex flex-wrap gap-3 mt-5">
            <Link href="/apply" className="btn btn-primary inline-flex items-center gap-2">
              <UserPlus size={16} /> অনলাইনে সদস্যপদ আবেদন করুন
            </Link>
            <Link href="/portal" className="btn btn-outline inline-flex items-center gap-2">
              সদস্য পোর্টালে প্রবেশ করুন
            </Link>
            <Link href="/verify" className="btn btn-outline inline-flex items-center gap-2">
              <ShieldCheck size={16} /> সদস্যপদ যাচাই (Verify ID)
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card card-body space-y-3">
            <CheckCircle2 size={24} className="text-primary" />
            <h2 className="text-lg font-bold">সদস্যপদ যোগ্যতা (Eligibility)</h2>
            <p className="text-xs text-secondary leading-relaxed">
              পিজিসিবি-তে কর্মরত উপ-সহকারী প্রকৌশলী ও সমমানের ডিপ্লোমা ইন ইঞ্জিনিয়ারিং ডিগ্রিধারী প্রকৌশলীগণ সাধারণ ও আজীবন
              সদস্যপদের জন্য আবেদন করতে পারবেন।
            </p>
            <Link href="/eligibility" className="text-xs font-bold text-primary hover:underline">
              বিস্তারিত যোগ্যতা দেখুন →
            </Link>
          </div>

          <div className="card card-body space-y-3">
            <CreditCard size={24} className="text-primary" />
            <h2 className="text-lg font-bold">সদস্যপদ ও বার্ষিক নবায়ন ফি</h2>
            <p className="text-xs text-secondary leading-relaxed">
              বার্ষিক সাধারণ সদস্যপদ নবায়ন ফি ২,০০০ টাকা। অনলাইন পেমেন্ট গেটওয়ে (SSLCommerz / bKash / Nagad) এর মাধ্যমে
              তাৎক্ষণিক ডিজিটাল রসিদ ও সক্রিয়করণ।
            </p>
            <Link href="/fees" className="text-xs font-bold text-primary hover:underline">
              ফি কাঠামো দেখুন →
            </Link>
          </div>

          <div className="card card-body space-y-3">
            <Award size={24} className="text-primary" />
            <h2 className="text-lg font-bold">সদস্য সুবিধা ও ডিজিটাল সেবা</h2>
            <p className="text-xs text-secondary leading-relaxed">
              কিউআর কোডযুক্ত ডিজিটাল আইডি কার্ড, অফিসিয়াল সনদ ওয়ালেট, কল্যাণ তহবিল সহায়তা, কারিগরি জার্নাল এবং ইভেন্ট ও
              প্রশিক্ষণে অগ্রাধিকার।
            </p>
            <Link href="/benefits" className="text-xs font-bold text-primary hover:underline">
              সদস্য সুবিধাসমূহ দেখুন →
            </Link>
          </div>
        </div>

        <div className="card card-body flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Users size={22} className="text-primary" />
            <div>
              <h2 className="text-base font-bold">সদস্য ডিরেক্টরি ও গ্রিড সার্কেল</h2>
              <p className="text-xs text-secondary">
                সারা দেশের ৯টি গ্রিড সার্কেলের ১,৫০০+ নিবন্ধিত প্রকৌশলী সদস্যদের তালিকা ও সার্কেল কমিটি দেখুন।
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href="/members" className="btn btn-outline text-xs">
              সদস্য ডিরেক্টরি
            </Link>
            <Link href="/circles" className="btn btn-outline text-xs">
              গ্রিড সার্কেলসমূহ
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
