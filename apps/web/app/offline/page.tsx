import Link from 'next/link';

export default function OfflinePage() {
  return (
    <section className="max-w-2xl mx-auto px-4 py-16 text-center space-y-6">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-500/10 text-amber-600 font-bold text-2xl">
        ⚡
      </div>
      <h1 className="text-2xl md:text-3xl font-bold text-foreground">
        আপনি বর্তমানে অফলাইনে আছেন (Offline Mode)
      </h1>
      <p className="text-sm text-secondary leading-relaxed">
        আপনার ইন্টারনেট সংযোগ বিচ্ছিন্ন রয়েছে। তবে ক্যাশ করা ডিজিটাল আইডি কার্ড, সর্বশেষ দেখা নোটিশ ও ইভেন্ট পেজগুলো অফলাইনেও দেখা যাবে।
      </p>
      <div className="flex flex-wrap justify-center gap-3 pt-2">
        <Link
          href="/portal/id-card"
          className="px-5 py-2.5 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90"
        >
          ডিজিটাল আইডি কার্ড (Cached ID Card)
        </Link>
        <Link
          href="/notices"
          className="px-5 py-2.5 rounded-xl border border-border bg-card text-foreground text-xs font-semibold hover:bg-surface"
        >
          নোটিশ বোর্ড (Notices)
        </Link>
        <Link
          href="/"
          className="px-5 py-2.5 rounded-xl border border-border bg-card text-foreground text-xs font-semibold hover:bg-surface"
        >
          হোমপেজে ফিরুন (Home)
        </Link>
      </div>
    </section>
  );
}
