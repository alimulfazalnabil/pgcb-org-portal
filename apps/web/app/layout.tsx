import type { Metadata } from 'next';
import '@/styles/globals.css';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { HelpdeskWidget } from '@/components/HelpdeskWidget';
import { MobileBottomNav } from '@/components/MobileBottomNav';
import { LanguageProvider } from '@/lib/i18n';

export const metadata: Metadata = {
  title: 'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশল সমিতি',
  description: 'বাংলাদেশব্যাপী ডিপ্লোমা প্রকৌশলীদের জন্য আধুনিক সাংগঠনিক ওয়েবসাইট, সদস্য পোর্টাল ও যাচাইকরণ ব্যবস্থা.',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://example.org'),
  manifest: '/manifest.webmanifest',
  openGraph: {
    title: 'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশল সমিতি',
    description: 'Institutional website, member portal and verification platform',
    type: 'website',
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn">
      <body className="pb-16 md:pb-0">
        <LanguageProvider>
          <a className="skip-link" href="#main-content">মূল কনটেন্টে যান</a>
          <Header />
          <main id="main-content">{children}</main>
          <Footer />
          <HelpdeskWidget />
          <MobileBottomNav />
        </LanguageProvider>
      </body>
    </html>
  );
}
