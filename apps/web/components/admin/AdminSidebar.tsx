'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  UserCheck,
  Users,
  Calendar,
  CheckSquare,
  Award,
  Bell,
  FileText,
  Bookmark,
  ShieldAlert,
  Settings,
  LogOut,
  ChevronRight,
  ExternalLink,
  CreditCard,
  BookOpen,
  Image as ImageIcon,
  Layers,
  KeyRound,
  BarChart3,
  ClipboardList,
} from 'lucide-react';

interface SidebarProps {
  userRole?: string;
  permissions?: string[];
  unreadCount?: number;
}

export function AdminSidebar({ userRole = 'ADMIN', permissions = [] }: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    {
      title: 'ওভারভিউ (Overview)',
      href: '/admin',
      icon: LayoutDashboard,
      exact: true,
      permission: 'admin.stats',
    },
    {
      title: 'সদস্য আবেদন (Applications)',
      href: '/admin/applications',
      icon: UserCheck,
      permission: 'member.review',
    },
    {
      title: 'সদস্য তালিকা (Members)',
      href: '/admin/members',
      icon: Users,
      permission: 'member.read',
    },
    {
      title: 'ইভেন্ট ও সম্মেলন (Events)',
      href: '/admin/events',
      icon: Calendar,
      permission: 'events.read',
    },
    {
      title: 'ইভেন্ট নিবন্ধন (Registrations)',
      href: '/admin/event-registrations',
      icon: ClipboardList,
      permission: 'events.read',
    },
    {
      title: 'উপস্থিতি ও কিউআর (Attendance)',
      href: '/admin/attendance',
      icon: CheckSquare,
      permission: 'events.write',
    },
    {
      title: 'পেমেন্ট ও হিসাব (Payments)',
      href: '/admin/payments',
      icon: CreditCard,
      permission: 'finance.read',
    },
    {
      title: 'সার্টিফিকেট ডেস্ক (Certificates)',
      href: '/admin/certificates',
      icon: Award,
      permission: 'certificate.write',
    },
    {
      title: 'নোটিশ ও বিজ্ঞপ্তি (Notices)',
      href: '/admin/notices',
      icon: Bell,
      permission: 'notice.read',
    },
    {
      title: 'ডকুমেন্ট লাইব্রেরি (Documents)',
      href: '/admin/documents',
      icon: FileText,
      permission: 'document.read',
    },
    {
      title: 'সার্কুলার ও রেজোলিউশন (Circulars)',
      href: '/admin/circulars',
      icon: Bookmark,
      permission: 'content.read',
    },
    {
      title: 'কারিগরি জার্নাল (Journal)',
      href: '/admin/journal',
      icon: BookOpen,
      permission: 'journal.read',
    },
    {
      title: 'মিডিয়া ও গ্যালারি (Media)',
      href: '/admin/media',
      icon: ImageIcon,
      permission: 'media.read',
    },
    {
      title: 'কমিটি ও সিএমএস (Content)',
      href: '/admin/content',
      icon: Layers,
      permission: 'content.read',
    },
    {
      title: 'ব্যবহারকারী ও অ্যাক্সেস (Users)',
      href: '/admin/users',
      icon: Users,
      permission: 'user.read',
    },
    {
      title: 'রোল ও পারমিশন (RBAC)',
      href: '/admin/roles',
      icon: KeyRound,
      permission: 'admin.stats',
    },
    {
      title: 'রিপোর্ট ও এক্সপোর্ট (Reports)',
      href: '/admin/reports',
      icon: BarChart3,
      permission: 'admin.stats',
    },
    {
      title: 'সিকিউরিটি অডিট (Audit Log)',
      href: '/admin/audit',
      icon: ShieldAlert,
      permission: 'audit.read',
    },
    {
      title: 'সিস্টেম সেটিংস (Settings)',
      href: '/admin/settings',
      icon: Settings,
      permission: 'settings.read',
    },
  ];

  const allowedItems = navItems.filter((item) => {
    if (!item.permission) return true;
    if (permissions.includes('*')) return true;
    return permissions.includes(item.permission);
  });

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col h-screen sticky top-0 select-none">
      {/* Brand Header */}
      <div className="p-5 border-b border-border flex items-center justify-between">
        <Link href="/admin" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-primary flex items-center justify-center text-white font-bold text-lg shadow-sm">
            P
          </div>
          <div>
            <div className="text-sm font-bold text-foreground leading-none">PGCB ADMIN</div>
            <div className="text-[10px] text-secondary font-medium mt-1">সচিবালয় নিয়ন্ত্রণ প্যানেল</div>
          </div>
        </Link>
      </div>

      {/* Role Pill */}
      <div className="px-4 py-2.5 bg-surface/50 border-b border-border flex items-center justify-between text-xs">
        <span className="text-secondary font-medium">রোল:</span>
        <span className="px-2 py-0.5 rounded-md font-bold bg-primary/10 text-primary text-[11px]">
          {userRole}
        </span>
      </div>

      {/* Nav List */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {allowedItems.map((item) => {
          const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-secondary hover:text-foreground hover:bg-surface'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon size={16} />
                <span>{item.title}</span>
              </div>
              {isActive && <ChevronRight size={14} className="opacity-80" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer Controls */}
      <div className="p-3 border-t border-border space-y-1.5 bg-surface/30">
        <Link
          href="/"
          target="_blank"
          className="flex items-center justify-between w-full px-3 py-2 rounded-xl text-xs font-semibold text-secondary hover:text-foreground hover:bg-surface transition-all"
        >
          <span className="flex items-center gap-2">
            <ExternalLink size={14} /> মূল পোর্টাল দেখুন
          </span>
        </Link>
        <button
          onClick={async () => {
            await fetch('/backend/api/v1/auth/logout', { method: 'POST' }).catch(() => {});
            window.location.href = '/login';
          }}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-xl text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-all text-left"
        >
          <LogOut size={14} /> লগআউট করুন
        </button>
      </div>
    </aside>
  );
}
