import Link from 'next/link';

export default function CommitteeMessagePage() {
  return (
    <section className="py-16 px-4 md:px-8 max-w-4xl mx-auto">
      <div className="bg-surface p-8 md:p-12 rounded-2xl border border-border shadow-sm">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-accent/20 text-accent mb-4">
          সভাপতি ও সাধারণ সম্পাদকের বার্তা
        </span>
        <h1 className="text-3xl md:text-4xl font-bold text-primary mb-6">
          ঐক্য, অধিকার ও পেশাগত মানোন্নয়নের শপথ
        </h1>
        <div className="prose text-secondary leading-relaxed space-y-4 text-base md:text-lg">
          <p>
            বিসমিল্লাহির রাহমানির রাহিম। দেশের বিদ্যুৎ খাতের অবিচ্ছিন্ন উন্নয়নে আমাদের ডিপ্লোমা প্রকৌশলীদের নিরলস পরিশ্রম ও আত্মত্যাগ অনস্বীকার্য। পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর বিদ্যুৎ সঞ্চালন নেটওয়ার্ককে আধুনিক ও ডিজিটাল স্মার্ট গ্রিডে রূপান্তরের অগ্রযাত্রায় আমরা সর্বদা অগ্রণী ভূমিকা পালন করে আসছি।
          </p>
          <p>
            আমাদের সমিতি সদস্যদের অধিকার সংরক্ষণ, পেশাগত মর্যাদা বৃদ্ধি, মেধাভিত্তিক মূল্যায়ন এবং উন্নত কারিগরি প্রশিক্ষণের মাধ্যমে আন্তর্জাতিক মানে পৌঁছাতে বদ্ধপরিকর। সকল প্রকৌশলীর প্রতি আমাদের আহ্বান—ঐক্যবদ্ধ থাকুন এবং দেশের সেবায় আত্মনিয়োগ করুন।
          </p>
        </div>
        <div className="mt-8 pt-6 border-t border-border flex justify-between items-center flex-wrap gap-4">
          <div>
            <h4 className="font-bold text-primary">প্রকৌশলী মোঃ আব্দুর রহমান</h4>
            <p className="text-xs text-secondary">সভাপতি, পি.জি.সি.বি প্রকৌশলী সমিতি</p>
          </div>
          <Link href="/committee" className="text-sm font-semibold text-success hover:underline">
            সম্পূর্ণ নির্বাহী পরিষদ দেখুন →
          </Link>
        </div>
      </div>
    </section>
  );
}
