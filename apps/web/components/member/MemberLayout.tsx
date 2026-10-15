'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Home,
  User,
  ShieldCheck,
  FileText,
  FileCheck,
  CreditCard,
  Award,
  Calendar,
  Sparkles,
  Settings,
  Bell,
  Globe,
  Menu,
  X,
  LogOut,
  ChevronRight,
} from 'lucide-react';
import { api } from '@/lib/api';

interface MemberLayoutProps {
  children: React.ReactNode;
  title?: string;
  lang?: 'en' | 'bn';
  onLangChange?: (lang: 'en' | 'bn') => void;
  activeTab?: string;
}

export function MemberLayout({
  children,
  title,
  lang = 'en',
  onLangChange,
  activeTab,
}: MemberLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [memberName, setMemberName] = useState<string>('Member');
  const [currentLang, setCurrentLang] = useState<'en' | 'bn'>(lang);

  const isEn = currentLang === 'en';

  useEffect(() => {
    setCurrentLang(lang);
  }, [lang]);

  useEffect(() => {
    async function loadQuickData() {
      try {
        const dashboard = await api.getMemberDashboard();
        if (dashboard?.member?.name_en || dashboard?.user?.name_en) {
          setMemberName(dashboard.member?.name_en || dashboard.user?.name_en || 'Member');
        }
        if (typeof dashboard?.unread_notifications_count === 'number') {
          setUnreadCount(dashboard.unread_notifications_count);
        }
      } catch {
        // Silently continue
      }
    }
    loadQuickData();
  }, []);

  const handleToggleLang = () => {
    const next = currentLang === 'en' ? 'bn' : 'en';
    setCurrentLang(next);
    if (onLangChange) {
      onLangChange(next);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      router.push('/login');
    }
  };

  const navItems = [
    {
      label_en: 'Dashboard',
      label_bn: 'ড্যাশবোর্ড',
      href: '/member/dashboard',
      icon: Home,
      exact: true,
    },
    {
      label_en: 'My Profile',
      label_bn: 'আমার প্রোফাইল',
      href: '/member/profile',
      icon: User,
      exact: false,
    },
    {
      label_en: 'Membership',
      label_bn: 'সদস্যপদ',
      href: '/member/membership',
      icon: ShieldCheck,
      exact: false,
    },
    {
      label_en: 'Application',
      label_bn: 'আবেদন ট্র্যাকিং',
      href: '/member/application',
      icon: FileText,
      exact: false,
    },
    {
      label_en: 'Documents',
      label_bn: 'ডকুমেন্টস',
      href: '/member/documents',
      icon: FileCheck,
      exact: false,
    },
    {
      label_en: 'Digital ID',
      label_bn: 'ডিজিটাল আইডি',
      href: '/member/digital-id',
      icon: CreditCard,
      exact: false,
    },
    {
      label_en: 'Certificates',
      label_bn: 'সনদপত্র ওয়ালেট',
      href: '/member/certificates',
      icon: Award,
      exact: false,
    },
    {
      label_en: 'Payments',
      label_bn: 'পেমেন্ট ও রসিদ',
      href: '/member/payments',
      icon: CreditCard,
      exact: false,
    },
    {
      label_en: 'Events',
      label_bn: 'ইভেন্টস',
      href: '/events',
      icon: Calendar,
      exact: false,
    },
    {
      label_en: 'Notifications',
      label_bn: 'বিজ্ঞপ্তি',
      href: '/portal?tab=notifications',
      icon: Bell,
      badge: unreadCount > 0 ? unreadCount : undefined,
      exact: false,
    },
    {
      label_en: 'AI Assistant',
      label_bn: 'এআই সহকারী',
      href: '/portal?tab=ai',
      icon: Sparkles,
      exact: false,
    },
    {
      label_en: 'Settings',
      label_bn: 'সেটিংস',
      href: '/portal?tab=settings',
      icon: Settings,
      exact: false,
    },
  ];

  const isItemActive = (href: string, exact: boolean) => {
    if (activeTab && href.includes(`tab=${activeTab}`)) return true;
    if (exact) return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link href="/member/dashboard" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 font-black text-slate-950 text-lg">
              P
            </div>
            <div>
              <span className="font-extrabold tracking-tight text-white text-base lg:text-lg block leading-none">
                PGCB MEMBER PORTAL
              </span>
              <span className="text-[11px] font-semibold text-emerald-400 block leading-tight mt-0.5">
                {isEn ? 'Power Grid Bangladesh PLC' : 'বাংলাদেশ পাওয়ার গ্রিড সদস্য পোর্টাল'}
              </span>
            </div>
          </Link>
        </div>

        {/* Right Header Controls */}
        <div className="flex items-center gap-2.5 lg:gap-4">
          <Link
            href="/portal?tab=notifications"
            className="relative p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white transition-colors"
            title={isEn ? 'Notifications' : 'বিজ্ঞপ্তি'}
          >
            <Bell size={19} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 px-1.5 py-0.5 min-w-[18px] text-center text-[10px] font-black bg-rose-500 text-white rounded-full border-2 border-slate-900 animate-pulse">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>

          <button
            type="button"
            onClick={handleToggleLang}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-xs font-bold text-slate-200 border border-slate-700/60 transition-colors"
          >
            <Globe size={14} className="text-emerald-400" />
            <span>{isEn ? 'বাংলা' : 'EN'}</span>
          </button>

          <Link
            href="/member/profile"
            className="flex items-center gap-2 py-1.5 px-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20 transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center font-black text-xs">
              {memberName ? memberName.charAt(0).toUpperCase() : 'M'}
            </div>
            <span className="hidden sm:inline text-xs font-bold text-emerald-300 max-w-[120px] truncate">
              {memberName}
            </span>
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex flex-col w-64 border-r border-slate-800/80 bg-slate-900/40 p-4 shrink-0 justify-between">
          <div className="space-y-1">
            {navItems.map((item) => {
              const active = isItemActive(item.href, item.exact);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl font-semibold text-sm transition-colors ${
                    active
                      ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20 font-bold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={18} className={active ? 'text-white' : 'text-slate-400'} />
                    <span>{isEn ? item.label_en : item.label_bn}</span>
                  </div>
                  {item.badge ? (
                    <span className="px-1.5 py-0.5 text-[10px] font-black bg-rose-500 text-white rounded-full">
                      {item.badge}
                    </span>
                  ) : null}
                </Link>
              );
            })}
          </div>

          <div className="pt-4 border-t border-slate-800/80">
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
            >
              <LogOut size={18} />
              <span>{isEn ? 'Log Out' : 'লগআউট'}</span>
            </button>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            <div
              className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="relative w-72 bg-slate-900 border-r border-slate-800 p-4 flex flex-col justify-between z-10">
              <div className="space-y-1">
                <div className="flex items-center justify-between pb-3 mb-2 border-b border-slate-800">
                  <span className="font-bold text-emerald-400 text-sm">
                    {isEn ? 'Menu' : 'মেনু'}
                  </span>
                  <button
                    type="button"
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white"
                  >
                    <X size={18} />
                  </button>
                </div>
                {navItems.map((item) => {
                  const active = isItemActive(item.href, item.exact);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-xl font-semibold text-sm transition-colors ${
                        active
                          ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20 font-bold'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon size={18} className={active ? 'text-white' : 'text-slate-400'} />
                        <span>{isEn ? item.label_en : item.label_bn}</span>
                      </div>
                      {item.badge ? (
                        <span className="px-1.5 py-0.5 text-[10px] font-black bg-rose-500 text-white rounded-full">
                          {item.badge}
                        </span>
                      ) : null}
                    </Link>
                  );
                })}
              </div>

              <div className="pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors"
                >
                  <LogOut size={18} />
                  <span>{isEn ? 'Log Out' : 'লগআউট'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Content Area */}
        <main className="flex-1 p-4 lg:p-8 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
}
