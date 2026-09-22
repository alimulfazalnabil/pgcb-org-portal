import Link from 'next/link';

export function Footer() {
  return (
    <footer style={{ background: 'var(--navy, #0f172a)', color: '#d7dfeb', padding: '60px 0 24px' }}>
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">⚡</span>
            <h3 style={{ color: '#fff', margin: 0, fontSize: '18px', fontWeight: 700 }}>
              পাওয়ার গ্রিড প্রকৌশলী সমিতি
            </h3>
          </div>
          <p style={{ lineHeight: 1.8, fontSize: '14px', color: '#94a3b8' }}>
            পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের কল্যাণ, পেশাগত উন্নয়ন এবং জাতীয় গ্রিড সঞ্চালন সেবায় নিবেদিত সংগঠন।
          </p>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>দ্রুত লিঙ্ক</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><Link href="/about" className="hover:text-white transition-colors">আমাদের সম্পর্কে</Link></li>
            <li><Link href="/leadership" className="hover:text-white transition-colors">কেন্দ্রীয় ও সার্কেল কমিটি</Link></li>
            <li><Link href="/members" className="hover:text-white transition-colors">সদস্য ডিরেক্টরি</Link></li>
            <li><Link href="/notices" className="hover:text-white transition-colors">অফিসিয়াল নোটিশ বোর্ড</Link></li>
            <li><Link href="/circulars" className="hover:text-white transition-colors">সার্কুলার ও আদেশ</Link></li>
            <li><Link href="/documents" className="hover:text-white transition-colors">ফরম ও প্রকাশনা</Link></li>
          </ul>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>সদস্য সেবা ও পোর্টাল</h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><Link href="/membership/apply" className="hover:text-white transition-colors">সদস্যপদের আবেদন</Link></li>
            <li><Link href="/membership/track" className="hover:text-white transition-colors">আবেদনের অগ্রগতি ট্র্যাকিং</Link></li>
            <li><Link href="/verify" className="hover:text-white transition-colors">ডিজিটাল সদস্যপদ যাচাই</Link></li>
            <li><Link href="/portal" className="hover:text-white transition-colors">মেম্বার ড্যাশবোর্ড</Link></li>
            <li><Link href="/events" className="hover:text-white transition-colors">ইভেন্ট ও সম্মেলন</Link></li>
            <li><Link href="/admin" className="hover:text-white transition-colors">অ্যাডমিন কনসোল</Link></li>
          </ul>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>যোগাযোগ ও নীতি</h4>
          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6, margin: '0 0 12px 0' }}>
            পিজিসিবি প্রধান কার্যালয়, আফতাবনগর, ঢাকা-১২১২
          </p>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: '0 0 12px 0' }}>
            ইমেইল: <a href="mailto:info@pgcb.gov.bd" className="text-emerald-400">info@pgcb.gov.bd</a>
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '13px', color: '#64748b' }}>
            <Link href="/privacy" className="hover:text-slate-300">গোপনীয়তা</Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-slate-300">শর্তাবলী</Link>
            <span>•</span>
            <Link href="/search" className="hover:text-slate-300">সাইট সার্চ</Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6" style={{ borderTop: '1px solid #1e293b', marginTop: '40px', paddingTop: '20px', fontSize: '13px', color: '#64748b', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div>&copy; 2026 Power Grid Bangladesh PLC &middot; সর্বস্বত্ব সংরক্ষিত।</div>
        <div>সরকারি ও প্রাতিষ্ঠানিক ডিজিটাল সেবা পোর্টাল</div>
      </div>
    </footer>
  );
}

export default Footer;
