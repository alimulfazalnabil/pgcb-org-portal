'use client';

import Link from 'next/link';
import { useLanguage } from '../lib/i18n';

export function Footer() {
  const { t } = useLanguage();

  return (
    <footer style={{ background: 'var(--navy, #0f172a)', color: '#d7dfeb', padding: '60px 0 24px' }}>
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xl">⚡</span>
            <h3 style={{ color: '#fff', margin: 0, fontSize: '18px', fontWeight: 700 }}>
              {t('পাওয়ার গ্রিড প্রকৌশলী সমিতি', 'Power Grid Engineers Association')}
            </h3>
          </div>
          <p style={{ lineHeight: 1.8, fontSize: '14px', color: '#94a3b8' }}>
            {t(
              'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের কল্যাণ, পেশাগত উন্নয়ন এবং জাতীয় গ্রিড সঞ্চালন সেবায় নিবেদিত সংগঠন।',
              'Dedicated to the welfare, professional development, and national grid transmission excellence of Power Grid Bangladesh PLC (PGCB) engineers.'
            )}
          </p>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>
            {t('দ্রুত লিঙ্ক', 'Quick Links')}
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><Link href="/about" className="hover:text-white transition-colors">{t('আমাদের সম্পর্কে', 'About Us')}</Link></li>
            <li><Link href="/leadership" className="hover:text-white transition-colors">{t('কেন্দ্রীয় ও সার্কেল কমিটি', 'Central & Circle Committees')}</Link></li>
            <li><Link href="/members" className="hover:text-white transition-colors">{t('সদস্য ডিরেক্টরি', 'Member Directory')}</Link></li>
            <li><Link href="/notices" className="hover:text-white transition-colors">{t('অফিসিয়াল নোটিশ বোর্ড', 'Official Notice Board')}</Link></li>
            <li><Link href="/circulars" className="hover:text-white transition-colors">{t('সার্কুলার ও আদেশ', 'Circulars & Orders')}</Link></li>
            <li><Link href="/documents" className="hover:text-white transition-colors">{t('ফরম ও প্রকাশনা', 'Forms & Publications')}</Link></li>
          </ul>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>
            {t('সদস্য সেবা ও পোর্টাল', 'Member Services & Portal')}
          </h4>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <li><Link href="/membership/apply" className="hover:text-white transition-colors">{t('সদস্যপদের আবেদন', 'Apply for Membership')}</Link></li>
            <li><Link href="/membership/track" className="hover:text-white transition-colors">{t('আবেদনের অগ্রগতি ট্র্যাকিং', 'Track Application Status')}</Link></li>
            <li><Link href="/verify" className="hover:text-white transition-colors">{t('ডিজিটাল সদস্যপদ যাচাই', 'Digital Membership Verification')}</Link></li>
            <li><Link href="/portal" className="hover:text-white transition-colors">{t('মেম্বার ড্যাশবোর্ড', 'Member Dashboard')}</Link></li>
            <li><Link href="/events" className="hover:text-white transition-colors">{t('ইভেন্ট ও সম্মেলন', 'Events & Conferences')}</Link></li>
            <li><Link href="/admin" className="hover:text-white transition-colors">{t('অ্যাডমিন কনসোল', 'Admin Console')}</Link></li>
          </ul>
        </div>

        <div>
          <h4 style={{ color: '#fff', fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>
            {t('যোগাযোগ ও নীতি', 'Contact & Policies')}
          </h4>
          <p style={{ fontSize: '14px', color: '#94a3b8', lineHeight: 1.6, margin: '0 0 12px 0' }}>
            {t('পিজিসিবি প্রধান কার্যালয়, আফতাবনগর, ঢাকা-১২১২', 'PGCB Head Office, Aftabnagar, Dhaka-1212')}
          </p>
          <p style={{ fontSize: '14px', color: '#94a3b8', margin: '0 0 12px 0' }}>
            {t('ইমেইল:', 'Email:')} <a href="mailto:info@pgcb.gov.bd" className="text-emerald-400">info@pgcb.gov.bd</a>
          </p>
          <div style={{ display: 'flex', gap: '12px', fontSize: '13px', color: '#64748b', flexWrap: 'wrap' }}>
            <Link href="/privacy" className="hover:text-slate-300">{t('গোপনীয়তা', 'Privacy Policy')}</Link>
            <span>•</span>
            <Link href="/terms" className="hover:text-slate-300">{t('শর্তাবলী', 'Terms of Use')}</Link>
            <span>•</span>
            <Link href="/accessibility" className="hover:text-slate-300">{t('অ্যাক্সেসিবিলিটি', 'Accessibility')}</Link>
            <span>•</span>
            <Link href="/search" className="hover:text-slate-300">{t('সাইট সার্চ', 'Site Search')}</Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6" style={{ borderTop: '1px solid #1e293b', marginTop: '40px', paddingTop: '20px', fontSize: '13px', color: '#64748b', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div>
          &copy; {new Date().getFullYear()}{' '}
          {t(
            'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস) · Power Grid Bangladesh PLC · সর্বস্বত্ব সংরক্ষিত।',
            'Diploma Engineers Association, PGCB (Diprokous) · Power Grid Bangladesh PLC · All rights reserved.'
          )}
        </div>
        <div>{t('সরকারি ও প্রাতিষ্ঠানিক ডিজিটাল সেবা পোর্টাল', 'Official Institutional Digital Service Portal')}</div>
      </div>
    </footer>
  );
}

export default Footer;
