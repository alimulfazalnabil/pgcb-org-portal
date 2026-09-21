'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Phone, Mail, MapPin, Menu, X, UserCircle } from 'lucide-react';

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [language, setLanguage] = useState<'bn' | 'en'>('bn');

  return (
    <header className="w-full border-b border-border bg-background sticky top-0 z-50 shadow-sm">
      
      {/* Layer 1: Announcement Bar */}
      <div className="bg-danger text-white text-xs py-1.5 px-4 text-center font-medium">
        জরুরী নোটিশ: ২০২৩-২০২৪ সালের বার্ষিক সাধারণ সভা আগামী মাসে অনুষ্ঠিত হবে।
      </div>

      {/* Layer 2: Utility & Contact Bar */}
      <div className="hidden md:flex justify-between items-center py-1.5 px-6 bg-primary text-white text-xs">
        <div className="flex items-center space-x-4">
          <span className="flex items-center gap-1.5"><Phone size={12} /> +880 1700-000000</span>
          <span className="flex items-center gap-1.5"><Mail size={12} /> info@pgcb.org.bd</span>
          <span className="flex items-center gap-1.5"><MapPin size={12} /> IDEB Bhaban, Kakrail, Dhaka</span>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => setLanguage(language === 'bn' ? 'en' : 'bn')}
            className="hover:text-accent font-semibold transition-colors"
          >
            {language === 'bn' ? 'English' : 'বাংলা'}
          </button>
          <Link href="/portal" className="flex items-center gap-1 hover:text-accent transition-colors">
            <UserCircle size={14} /> মেম্বার পোর্টাল
          </Link>
        </div>
      </div>

      {/* Layer 3: Main Navigation */}
      <div className="px-4 md:px-6 py-3 flex justify-between items-center max-w-7xl mx-auto">
        
        {/* Branding */}
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded shadow-md flex items-center justify-center">
            <span className="text-accent text-xl font-bold">⚡</span>
          </div>
          <div className="flex flex-col">
            <span className="text-lg md:text-xl font-bold text-primary leading-tight">
              পাওয়ার গ্রিড প্রকৌশলী সমিতি
            </span>
            <span className="text-[10px] md:text-xs text-secondary font-medium">
              Power Grid Engineers Association
            </span>
          </div>
        </Link>

        {/* Desktop Menu */}
        <nav className="hidden lg:flex items-center gap-6 text-sm font-medium text-primary">
          <Link href="/about" className="hover:text-success transition-colors">আমাদের সম্পর্কে</Link>
          <Link href="/committee" className="hover:text-success transition-colors">কমিটি</Link>
          <Link href="/circulars" className="hover:text-success transition-colors">সার্কুলার</Link>
          <Link href="/events" className="hover:text-success transition-colors">ইভেন্ট</Link>
          <Link href="/gallery" className="hover:text-success transition-colors">গ্যালারি</Link>
          <Link href="/contact" className="hover:text-success transition-colors">যোগাযোগ</Link>
        </nav>

        {/* Desktop CTA */}
        <div className="hidden lg:flex items-center gap-3">
          <Link 
            href="/register" 
            className="bg-success text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-emerald-600 transition-colors shadow-sm"
          >
            সদস্য আবেদন
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button 
          className="lg:hidden text-primary p-1"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Layer 4: Mobile Drawer Navigation */}
      {isMobileMenuOpen && (
        <div className="lg:hidden absolute top-full left-0 w-full bg-surface border-b border-border shadow-lg p-4 flex flex-col gap-4">
          <nav className="flex flex-col gap-3 text-sm font-medium text-primary">
            <Link href="/about" className="border-b border-border pb-2">আমাদের সম্পর্কে</Link>
            <Link href="/committee" className="border-b border-border pb-2">কমিটি</Link>
            <Link href="/circulars" className="border-b border-border pb-2">সার্কুলার</Link>
            <Link href="/events" className="border-b border-border pb-2">ইভেন্ট</Link>
          </nav>
          <Link 
            href="/register" 
            className="bg-success text-white px-4 py-2 rounded-md text-sm font-medium text-center shadow-sm"
          >
            সদস্য আবেদন করুন
          </Link>
        </div>
      )}
    </header>
  );
}

export default Header;
