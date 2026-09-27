'use client';

import React, { useEffect, useState } from 'react';
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { api, ApiError } from '@/lib/api';
import { ShieldAlert, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function AdminRootLayout({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<any>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function checkAdminAuth() {
      try {
        const userData = await api.getMe();
        if (userData.role === 'MEMBER') {
          setError('আপনার অ্যাকাউন্টের জন্য প্রশাসনিক এক্সেস অনুমোদিত নয় (Access Restricted to Staff).');
          setLoading(false);
          return;
        }
        setMe(userData);
        const permsData = await api.getAdminPermissions().catch(() => ({ permissions: ['*'] }));
        setPermissions(permsData.permissions || []);
      } catch (err: any) {
        if (err.status === 401) {
          window.location.href = '/login?next=/admin';
          return;
        }
        setError(err.message || 'অ্যাডমিন সেশন যাচাই করতে ব্যর্থ হয়েছে।');
      } finally {
        setLoading(false);
      }
    }

    checkAdminAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="animate-spin text-primary mb-3" size={32} />
        <p className="text-xs text-secondary font-medium">প্রশাসনিক সেশন যাচাই হচ্ছে...</p>
      </div>
    );
  }

  if (error || !me) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-6">
        <div className="bg-card border border-border p-8 rounded-2xl max-w-md w-full text-center shadow-xl space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
            <ShieldAlert size={28} />
          </div>
          <h2 className="text-lg font-bold text-foreground">অননুমোদিত এক্সেস (Unauthorized)</h2>
          <p className="text-xs text-secondary">{error || 'অনুগ্রহ করে অ্যাডমিন অ্যাকাউন্টে লগইন করুন।'}</p>
          <div className="pt-2">
            <Link
              href="/login"
              className="inline-flex items-center justify-center w-full py-2.5 px-4 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all shadow-sm"
            >
              লগইন পেজে যান
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Persistent Modular Sidebar */}
      <AdminSidebar userRole={me.role} permissions={permissions} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
