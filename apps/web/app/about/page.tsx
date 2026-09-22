import Link from 'next/link';
import { ShieldCheck, Target, HeartHandshake, BookOpen, Users, Award, ArrowRight } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="py-16 px-4 md:px-8 max-w-6xl mx-auto min-h-screen">
      {/* Title */}
      <div className="text-center mb-16">
        <span className="inline-block px-3.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 mb-3">
          পরিচিতি ও রূপরেখা &middot; PGCB Engineers Association
        </span>
        <h1 className="text-3xl md:text-5xl font-bold text-slate-900 mb-4">
          আমাদের সম্পর্কে
        </h1>
        <p className="text-slate-600 max-w-3xl mx-auto text-base md:text-lg leading-relaxed">
          পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের পেশাগত উৎকর্ষ, সাংগঠনিক ঐক্য ও জাতীয় বিদ্যুৎ সঞ্চালন সেবায় নিবেদিত প্রাতিষ্ঠানিক প্ল্যাটফর্ম।
        </p>
      </div>

      {/* History & Foundation */}
      <div className="bg-white rounded-2xl border border-slate-200 p-8 md:p-12 shadow-sm mb-12">
        <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-2">
          <span>📜</span> পটভূমি ও প্রাতিষ্ঠানিক ইতিহাস
        </h2>
        <div className="space-y-4 text-slate-700 leading-relaxed text-sm md:text-base">
          <p>
            বাংলাদেশ বিদ্যুৎ উন্নয়ন বোর্ড (বিউবো) হতে গ্রিড সঞ্চালন ব্যবস্থা পৃথকীকরণের মাধ্যমে ১৯৯৬ সালে পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি) গঠিত হয়। দেশের প্রত্যন্ত অঞ্চলে উচ্চ ভোল্টেজের ৪০০ কেভি, ২৩০ কেভি ও ১৩২ কেভি বিদ্যুৎ সঞ্চালন লাইন ও সাব-স্টেশন পরিচালনায় ডিপ্লোমা প্রকৌশলীবৃন্দ শুরু থেকেই অগ্রণী ভূমিকা পালন করে আসছেন।
          </p>
          <p>
            কর্মরত প্রকৌশলীদের পেশাগত অধিকার রক্ষা, কারিগরি সক্ষমতা বৃদ্ধি, প্রশিক্ষণ কর্মসূচি পরিচালনা এবং সদস্য ও তাদের পরিবারের পারস্পরিক কল্যাণ নিশ্চিত করার লক্ষ্য নিয়ে সমিতি গঠিত হয়। বর্তমান ডিজিটাল যুগে সকল সদস্যকে একটি একক নেটওয়ার্কে যুক্ত করতে এই ডিজিটাল পোর্টাল বাস্তবায়িত হয়েছে।
          </p>
        </div>
      </div>

      {/* Core Values / Vision Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="bg-emerald-50/50 p-6 rounded-xl border border-emerald-100 shadow-sm">
          <div className="w-12 h-12 bg-emerald-700 text-white rounded-lg flex items-center justify-center mb-4">
            <Target size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">আমাদের লক্ষ্য ও উদ্দেশ্য</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            জাতীয় গ্রিড ব্যবস্থার আধুনিকায়ন, প্রকৌশলীদের কারিগরি জ্ঞান বিনিময় এবং সর্বোচ্চ পেশাদারিত্বের সাথে স্মার্ট বাংলাদেশ বিনির্মাণে অবদান রাখা।
          </p>
        </div>

        <div className="bg-blue-50/50 p-6 rounded-xl border border-blue-100 shadow-sm">
          <div className="w-12 h-12 bg-blue-700 text-white rounded-lg flex items-center justify-center mb-4">
            <HeartHandshake size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">সদস্য কল্যাণ ও সহযোগিতা</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            সদস্য প্রকৌশলী ও তাদের পরিবারের চিকিৎসাগত সহায়তা, আকস্মিক দুর্ঘটনাজনিত সহযোগিতা এবং শিক্ষাবৃত্তি প্রদান সংক্রান্ত কার্যক্রম।
          </p>
        </div>

        <div className="bg-amber-50/50 p-6 rounded-xl border border-amber-100 shadow-sm">
          <div className="w-12 h-12 bg-amber-700 text-white rounded-lg flex items-center justify-center mb-4">
            <ShieldCheck size={24} />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">অধিকার ও পেশাগত মর্যাদা</h3>
          <p className="text-slate-600 text-sm leading-relaxed">
            ন্যায্য পদোন্নতি, পদমর্যাদা ও চাকরিকালীন সুযোগ-সুবিধা সংরক্ষণ এবং কর্তৃপক্ষের সাথে পারস্পরিক গঠনমূলক আলোচনার মাধ্যমে দাবি পূরণ।
          </p>
        </div>
      </div>

      {/* Organizational Structure */}
      <div className="bg-slate-900 text-white rounded-2xl p-8 md:p-12 mb-12 shadow-md">
        <div className="max-w-3xl">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">সাংগঠনিক কাঠামো ও বিস্তৃতি</h2>
          <p className="text-slate-300 text-sm md:text-base leading-relaxed mb-6">
            সমিতির কার্যক্রম কেন্দ্রীয় নির্বাহী কমিটি এবং আঞ্চলিক গ্রিড সার্কেল সমূহের সমন্বয়ে গণতান্ত্রিক নীতিমালার আলোকে পরিচালিত হয়।
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs md:text-sm">
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-base mb-1">কেন্দ্রীয় পরিষদ</span>
              নির্বাহী নীতিনির্ধারণী ফোরাম
            </div>
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-base mb-1">আঞ্চলিক সার্কেল</span>
              দেশব্যাপী মাঠপর্যায়ের শাখা
            </div>
            <div className="bg-white/10 p-3 rounded-lg border border-white/10">
              <span className="font-bold text-emerald-400 block text-base mb-1">ডিজিটাল সেবা</span>
              আইডি ভেরিফিকেশন ও ট্র্যাকিং
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap justify-center gap-4 pt-4">
        <Link
          href="/leadership"
          className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white px-6 py-3 rounded-lg font-semibold transition-all shadow-sm"
        >
          নির্বাহী কমিটি দেখুন <ArrowRight size={16} />
        </Link>
        <Link
          href="/documents"
          className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-800 px-6 py-3 rounded-lg font-semibold transition-all"
        >
          গঠনতন্ত্র ও নীতিমালা ডাউনলোড
        </Link>
        <Link
          href="/membership/apply"
          className="inline-flex items-center gap-2 bg-white border border-slate-300 hover:border-emerald-600 text-emerald-800 px-6 py-3 rounded-lg font-semibold transition-all"
        >
          সদস্যপদ আবেদন করুন
        </Link>
      </div>
    </div>
  );
}
