'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Phone, Mail, MapPin, Menu, X, UserCircle, AlertCircle, FileSearch, ShieldCheck, Globe } from 'lucide-react';
import { api, Notice } from '../lib/api';
import { useLanguage } from '../lib/i18n';

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { language, toggleLanguage, t, pick } = useLanguage();
  const [urgentNotice, setUrgentNotice] = useState<Notice | null>(null);
  const [settings, setSettings] = useState<Record<string, string>>({
    contact_phone: '+880-2-9553663',
    contact_email: 'info@pgcb.gov.bd',
    address_bn: 'পিজিসিবি ভবন, আফতাবনগর, ঢাকা-১২১২',
    address_en: 'PGCB Bhaban, Aftabnagar, Dhaka-1212',
  });

  useEffect(() => {
    let isMounted = true;
    api.getUrgentNotice()
      .then((data) => {
        if (isMounted && data) setUrgentNotice(data);
      })
      .catch(() => {});

    api.getSettings()
      .then((data) => {
        if (isMounted && data) setSettings((prev) => ({ ...prev, ...data }));
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <header className="w-full border-b border-border bg-background sticky top-0 z-50 shadow-sm">
      {/* Layer 1: Announcement Bar (Dynamic from CMS/DB) */}
      {urgentNotice && (
        <div className="bg-danger text-white text-xs py-1.5 px-4 text-center font-medium flex items-center justify-center gap-2">
          <AlertCircle size={14} className="shrink-0" />
          <span>
            {t('জরুরী নোটিশ:', 'Urgent Notice:')} {pick(urgentNotice, 'title', urgentNotice.title_bn)}
          </span>
          <Link
            href={`/notices/${urgentNotice.id}`}
            className="underline font-semibold ml-2 hover:text-accent transition-colors"
          >
            {t('বিস্তারিত দেখুন', 'View Details')} &rarr;
          </Link>
        </div>
      )}

      {/* Layer 2: Utility & Contact Bar */}
      <div className="hidden md:flex justify-between items-center py-1.5 px-6 bg-primary text-white text-xs">
        <div className="flex items-center space-x-4">
          <span className="flex items-center gap-1.5">
            <Phone size={12} /> {settings.contact_phone}
          </span>
          <span className="flex items-center gap-1.5">
            <Mail size={12} /> {settings.contact_email}
          </span>
          <span className="flex items-center gap-1.5">
            <MapPin size={12} /> {language === 'en' ? settings.address_en || 'PGCB Bhaban, Aftabnagar, Dhaka-1212' : settings.address_bn}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/membership/track" className="flex items-center gap-1 hover:text-accent transition-colors">
            <FileSearch size={13} /> {t('আবেদন ট্র্যাকিং', 'Track Application')}
          </Link>
          <Link href="/verify" className="flex items-center gap-1 hover:text-accent transition-colors">
            <ShieldCheck size={13} /> {t('সদস্য যাচাই', 'Verify Member')}
          </Link>
          <button
            type="button"
            data-no-i18n="true"
            onClick={toggleLanguage}
            aria-label="Switch language between Bangla and English"
            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-white/15 hover:bg-white/25 hover:text-accent font-semibold transition-colors"
          >
            <Globe size={12} />
            {language === 'bn' ? 'English' : 'বাংলা'}
          </button>
          <Link href="/portal" className="flex items-center gap-1 bg-white/10 hover:bg-white/20 px-2 py-0.5 rounded text-accent transition-colors">
            <UserCircle size={14} /> {t('মেম্বার পোর্টাল', 'Member Portal')}
          </Link>
        </div>
      </div>

      {/* Layer 3: Main Navigation */}
      <div className="px-4 md:px-6 py-3 flex justify-between items-center gap-3 max-w-7xl mx-auto">
        {/* Institutional Branding */}
        <Link href="/" className="flex items-center gap-2.5 shrink-0">
          <div className="w-9 h-9 bg-primary rounded-lg shadow-md flex items-center justify-center text-accent text-lg font-bold shrink-0">
            ⚡
          </div>
          <div className="flex flex-col" data-no-i18n="true">
            <span className="text-sm sm:text-base font-bold text-primary leading-tight whitespace-nowrap">
              {t('পাওয়ার গ্রিড প্রকৌশলী সমিতি', 'Power Grid Engineers Association')}
            </span>
            <span className="text-[10px] sm:text-[11px] text-secondary font-medium whitespace-nowrap">
              {t('ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)', 'Diploma Engineers Association, PGCB (Diprokous)')}
            </span>
          </div>
        </Link>

        {/* Desktop Menu */}
        <nav className="hidden lg:flex items-center gap-3 xl:gap-4 text-[13px] xl:text-sm font-medium text-primary whitespace-nowrap">
          <Link href="/about" className="hover:text-success transition-colors">{t('আমাদের সম্পর্কে', 'About Us')}</Link>
          <Link href="/leadership" className="hover:text-success transition-colors">{t('নেতৃত্ব', 'Leadership')}</Link>
          <Link href="/members" className="hover:text-success transition-colors">{t('সদস্যবৃন্দ', 'Members')}</Link>
          <Link href="/news" className="hover:text-success transition-colors">{t('সংবাদ', 'News')}</Link>
          <Link href="/notices" className="hover:text-success transition-colors">{t('নোটিশ বোর্ড', 'Notice Board')}</Link>
          <Link href="/circulars" className="hover:text-success transition-colors">{t('সার্কুলার', 'Circulars')}</Link>
          <Link href="/documents" className="hover:text-success transition-colors">{t('ডকুমেন্টস', 'Documents')}</Link>
          <Link href="/events" className="hover:text-success transition-colors">{t('ইভেন্ট', 'Events')}</Link>
          <Link href="/gallery" className="hover:text-success transition-colors">{t('গ্যালারি', 'Gallery')}</Link>
          <Link href="/contact" className="hover:text-success transition-colors">{t('যোগাযোগ', 'Contact')}</Link>
        </nav>

        {/* Desktop CTA */}
        <div className="hidden lg:flex items-center gap-3 shrink-0">
          <Link
            href="/membership/apply"
            className="bg-success text-white px-3.5 py-2 rounded-md text-xs xl:text-sm font-medium hover:bg-emerald-600 transition-colors shadow-sm whitespace-nowrap"
          >
            {t('সদস্য আবেদন', 'Apply for Membership')}
          </Link>
        </div>

        {/* Mobile Actions (Language Switcher + Menu Toggle) */}
        <div className="flex items-center gap-2 lg:hidden">
          <button
            type="button"
            data-no-i18n="true"
            onClick={toggleLanguage}
            aria-label="Switch language"
            className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md border border-border bg-surface text-primary text-xs font-bold hover:bg-border/60 transition-colors"
          >
            <Globe size={13} />
            {language === 'bn' ? 'EN' : 'বাংলা'}
          </button>
          <button
            className="text-primary p-1.5 rounded-md hover:bg-surface transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle navigation menu"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Layer 4: Mobile Drawer Navigation */}
      {isMobileMenuOpen && (
        <div className="lg:hidden w-full bg-surface border-b border-border shadow-lg p-4 flex flex-col gap-3">
          <nav className="flex flex-col gap-2.5 text-sm font-medium text-primary">
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('হোম', 'Home')}</Link>
            <Link href="/about" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('আমাদের সম্পর্কে', 'About Us')}</Link>
            <Link href="/leadership" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('নেতৃত্ব ও কমিটি', 'Leadership & Committee')}</Link>
            <Link href="/members" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('সদস্যবৃন্দ', 'Members')}</Link>
            <Link href="/news" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('সংবাদ ও প্রেস বিজ্ঞপ্তি', 'News & Press Releases')}</Link>
            <Link href="/notices" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('নোটিশ বোর্ড', 'Notice Board')}</Link>
            <Link href="/circulars" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('সার্কুলার', 'Circulars')}</Link>
            <Link href="/documents" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('ডকুমেন্টস ও ফরম', 'Documents & Forms')}</Link>
            <Link href="/events" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('ইভেন্ট', 'Events')}</Link>
            <Link href="/gallery" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('গ্যালারি', 'Gallery')}</Link>
            <Link href="/contact" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">{t('যোগাযোগ', 'Contact')}</Link>
            <Link href="/membership/track" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2 text-blue-600">{t('আবেদন ট্র্যাকিং', 'Track Application')}</Link>
            <Link href="/verify" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2 text-blue-600">{t('সদস্য যাচাইকরণ', 'Verify Member')}</Link>
          </nav>
          <div className="flex flex-col gap-2 pt-2">
            <Link
              href="/membership/apply"
              onClick={() => setIsMobileMenuOpen(false)}
              className="bg-success text-white px-4 py-2.5 rounded-md text-sm font-medium text-center shadow-sm"
            >
              {t('সদস্যপদের আবেদন', 'Apply for Membership')}
            </Link>
            <Link
              href="/portal"
              onClick={() => setIsMobileMenuOpen(false)}
              className="bg-primary text-white px-4 py-2.5 rounded-md text-sm font-medium text-center shadow-sm"
            >
              {t('মেম্বার পোর্টাল লগইন', 'Member Portal Login')}
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

export default Header;
