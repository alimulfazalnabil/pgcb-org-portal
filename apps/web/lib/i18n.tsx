'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';

export type Language = 'bn' | 'en';

interface LanguageContextValue {
  language: Language;
  setLanguage: (lang: Language) => void;
  toggleLanguage: () => void;
  t: (bn: string, en: string) => string;
  pick: (item: Record<string, any> | null | undefined, baseField: string, fallback?: string) => string;
  formatNumber: (value: number | string | null | undefined) => string;
  formatDate: (value: string | null | undefined, options?: Intl.DateTimeFormatOptions) => string;
}

const STORAGE_KEY = 'pgcb_portal_lang';

const BN_DIGITS: Record<string, string> = {
  '০': '0',
  '১': '1',
  '২': '2',
  '৩': '3',
  '৪': '4',
  '৫': '5',
  '৬': '6',
  '৭': '7',
  '৮': '8',
  '৯': '9',
};

export function bengaliDigitsToAscii(input: string): string {
  return input.replace(/[০-৯]/g, (d) => BN_DIGITS[d] ?? d);
}

/**
 * Comprehensive Bangla -> English dictionary for static UI labels, headings,
 * buttons, badges, placeholders, and institutional phrases across all 71 routes.
 */
const BN_TO_EN_EXACT: Record<string, string> = {
  // Brand & Global Navigation
  'মূল কনটেন্টে যান': 'Skip to main content',
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি': 'Power Grid Engineers Association',
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি': 'Power Grid Engineers Association',
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি, বাংলাদেশ': 'Power Grid Engineers Association, Bangladesh',
  'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)': 'Diploma Engineers Association, PGCB (Diprokous)',
  'হোম': 'Home',
  'আমাদের সম্পর্কে': 'About Us',
  'নেতৃত্ব': 'Leadership',
  'নেতৃত্ব ও কমিটি': 'Leadership & Committee',
  'সদস্যবৃন্দ': 'Members',
  'সদস্য ডিরেক্টরি': 'Member Directory',
  'সদস্য প্রকৌশলী ডিরেক্টরি': 'Member Engineer Directory',
  'সংবাদ': 'News',
  'সংবাদ ও প্রেস বিজ্ঞপ্তি': 'News & Press Releases',
  'নোটিশ': 'Notices',
  'নোটিশ বোর্ড': 'Notice Board',
  'অফিসিয়াল নোটিশ বোর্ড': 'Official Notice Board',
  'সার্কুলার': 'Circulars',
  'সার্কুলার ও আদেশ': 'Circulars & Orders',
  'ডকুমেন্টস': 'Documents',
  'ডকুমেন্টস ও ফরম': 'Documents & Forms',
  'ফরম ও প্রকাশনা': 'Forms & Publications',
  'ইভেন্ট': 'Events',
  'ইভেন্ট ও সম্মেলন': 'Events & Conferences',
  'গ্যালারি': 'Gallery',
  'যোগাযোগ': 'Contact',
  'সদস্য আবেদন': 'Apply for Membership',
  'সদস্যপদের আবেদন': 'Apply for Membership',
  'আবেদন ট্র্যাকিং': 'Track Application',
  'আবেদনের অগ্রগতি ট্র্যাকিং': 'Track Application Status',
  'সদস্য যাচাই': 'Verify Member',
  'সদস্য যাচাইকরণ': 'Member Verification',
  'ডিজিটাল সদস্যপদ যাচাই': 'Digital Membership Verification',
  'সদস্য ভেরিফিকেশন': 'Member Verification',
  'মেম্বার পোর্টাল': 'Member Portal',
  'মেম্বার পোর্টাল লগইন': 'Member Portal Login',
  'মেম্বার ড্যাশবোর্ড': 'Member Dashboard',
  'আইডি কার্ড': 'ID Card',
  'পোর্টাল': 'Portal',
  'অ্যাডমিন কনসোল': 'Admin Console',

  // Homepage
  'অফিসিয়াল ডিজিটাল পোর্টাল · PGCB': 'Official Digital Portal · PGCB',
  'জাতীয় বিদ্যুৎ গ্রিড সঞ্চালন খাতের প্রকৌশলীদের পেশাগত মানোন্নয়ন, সাংগঠনিক ঐক্য ও কল্যাণমূলক কর্মকাণ্ডের একমাত্র সার্বজনীন প্ল্যাটফর্ম।':
    'The official institutional platform for professional excellence, organizational unity, and welfare of engineers across the national power grid of Bangladesh.',
  'নিবন্ধিত সক্রিয় সদস্য': 'Active Registered Members',
  'গ্রিড সার্কেল ইউনিট': 'Grid Circle Units',
  'প্রকাশনা ও ডকুমেন্টস': 'Publications & Documents',
  'আসন্ন প্রাতিষ্ঠানিক ইভেন্ট': 'Upcoming Institutional Events',
  'অনলাইনে আবেদন জমা দিন': 'Submit online application',
  'ডাউনলোড করুন': 'Download forms & reports',
  'প্রকৌশলীদের তালিকা': 'Directory of engineers',
  'ডিজিটাল কার্ড': 'Digital ID Card',
  'প্রোফাইল ও কার্ড প্রিন্ট': 'Profile & smart ID print',
  'সাম্প্রতিক নোটিশ ও সার্কুলার': 'Recent Notices & Circulars',
  'সকল নোটিশ': 'All Notices',
  'নোটিশ লোড হচ্ছে...': 'Loading notices...',
  'নোটিশসমূহ লোড হচ্ছে...': 'Loading notices...',
  'কোনো নোটিশ পাওয়া যায়নি': 'No notices found',
  'কোনো নোটিশ পাওয়া যায়নি': 'No notices found',
  'বর্তমানে কোনো নতুন নোটিশ প্রকাশিত হয়নি।': 'No new notices have been published at this time.',
  'তারিখ': 'Date',
  'জরুরী': 'URGENT',
  'অফিসিয়াল সার্কুলার': 'Official Circular',
  'সভাপতির বার্তা': "President's Message",
  'প্রকৌশলী নেতৃত্ব': 'Engineering Leadership',
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর সম্মানিত প্রকৌশলী ও সদস্যদের ঐক্যবদ্ধ প্রচেষ্টায় জাতীয় বিদ্যুৎ সঞ্চালন ব্যবস্থার নিরবচ্ছিন্ন উন্নয়ন নিশ্চিত করতে আমরা অঙ্গীকারবদ্ধ।':
    'We are committed to ensuring the continuous modernization and reliability of the national power transmission grid through the united leadership of PGCB engineers.',
  'সম্পূর্ণ কার্যনির্বাহী কমিটি দেখুন': 'View Full Executive Committee',
  'প্রকৌশলী সহায়তা ও তথ্যকেন্দ্র': 'Engineer Helpdesk & Information Center',
  'সদস্যপদ, পরিচয়পত্র বা যেকোনো তথ্যের জন্য সরাসরি যোগাযোগ করুন।':
    'Contact our secretariat directly for membership, digital ID cards, or official inquiries.',

  // Footer
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের কল্যাণ, পেশাগত উন্নয়ন এবং জাতীয় গ্রিড সঞ্চালন সেবায় নিবেদিত সংগঠন।':
    'Dedicated to the welfare, professional development, and national grid transmission excellence of Power Grid Bangladesh PLC (PGCB) engineers.',
  'দ্রুত লিঙ্ক': 'Quick Links',
  'কেন্দ্রীয় ও সার্কেল কমিটি': 'Central & Circle Committees',
  'সদস্য সেবা ও পোর্টাল': 'Member Services & Portal',
  'যোগাযোগ ও নীতি': 'Contact & Policies',
  'পিজিসিবি প্রধান কার্যালয়, আফতাবনগর, ঢাকা-১২১২': 'PGCB Head Office, Aftabnagar, Dhaka-1212',
  'পিজিসিবি ভবন, আফতাবনগর, ঢাকা-১২১২': 'PGCB Bhaban, Aftabnagar, Dhaka-1212',
  'গোপনীয়তা': 'Privacy Policy',
  'শর্তাবলী': 'Terms of Use',
  'অ্যাক্সেসিবিলিটি': 'Accessibility',
  'সাইট সার্চ': 'Site Search',
  'সরকারি ও প্রাতিষ্ঠানিক ডিজিটাল সেবা পোর্টাল': 'Official Institutional Digital Service Portal',

  // Member Directory & Circles
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর নিবন্ধিত সদস্য প্রকৌশলীদের প্রাতিষ্ঠানিক তালিকা।':
    'Official institutional directory of registered member engineers of Power Grid Bangladesh PLC (PGCB).',
  'সকল গ্রিড সার্কেল': 'All Grid Circles',
  'সক্রিয়': 'ACTIVE',
  'সক্রিয়': 'ACTIVE',
  'জাতীয় গ্রিড সার্কেল ও আঞ্চলিক শাখা কমিটি': 'National Grid Circles & Regional Branch Committees',
  'গ্রিড সার্কেল ও শাখা কমিটি লোড হচ্ছে...': 'Loading grid circles and branch committees...',
  'সকল গ্রিড সার্কেলে ফিরুন': 'Back to All Grid Circles',
  'সার্কেল তথ্য পাওয়া যায়নি': 'Circle Information Not Found',

  // Notices, Circulars, Documents, News
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি ও পিজিসিবি সংক্রান্ত সকল বিজ্ঞপ্তি, প্রেস রিলিজ ও প্রাতিষ্ঠানিক নোটিশ।':
    'All official notices, press releases, and institutional announcements of the PGCB Engineers Association.',
  'সকল ক্যাটাগরি': 'All Categories',
  'সাধারণ': 'General',
  'কল্যাণমূলক': 'Welfare',
  'পরীক্ষা': 'Exam',
  'পিন করা': 'Pinned',
  'সংযুক্তি ডাউনলোড': 'Download Attachment',
  'সকল নোটিশে ফিরে যান': 'Back to All Notices',
  'গ্রিড সার্কুলার ও অফিসিয়াল বিজ্ঞপ্তি': 'Grid Circulars & Official Bulletins',
  'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির অফিস আদেশ, কারিগরি নির্দেশিকা, পেশাগত উন্নয়ন ও বার্ষিক সাধারণ সভা সংক্রান্ত বিজ্ঞপ্তি।':
    'Office orders, technical guidelines, professional development notices, and AGM bulletins of the PGCB Diploma Engineers Association.',
  'সকল সার্কুলার': 'All Circulars',
  'অফিস আদেশ': 'Office Order',
  'সাধারণ সার্কুলার': 'General Circular',
  'প্রশাসনিক বিজ্ঞপ্তি': 'Administrative Notice',
  'কল্যাণমূলক কার্যক্রম': 'Welfare Program',
  'ইভেন্ট ও সম্মেলন': 'Events & Conferences',
  'বিজ্ঞপ্তি তালিকা লোড হচ্ছে...': 'Loading circulars...',
  'সার্কুলার সেবা সাময়িকভাবে অনুপলব্ধ': 'Circulars Service Temporarily Unavailable',
  'অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন অথবা কেন্দ্রীয় সচিবালয়ে যোগাযোগ করুন।':
    'Please try again shortly or contact the Central Secretariat.',
  'কোনো সার্কুলার পাওয়া যায়নি': 'No Circulars Found',
  'ভিন্ন কীওয়ার্ড বা বিভাগ নির্বাচন করে পুনরায় চেষ্টা করুন।':
    'Please try again with a different keyword or category filter.',
  'বিস্তারিত': 'Details',
  'পিডিএফ': 'PDF',
  'প্রিভিউ': 'Preview',
  'প্রাতিষ্ঠানিক ডকুমেন্টস ও ফরম সংগ্রহশালা': 'Institutional Documents & Forms Repository',
  'পিজিসিবি প্রকৌশলী সমিতির সদস্য ফরম, কল্যাণ নীতিমালা, বার্ষিক নিরীক্ষা রিপোর্ট ও অফিশিয়াল প্রকাশনাসমূহ ডাউনলোড করুন।':
    'Download membership forms, welfare policies, annual audit reports, and official publications of the PGCB Engineers Association.',
  'সকল ডকুমেন্টস': 'All Documents',
  'ডকুমেন্টের নাম ও বিবরণ': 'Document Title & Description',
  'ক্যাটাগরি': 'Category',
  'ভার্সন': 'Version',
  'ফাইল সাইজ': 'File Size',
  'ডাউনলোড': 'Download',
  'অ্যাকশন': 'Action',
  'খুঁজুন': 'Search',
  'সকল সংবাদ': 'All News',
  'সাংগঠনিক': 'Organizational',
  'প্রেস বিজ্ঞপ্তি': 'Press Release',
  'সদস্য কল্যাণ': 'Member Welfare',
  'গ্রিড কার্যক্রম': 'Grid Operations',
  'সম্মেলন ও ইভেন্ট': 'Conferences & Events',

  // Events, Journal, Media, Committee
  'কেন্দ্রীয় সম্মেলন, কাউন্সিল ও কারিগরি কর্মশালা': 'Central Conferences, Councils & Technical Workshops',
  'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর বার্ষিক সাধারণ সভা, আঞ্চলিক প্রতিনিধি সম্মেলন ও কারিগরি প্রশিক্ষণ কর্মসূচির ক্যালেন্ডার।':
    'Official calendar of Annual General Meetings, regional council conferences, and technical training workshops of Diprokous (PGCB).',
  'সকল কর্মসূচি': 'All Events',
  'আসন্ন কর্মসূচি': 'Upcoming Events',
  'কারিগরি জার্নাল, গবেষণা ও স্মরণিকা': 'Technical Journal, Research & Souvenirs',
  'গ্রিড কারিগরি জার্নাল ও প্রকাশনা': 'Grid Technical Journal & Publications',
  'সকল প্রকাশনা': 'All Publications',
  'কেন্দ্রীয় কার্যনির্বাহী পরিষদ ও নেতৃত্ব': 'Central Executive Committee & Leadership',
  'মিডিয়া আর্কাইভ, ফটো গ্যালারি ও প্রেস কর্নার': 'Media Archive, Photo Gallery & Press Corner',

  // Auth, Verification & Portal
  'সদস্য/অ্যাডমিন লগইন': 'Member / Admin Login',
  'আপনার নিবন্ধিত অ্যাকাউন্ট দিয়ে প্রবেশ করুন।': 'Sign in with your registered institutional account.',
  'পাসওয়ার্ড ভুলে গেছেন?': 'Forgot Password?',
  'নতুন সদস্য নিবন্ধন': 'New Member Registration',
  'সদস্য পোর্টাল প্রবেশাধিকার': 'Member Portal Access',
  'লগইন করুন': 'Login',
  'সনদপত্রটি খুঁজে পাওয়া যায়নি': 'Certificate Not Found',
  'লোড হচ্ছে...': 'Loading...',
};

