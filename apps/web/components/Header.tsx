'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Phone, Mail, MapPin, Menu, X, UserCircle, AlertCircle, FileSearch, ShieldCheck } from 'lucide-react';
import { api, Notice } from '../lib/api';

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [language, setLanguage] = useState<'bn' | 'en'>('bn');
  const [urgentNotice, setUrgentNotice] = useState<Notice | null>(null);
  const [settings, setSettings] = useState<Record<string, string>>({
    contact_phone: '+880-2-9553663',
    contact_email: 'info@pgcb.gov.bd',
    address_bn: 'পিজিসিবি ভবন, আফতাবনগর, ঢাকা-১২১২',
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
            জরুরী নোটিশ: {urgentNotice.title_bn}
          </span>
          <Link
            href={`/notices/${urgentNotice.id}`}
            className="underline font-semibold ml-2 hover:text-accent transition-colors"
          >
            বিস্তারিত দেখুন &rarr;
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
            <MapPin size={12} /> {settings.address_bn}
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/membership/track" className="flex items-center gap-1 hover:text-accent transition-colors">
            <FileSearch size={13} /> আবেদন ট্র্যাকিং
          </Link>
          <Link href="/verify" className="flex items-center gap-1 hover:text-accent transition-colors">
            <ShieldCheck size={13} /> সদস্য যাচাই
          </Link>
          <button
            onClick={() => setLanguage(language === 'bn' ? 'en' : 'bn')}
            className="hover:text-accent font-semibold transition-colors"
          >
            {language === 'bn' ? 'English' : 'বাংলা'}
          </button>
          <Link href="/portal" className="flex items-center gap-1 bg-white/10 hover:bg-white/20 px-2 py-0.5 rounded text-accent transition-colors">
            <UserCircle size={14} /> মেম্বার পোর্টাল
          </Link>
        </div>
      </div>

      {/* Layer 3: Main Navigation */}
      <div className="px-4 md:px-6 py-3 flex justify-between items-center max-w-7xl mx-auto">
        {/* Institutional Branding */}
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-lg shadow-md flex items-center justify-center text-accent text-xl font-bold">
            ⚡
          </div>
          <div className="flex flex-col">
            <span className="text-base md:text-lg font-bold text-primary leading-tight">
              পাওয়ার গ্রিড প্রকৌশলী সমিতি
            </span>
            <span className="text-[10px] md:text-xs text-secondary font-medium">
              Power Grid Engineers Association
            </span>
          </div>
        </Link>

        {/* Desktop Menu */}
        <nav className="hidden lg:flex items-center gap-5 text-sm font-medium text-primary">
          <Link href="/about" className="hover:text-success transition-colors">আমাদের সম্পর্কে</Link>
          <Link href="/leadership" className="hover:text-success transition-colors">নেতৃত্ব</Link>
          <Link href="/members" className="hover:text-success transition-colors">সদস্যবৃন্দ</Link>
          <Link href="/notices" className="hover:text-success transition-colors">নোটিশ বোর্ড</Link>
          <Link href="/circulars" className="hover:text-success transition-colors">সার্কুলার</Link>
          <Link href="/documents" className="hover:text-success transition-colors">ডকুমেন্টস</Link>
          <Link href="/events" className="hover:text-success transition-colors">ইভেন্ট</Link>
          <Link href="/gallery" className="hover:text-success transition-colors">গ্যালারি</Link>
          <Link href="/contact" className="hover:text-success transition-colors">যোগাযোগ</Link>
        </nav>

        {/* Desktop CTA */}
        <div className="hidden lg:flex items-center gap-3">
          <Link
            href="/membership/apply"
            className="bg-success text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-emerald-600 transition-colors shadow-sm"
          >
            সদস্য আবেদন
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          className="lg:hidden text-primary p-1.5 rounded-md hover:bg-surface transition-colors"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Layer 4: Mobile Drawer Navigation */}
      {isMobileMenuOpen && (
        <div className="lg:hidden w-full bg-surface border-b border-border shadow-lg p-4 flex flex-col gap-3">
          <nav className="flex flex-col gap-2.5 text-sm font-medium text-primary">
            <Link href="/" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">হোম</Link>
            <Link href="/about" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">আমাদের সম্পর্কে</Link>
            <Link href="/leadership" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">নেতৃত্ব ও কমিটি</Link>
            <Link href="/members" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">সদস্যবৃন্দ</Link>
            <Link href="/notices" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">নোটিশ বোর্ড</Link>
            <Link href="/circulars" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">সার্কুলার</Link>
            <Link href="/documents" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">ডকুমেন্টস ও ফরম</Link>
            <Link href="/events" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">ইভেন্ট</Link>
            <Link href="/gallery" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">গ্যালারি</Link>
            <Link href="/contact" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2">যোগাযোগ</Link>
            <Link href="/membership/track" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2 text-blue-600">আবেদন ট্র্যাকিং</Link>
            <Link href="/verify" onClick={() => setIsMobileMenuOpen(false)} className="border-b border-border/60 pb-2 text-blue-600">সদস্য যাচাইকরণ</Link>
          </nav>
          <div className="flex flex-col gap-2 pt-2">
            <Link
              href="/membership/apply"
              onClick={() => setIsMobileMenuOpen(false)}
              className="bg-success text-white px-4 py-2.5 rounded-md text-sm font-medium text-center shadow-sm"
            >
              সদস্যপদের আবেদন
            </Link>
            <Link
              href="/portal"
              onClick={() => setIsMobileMenuOpen(false)}
              className="bg-primary text-white px-4 py-2.5 rounded-md text-sm font-medium text-center shadow-sm"
            >
              মেম্বার পোর্টাল লগইন
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

export default Header;
