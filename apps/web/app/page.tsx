import Link from 'next/link';
import { ArrowRight, FileText, Calendar, Users, MapPin } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-primary text-white overflow-hidden">
        {/* Abstract Background Pattern */}
        <div className="absolute inset-0 opacity-10 bg-[url('/pattern.svg')] bg-repeat"></div>
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-accent opacity-20 rounded-full blur-3xl"></div>
        
        <div className="relative max-w-7xl mx-auto px-6 py-20 md:py-32 flex flex-col items-start">
          <span className="inline-block py-1 px-3 rounded-full bg-secondary/50 border border-secondary text-accent text-xs font-semibold tracking-wider mb-6">
            OFFICIAL PORTAL
          </span>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6 max-w-3xl">
            পাওয়ার গ্রিড প্রকৌশলী সমিতি, বাংলাদেশ
          </h1>
          <p className="text-lg md:text-xl text-border/80 mb-10 max-w-2xl">
            দেশের বিদ্যুৎ খাতের উন্নয়নে ও প্রকৌশলীদের পেশাগত মানোন্নয়নে নিবেদিত একটি পেশাজীবী সংগঠন।
          </p>
          
          <div className="flex flex-wrap gap-4">
            <Link 
              href="/register" 
              className="px-8 py-3.5 bg-success text-white font-medium rounded-md hover:bg-emerald-600 transition-colors shadow-lg shadow-success/20"
            >
              সদস্যপদ আবেদন করুন
            </Link>
            <Link 
              href="/verify" 
              className="px-8 py-3.5 bg-transparent border-2 border-border text-white font-medium rounded-md hover:bg-white/10 transition-colors"
            >
              সদস্য ভেরিফিকেশন
            </Link>
          </div>
        </div>
      </section>

      {/* Statistics / Quick Links Section */}
      <section className="max-w-7xl mx-auto px-6 py-12 -mt-16 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { title: "নিবন্ধিত প্রকৌশলী", count: "৩,৫২৭+", icon: Users, color: "text-accent" },
            { title: "গ্রিড সার্কেল", count: "৯ টি", icon: MapPin, color: "text-success" },
            { title: "সাম্প্রতিক নোটিশ", count: "২৪ টি", icon: FileText, color: "text-blue-400" },
            { title: "আসন্ন ইভেন্ট", count: "২ টি", icon: Calendar, color: "text-purple-400" },
          ].map((stat, idx) => (
            <div key={idx} className="glass-panel p-6 rounded-xl flex items-center gap-5">
              <div className={`p-4 rounded-lg bg-primary/5 dark:bg-white/5 ${stat.color}`}>
                <stat.icon size={28} />
              </div>
              <div>
                <p className="text-3xl font-bold text-primary dark:text-white">{stat.count}</p>
                <p className="text-sm font-medium text-secondary">{stat.title}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Notice Board & Circulars Section */}
      <section className="bg-surface py-16">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-3 gap-10">
          
          {/* Main Notice Board (Spans 2 columns) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex justify-between items-end border-b-2 border-primary pb-3">
              <h2 className="text-2xl font-bold text-primary dark:text-white">সাম্প্রতিক নোটিশ ও সার্কুলার</h2>
              <Link href="/circulars" className="text-sm font-medium text-success hover:underline flex items-center gap-1">
                সকল নোটিশ <ArrowRight size={16} />
              </Link>
            </div>
            
            <div className="space-y-4">
              {/* CMS-driven notice mapping will go here */}
              {[1, 2, 3].map((notice) => (
                <div key={notice} className="bg-background p-5 rounded-lg border border-border hover:border-success/50 transition-colors group flex gap-4">
                  <div className="flex flex-col items-center justify-center min-w-[70px] bg-surface rounded p-2 text-primary border border-border">
                    <span className="text-xl font-bold leading-none">১৫</span>
                    <span className="text-xs font-medium uppercase mt-1">আগস্ট</span>
                  </div>
                  <div className="flex flex-col justify-center">
                    <span className="text-xs font-semibold text-accent mb-1">অফিস আদেশ</span>
                    <Link href={`/circulars/${notice}`} className="text-primary dark:text-white font-medium hover:text-success transition-colors line-clamp-2">
                      পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ লিঃ এর উপ-সহকারী প্রকৌশলীদের পদোন্নতি ও বদলি সংক্রান্ত জরুরি অফিস আদেশ।
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sidebar / Leadership Message */}
          <div className="space-y-6">
            <div className="border-b-2 border-primary pb-3">
              <h2 className="text-2xl font-bold text-primary dark:text-white">সভাপতির বার্তা</h2>
            </div>
            <div className="bg-background p-6 rounded-lg border border-border flex flex-col items-center text-center">
              <div className="w-24 h-24 bg-surface rounded-full mb-4 overflow-hidden border-2 border-accent">
                {/* Image Placeholder */}
                <div className="w-full h-full bg-secondary/20"></div>
              </div>
              <h3 className="font-bold text-lg text-primary dark:text-white">প্রকৌশলী মোঃ আব্দুর রহমান</h3>
              <p className="text-xs font-medium text-secondary mb-4">সভাপতি, পি.জি.সি.বি প্রকৌশলী সমিতি</p>
              <p className="text-sm text-secondary line-clamp-4 italic mb-4">
                "দেশের বিদ্যুৎ খাতের অবিচ্ছিন্ন উন্নয়নে আমাদের প্রকৌশলীদের নিরলস পরিশ্রম ও আত্মত্যাগ অনস্বীকার্য। আমরা পেশাগত উৎকর্ষ সাধনে প্রতিশ্রুতিবদ্ধ..."
              </p>
              <Link href="/committee/message" className="text-sm font-medium text-success hover:underline">
                সম্পূর্ণ বার্তা পড়ুন
              </Link>
            </div>
          </div>

        </div>
      </section>
    </div>
  );
}