const BN_TO_EN_PHRASES: Array<[string, string]> = [
  ['জরুরী নোটিশ:', 'Urgent Notice:'],
  ['বিস্তারিত দেখুন', 'View Details'],
  ['বিস্তারিত পড়ুন', 'Read More'],
  ['মোট সক্রিয় সদস্য:', 'Total Active Members:'],
  ['মোট সক্রিয় সদস্য:', 'Total Active Members:'],
  ['সদস্য আইডি:', 'Membership ID:'],
  ['কর্মকর্তা আইডি:', 'Employee ID:'],
  ['গ্রিড সার্কেল:', 'Grid Circle:'],
  ['পদবি:', 'Designation:'],
  ['স্মারক:', 'Ref:'],
  ['রেফারেন্স:', 'Reference:'],
  ['ক্যাটাগরি:', 'Category:'],
  ['প্রকাশের তারিখ:', 'Published Date:'],
  ['📞 হেল্পলাইন: +৮৮০ ২ ৯৫৫৩৬৬৩', '📞 Helpline: +880 2 9553663'],
  ['✉️ ইমেইল: info@pgcb.gov.bd', '✉️ Email: info@pgcb.gov.bd'],
  ['📍 প্রধান কার্যালয়: পিজিসিবি ভবন, আফতাবনগর, ঢাকা', '📍 Head Office: PGCB Bhaban, Aftabnagar, Dhaka'],
  ['ইমেইল:', 'Email:'],
  ['ফোন:', 'Phone:'],
  ['ঠিকানা:', 'Address:'],
  ['সর্বস্বত্ব সংরক্ষিত।', 'All rights reserved.'],
  ['সচিবালয় নিয়ন্ত্রণ প্যানেল', 'Secretariat Admin Control Panel'],
  ['অননুমোদিত এক্সেস', 'Access Restricted'],
  ['বার পঠিত', 'views'],
  ['জন প্রকৌশলী', 'Engineers'],
  ['জন সদস্য', 'Members'],
  ['জন', ''],
  ['টি', ''],
];

