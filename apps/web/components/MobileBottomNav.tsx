'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { Home, IdCard, Calendar, Bell, User } from 'lucide-react';
import { useLanguage } from '../lib/i18n';

const NAV_ITEMS = [
  { href: '/', label: 'Home', labelBn: 'হোম', icon: Home },
  { href: '/portal/id-card', label: 'ID Card', labelBn: 'আইডি কার্ড', icon: IdCard },
  { href: '/events', label: 'Events', labelBn: 'ইভেন্ট', icon: Calendar },
  { href: '/notices', label: 'Notices', labelBn: 'নোটিশ', icon: Bell },
  { href: '/portal', label: 'Portal', labelBn: 'পোর্টাল', icon: User },
];

export function MobileBottomNav() {
  const pathname = usePathname();
  const { language } = useLanguage();

  useEffect(() => {
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }, []);

  return (
    <nav
      aria-label="Mobile Bottom Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-background/95 backdrop-blur border-t border-border shadow-lg"
    >
      <div className="grid grid-cols-5 h-16 max-w-md mx-auto px-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === '/'
              ? pathname === '/'
              : pathname === item.href || (item.href !== '/portal' && pathname?.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-1 text-[11px] font-semibold transition-colors ${
                isActive ? 'text-primary' : 'text-secondary hover:text-foreground'
              }`}
            >
              <Icon size={19} className={isActive ? 'text-primary stroke-[2.5]' : ''} />
              <span>{language === 'en' ? item.label : item.labelBn}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export default MobileBottomNav;
