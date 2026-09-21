import Link from 'next/link';

export default function AboutPage() {
  return (
    <section className="py-16 px-4 md:px-8 max-w-5xl mx-auto">
      <div className="text-center mb-12">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 mb-3">
          আমাদের ইতিহাস ও লক্ষ্য
        </span>
        <h1 className="text-3xl md:text-5xl font-bold text-primary mb-4">আমাদের সম্পর্কে</h1>
        <p className="text-secondary max-w-2xl mx-auto text-base leading-relaxed">
          পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর আওতাধীন ডিপ্লোমা প্রকৌশলীদের পেশাগত উৎকর্ষ, ঐক্য ও অধিকার সুরক্ষায় নিবেদিত সংগঠন।
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-8 my-10">
        <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
          <h2 className="text-xl font-bold text-primary mb-3">🎯 আমাদের লক্ষ্য</h2>
          <p className="text-secondary leading-relaxed">
            জাতীয় বিদ্যুৎ গ্রিড ব্যবস্থার আধুনিকায়ন, নিরবচ্ছিন্ন বিদ্যুৎ সঞ্চালন নিশ্চিতকরণ এবং কারিগরি জনশক্তির দক্ষতা বৃদ্ধির লক্ষ্যে কাজ করা।
          </p>
        </div>
        <div className="bg-surface p-6 rounded-xl border border-border shadow-sm">
          <h2 className="text-xl font-bold text-primary mb-3">⚡ সাংগঠনিক কাঠামো</h2>
          <p className="text-secondary leading-relaxed">
            দেশব্যাপী ৯টি গ্রিড সার্কেল এবং কেন্দ্রীয় নির্বাহী পরিষদের সুসমন্বিত নেতৃত্বে সমিতির সাংগঠনিক কার্যক্রম পরিচালিত হয়।
          </p>
        </div>
      </div>

      <div className="text-center mt-12">
        <Link href="/committee" className="inline-flex items-center gap-2 bg-primary text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-dark transition-colors shadow">
          নির্বাহী কমিটি দেখুন →
        </Link>
      </div>
    </section>
  );
}