const PLACEHOLDER_BN_TO_EN: Record<string, string> = {
  'নাম, পদবি বা সদস্য আইডি খুঁজুন...': 'Search by name, designation, or member ID...',
  'নোটিশ খুঁজুন...': 'Search notices...',
  'বিষয়, শিরোনাম বা রেফারেন্স নম্বর দিয়ে সার্কুলার অনুসন্ধান করুন...':
    'Search circulars by subject, title, or reference number...',
  'ডকুমেন্ট খুঁজুন...': 'Search documents...',
  'সংবাদ অনুসন্ধান করুন...': 'Search news...',
};

function translateTextContent(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return raw;

  // Exact match
  if (BN_TO_EN_EXACT[trimmed]) {
    return raw.replace(trimmed, BN_TO_EN_EXACT[trimmed]);
  }

  let result = raw;
  for (const [bn, en] of BN_TO_EN_PHRASES) {
    if (result.includes(bn)) {
      result = result.split(bn).join(en);
    }
  }

  // Convert Bengali numerals if any remain
  if (/[০-৯]/.test(result)) {
    result = bengaliDigitsToAscii(result);
  }

  return result;
}

const LanguageContext = createContext<LanguageContextValue>({
  language: 'bn',
  setLanguage: () => {},
  toggleLanguage: () => {},
  t: (bn) => bn,
  pick: (item, baseField, fallback = '') => (item ? item[`${baseField}_bn`] || item[`${baseField}_en`] || fallback : fallback),
  formatNumber: (v) => (v !== undefined && v !== null ? Number(v).toLocaleString('bn-BD') : '০'),
  formatDate: (v, opts) => (v ? new Date(v).toLocaleDateString('bn-BD', opts) : ''),
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('bn');
  const pathname = usePathname();
  const originalTextMapRef = useRef<WeakMap<Node, string>>(new WeakMap());
  const isApplyingRef = useRef(false);

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === 'en' || saved === 'bn') {
        setLanguageState(saved);
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    try {
      window.localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      // ignore storage errors
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = lang;
    }
  }, []);

  const toggleLanguage = useCallback(() => {
    setLanguageState((prev) => {
      const next: Language = prev === 'bn' ? 'en' : 'bn';
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // ignore storage errors
      }
      if (typeof document !== 'undefined') {
        document.documentElement.lang = next;
      }
      return next;
    });
  }, []);

  const t = useCallback(
    (bn: string, en: string) => {
      return language === 'en' ? en : bn;
    },
    [language]
  );

  const pick = useCallback(
    (item: Record<string, any> | null | undefined, baseField: string, fallback = '') => {
      if (!item) return fallback;
      if (language === 'en') {
        return item[`${baseField}_en`] || item[`${baseField}_bn`] || fallback;
      }
      return item[`${baseField}_bn`] || item[`${baseField}_en`] || fallback;
    },
    [language]
  );

  const formatNumber = useCallback(
    (value: number | string | null | undefined) => {
      if (value === undefined || value === null || value === '') {
        return language === 'en' ? '0' : '০';
      }
      const num = Number(value);
      if (Number.isNaN(num)) return String(value);
      return num.toLocaleString(language === 'en' ? 'en-US' : 'bn-BD');
    },
    [language]
  );

  const formatDate = useCallback(
    (value: string | null | undefined, options?: Intl.DateTimeFormatOptions) => {
      if (!value) return '';
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return value;
      return d.toLocaleDateString(language === 'en' ? 'en-US' : 'bn-BD', options);
    },
    [language]
  );

  // Automatic DOM-level bilingual translation for all routes & components
  useEffect(() => {
    if (typeof document === 'undefined') return;
    document.documentElement.lang = language;

    const applyDomTranslation = () => {
      if (isApplyingRef.current) return;
      isApplyingRef.current = true;
      try {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
          acceptNode(node) {
            const parent = node.parentElement;
            if (!parent) return NodeFilter.FILTER_REJECT;
            const tag = parent.tagName;
            if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'TEXTAREA') {
              return NodeFilter.FILTER_REJECT;
            }
            if (parent.closest('[data-no-i18n="true"]')) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          },
        });

        let current: Node | null = walker.nextNode();
        while (current) {
          const text = current.nodeValue || '';
          const map = originalTextMapRef.current;

          if (language === 'en') {
            // Save original Bangla text if it contains Bangla characters
            if (/[\u0980-\u09FF]/.test(text)) {
              map.set(current, text);
            }
            const sourceText = map.get(current) ?? text;
            const translated = translateTextContent(sourceText);
            if (translated !== text) {
              current.nodeValue = translated;
            }
          } else {
            const orig = map.get(current);
            if (orig !== undefined && current.nodeValue !== orig) {
              current.nodeValue = orig;
            }
          }
          current = walker.nextNode();
        }

        // Translate input placeholders
        const inputs = document.querySelectorAll<HTMLInputElement>('input[placeholder]');
        inputs.forEach((inp) => {
          const currentPlaceholder = inp.getAttribute('placeholder') || '';
          if (language === 'en') {
            if (/[\u0980-\u09FF]/.test(currentPlaceholder)) {
              inp.setAttribute('data-orig-placeholder', currentPlaceholder);
            }
            const orig = inp.getAttribute('data-orig-placeholder') || currentPlaceholder;
            const translated = PLACEHOLDER_BN_TO_EN[orig] || translateTextContent(orig);
            if (translated && translated !== currentPlaceholder) {
              inp.setAttribute('placeholder', translated);
            }
          } else {
            const orig = inp.getAttribute('data-orig-placeholder');
            if (orig && currentPlaceholder !== orig) {
              inp.setAttribute('placeholder', orig);
            }
          }
        });
      } finally {
        isApplyingRef.current = false;
      }
    };

    applyDomTranslation();

    const observer = new MutationObserver(() => {
      if (language === 'en') {
        applyDomTranslation();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    return () => observer.disconnect();
  }, [language, pathname]);

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      toggleLanguage,
      t,
      pick,
      formatNumber,
      formatDate,
    }),
    [language, setLanguage, toggleLanguage, t, pick, formatNumber, formatDate]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  return useContext(LanguageContext);
}
