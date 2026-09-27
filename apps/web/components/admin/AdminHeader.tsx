'use client';

import React from 'react';
import Link from 'next/link';
import { Bell, ShieldCheck, User } from 'lucide-react';

interface AdminHeaderProps {
  title: string;
  subtitle?: string;
  userName?: string;
  userRole?: string;
  children?: React.ReactNode;
}

export function AdminHeader({
  title,
  subtitle,
  userName = 'অ্যাডমিনিস্ট্রেটর',
  userRole = 'SUPER_ADMIN',
  children,
}: AdminHeaderProps) {
  return (
    <header className="h-16 px-6 border-b border-border bg-card/60 backdrop-blur-md flex items-center justify-between sticky top-0 z-30">
      <div>
        <h1 className="text-base font-bold text-foreground leading-tight">{title}</h1>
        {subtitle && <p className="text-xs text-secondary mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {children}

        {/* User Pill */}
        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
            <User size={16} />
          </div>
          <div className="hidden sm:block text-right">
            <div className="text-xs font-bold text-foreground leading-none">{userName}</div>
            <div className="text-[10px] text-secondary font-medium mt-0.5">{userRole}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
