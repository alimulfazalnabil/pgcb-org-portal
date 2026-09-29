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

  // About Page (/about)
  'পরিচিতি ও রূপরেখা · PGCB Engineers Association': 'About & Institutional Profile · PGCB Engineers Association',
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর প্রকৌশলীদের পেশাগত উৎকর্ষ, সাংগঠনিক ঐক্য ও জাতীয় বিদ্যুৎ সঞ্চালন সেবায় নিবেদিত প্রাতিষ্ঠানিক প্ল্যাটফর্ম।':
    'An institutional platform dedicated to professional excellence, organizational unity, and national power transmission service of Power Grid Bangladesh PLC (PGCB) engineers.',
  'পটভূমি ও প্রাতিষ্ঠানিক ইতিহাস': 'Background & Institutional History',
  'বাংলাদেশ বিদ্যুৎ উন্নয়ন বোর্ড (বিউবো) হতে গ্রিড সঞ্চালন ব্যবস্থা পৃথকীকরণের মাধ্যমে ১৯৯৬ সালে পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি) গঠিত হয়। দেশের প্রত্যন্ত অঞ্চলে উচ্চ ভোল্টেজের ৪০০ কেভি, ২৩০ কেভি ও ১৩২ কেভি বিদ্যুৎ সঞ্চালন লাইন ও সাব-স্টেশন পরিচালনায় ডিপ্লোমা প্রকৌশলীবৃন্দ শুরু থেকেই অগ্রণী ভূমিকা পালন করে আসছেন।':
    'Power Grid Company of Bangladesh (PGCB) was established in 1996 through the unbundling of the national transmission grid from BPDB. Since its inception, Diploma Engineers have played a pioneering role in operating and maintaining 400kV, 230kV, and 132kV transmission lines and grid substations nationwide.',
  'কর্মরত প্রকৌশলীদের পেশাগত অধিকার রক্ষা, কারিগরি সক্ষমতা বৃদ্ধি, প্রশিক্ষণ কর্মসূচি পরিচালনা এবং সদস্য ও তাদের পরিবারের পারস্পরিক কল্যাণ নিশ্চিত করার লক্ষ্য নিয়ে সমিতি গঠিত হয়। বর্তমান ডিজিটাল যুগে সকল সদস্যকে একটি একক নেটওয়ার্কে যুক্ত করতে এই ডিজিটাল পোর্টাল বাস্তবায়িত হয়েছে।':
    'The association was formed to safeguard professional rights, enhance technical capacity, conduct training programs, and ensure mutual welfare for members and their families. This digital portal connects all engineers across Bangladesh into a unified institutional network.',
  'আমাদের লক্ষ্য ও উদ্দেশ্য': 'Our Mission & Vision',
  'জাতীয় গ্রিড ব্যবস্থার আধুনিকায়ন, প্রকৌশলীদের কারিগরি জ্ঞান বিনিময় এবং সর্বোচ্চ পেশাদারিত্বের সাথে স্মার্ট বাংলাদেশ বিনির্মাণে অবদান রাখা।':
    'Modernizing the national power grid, sharing technical knowledge among engineers, and contributing to national development with the highest professionalism.',
  'সদস্য কল্যাণ ও সহযোগিতা': 'Member Welfare & Support',
  'সদস্য প্রকৌশলী ও তাদের পরিবারের চিকিৎসাগত সহায়তা, আকস্মিক দুর্ঘটনাজনিত সহযোগিতা এবং শিক্ষাবৃত্তি প্রদান সংক্রান্ত কার্যক্রম।':
    'Medical assistance, emergency support, and educational scholarship programs for member engineers and their families.',
  'অধিকার ও পেশাগত মর্যাদা': 'Professional Rights & Dignity',
  'ন্যায্য পদোন্নতি, পদমর্যাদা ও চাকরিকালীন সুযোগ-সুবিধা সংরক্ষণ এবং কর্তৃপক্ষের সাথে পারস্পরিক গঠনমূলক আলোচনার মাধ্যমে দাবি পূরণ।':
    'Protecting fair promotion, professional status, and service benefits through constructive institutional engagement with management.',
  'সাংগঠনিক কাঠামো ও বিস্তৃতি': 'Organizational Structure & Network',
  'সমিতির কার্যক্রম কেন্দ্রীয় নির্বাহী কমিটি এবং আঞ্চলিক গ্রিড সার্কেল সমূহের সমন্বয়ে গণতান্ত্রিক নীতিমালার আলোকে পরিচালিত হয়।':
    'The association operates democratically through the Central Executive Committee in coordination with 20 Regional Grid Circles and Branch Committees.',
  'কেন্দ্রীয় পরিষদ': 'Central Council',
  'নির্বাহী নীতিনির্ধারণী ফোরাম': 'Executive policy-making forum',
  'আঞ্চলিক সার্কেল': 'Regional Circles',
  'দেশব্যাপী মাঠপর্যায়ের শাখা': 'Nationwide branch committees',
  'ডিজিটাল সেবা': 'Digital Services',
  'আইডি ভেরিফিকেশন ও ট্র্যাকিং': 'Smart ID verification & tracking',
  'নির্বাহী কমিটি দেখুন': 'View Executive Committee',
  'গঠনতন্ত্র ও নীতিমালা ডাউনলোড': 'Download Constitution & Policies',
  'সদস্যপদ আবেদন করুন': 'Apply for Membership',

  // Leadership & Committee (/leadership, /committee, /committee/message)
  'সাংগঠনিক নেতৃত্ব ও কার্যনির্বাহী কমিটি': 'Organizational Leadership & Executive Committee',
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি (পিজিসিবি)-এর কেন্দ্রীয় কার্যনির্বাহী পরিষদ এবং আঞ্চলিক গ্রিড সার্কেল সমূহের দায়িত্বপ্রাপ্ত কর্মকর্তাবৃন্দ।':
    'Office bearers of the Central Executive Committee and Regional Grid Circle Committees of the PGCB Engineers Association.',
  'কমিটির তথ্য লোড হচ্ছে...': 'Loading committee records...',
  'কেন্দ্রীয় কার্যনির্বাহী কমিটি': 'Central Executive Committee',
  'কোনো তথ্য পাওয়া যায়নি': 'No Information Found',
  'বর্তমানে কেন্দ্রীয় কমিটির তথ্য অন্তর্ভুক্ত করা হচ্ছে।': 'Central Executive Committee records are currently being updated.',
  'গ্রিড সার্কেল উপ-কমিটি': 'Grid Circle Sub-Committees',
  'সার্কেল কমিটির তথ্য লোড হচ্ছে...': 'Loading circle committee...',
  'সার্কেল কমিটির তালিকা প্রস্তুত হচ্ছে': 'Circle Committee Roster in Preparation',
  'এই সার্কেলের নবনির্বাচিত কমিটির তালিকা শীঘ্র হালনাগাদ করা হবে।': 'The newly elected committee roster for this circle will be updated shortly.',

  // Circles (/circles & /circles/[slug])
  'শাখা কমিটি ও আঞ্চলিক গ্রিড সার্কেলসমূহ': 'Branch Committees & Regional Grid Circles',
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি (পিজিসিবি)-এর দেশব্যাপী আঞ্চলিক গ্রিড সার্কেল, জিএমডি ও দপ্তরভিত্তিক ডিপ্রকৌস শাখা কমিটি এবং নিবন্ধিত প্রকৌশলী ডিরেক্টরি।':
    'Nationwide Regional Grid Circles, GMD offices, and Diprokous Branch Committees of Power Grid Bangladesh PLC (PGCB) with registered engineer directories.',
  'সক্রিয় শাখা / সার্কেল': 'Active Branches / Circles',
  'তালিকাভুক্ত প্রকৌশলী': 'Registered Engineers',
  'সম্পূর্ণ সদস্য ডিরেক্টরি দেখুন →': 'View Full Member Directory →',
  'কোনো গ্রিড সার্কেল বা শাখা কমিটি পাওয়া যায়নি': 'No Grid Circle or Branch Committee Found',
  'অনুসন্ধান শব্দ পরিবর্তন করে পুনরায় চেষ্টা করুন।': 'Please try again with a different search term.',
  'সার্কেল প্রোফাইল ও সদস্যবৃন্দ': 'Circle Profile & Members',
  'ডিরেক্টরি ফিল্টার': 'Filter Directory',
  '← সকল গ্রিড সার্কেল ও শাখা কমিটি': '← All Grid Circles & Branch Committees',
  'সার্কেল বা শাখা কমিটি পাওয়া যায়নি': 'Circle or Branch Committee Not Found',
  'সকল সার্কেল তালিকায় ফিরে যান': 'Back to All Circles',
  'সক্রিয় সদস্য': 'Active Members',
  'কমিটি সদস্য': 'Committee Members',
  'প্রক্রিয়াধীন আবেদন': 'Pending Applications',
  'শাখা কার্যনির্বাহী কমিটি': 'Branch Executive Committee',
  'সার্কেল/শাখা কমিটির অনুমোদিত দায়িত্বশীলদের তালিকা': 'Approved office bearers of this Circle / Branch Committee',
  'মেয়াদ ২০২৬–২০২৮': 'Term 2026–2028',
  'এই শাখা কমিটির দায়িত্বশীলদের নামের তালিকা কেন্দ্রীয় অ্যাডমিন প্যানেল থেকে হালনাগাদ প্রক্রিয়াধীন রয়েছে। নিচে এই শাখার তালিকাভুক্ত প্রকৌশলীদের ডিরেক্টরি প্রদর্শিত হচ্ছে।':
    'The executive roster for this branch committee is being updated from the central admin console. Registered engineers of this branch are listed below.',
  'অফিসিয়াল ডিপ্রকৌস ভোটার ও সদস্য তালিকা (২০২৬–২০২৮) অনুযায়ী নিবন্ধিত প্রকৌশলী':
    'Registered engineers according to the official Diprokous Voter & Member Roster (2026–2028)',
  'সকল সদস্য দেখুন →': 'View All Members →',
  'এই সার্কেলে এখনো কোনো সক্রিয় সদস্য তালিকাভুক্ত নেই।': 'No active members are currently listed in this circle.',
  'যাচাই': 'Verify',
  'আঞ্চলিক যোগাযোগ ও দপ্তর': 'Regional Office & Contact',
  'দপ্তর': 'Office',
  'ইমেইল': 'Email',
  'ফোন': 'Phone',
  'এই সার্কেলে সদস্যপদ আবেদন করুন': 'Apply for Membership in This Circle',
  'সার্কেলের সকল সদস্য খুঁজুন': 'Browse All Members in Circle',
  'সাম্প্রতিক নোটিশ': 'Recent Notices',
  'কোনো সাম্প্রতিক নোটিশ নেই।': 'No recent notices.',

  // Member Directory (/members)
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর নিবন্ধিত সদস্য প্রকৌশলীদের প্রাতিষ্ঠানিক তালিকা।':
    'Official institutional directory of registered member engineers of Power Grid Bangladesh PLC (PGCB).',
  'সকল গ্রিড সার্কেল': 'All Grid Circles',
  'সদস্য তালিকা লোড হচ্ছে...': 'Loading member directory...',
  'কোনো সদস্য পাওয়া যায়নি': 'No Members Found',
  'অনুসন্ধানের ফলাফলে কোনো সক্রিয় সদস্য প্রকৌশলী মিলছে না।': 'No active member engineers matched your search criteria.',
  'যাচাইকৃত': 'Verified',
  'ডিজিটাল সার্টিফিকেট যাচাই': 'Verify Digital ID',
  'সক্রিয়': 'ACTIVE',
  'সক্রিয়': 'ACTIVE',

  // Notices, Circulars, Documents, News
  'পাওয়ার গ্রিড প্রকৌশলী সমিতি ও পিজিসিবি সংক্রান্ত সকল বিজ্ঞপ্তি, প্রেস রিলিজ ও প্রাতিষ্ঠানিক নোটিশ।':
    'All official notices, press releases, and institutional announcements of the PGCB Engineers Association.',
  'সকল ক্যাটাগরি': 'All Categories',
  'সাধারণ': 'General',
  'কল্যাণমূলক': 'Welfare',
  'পরীক্ষা': 'Exam',
  'পিন করা': 'Pinned',
  'আপনার নির্বাচিত ক্যাটাগরি বা সার্চ কিওয়ার্ডের সাথে মিল রেখে কোনো নোটিশ নেই।':
    'No notices match your selected category or search keyword.',
  '📎 সংযুক্তি বিদ্যমান': '📎 Attachment available',
  'সংযুক্তি ডাউনলোড': 'Download Attachment',
  'সকল নোটিশে ফিরে যান': 'Back to All Notices',
  'অফিসিয়াল সংযুক্তি / ফাইল': 'Official Attachment / Document',
  'মূল সার্কুলার বা দলিলের কপি ডাউনলোড করুন': 'Download the official circular or document copy',
  'গ্রিড সার্কুলার ও অফিসিয়াল বিজ্ঞপ্তি': 'Grid Circulars & Official Bulletins',
  'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির অফিস আদেশ, কারিগরি নির্দেশিকা, পেশাগত উন্নয়ন ও বার্ষিক সাধারণ সভা সংক্রান্ত বিজ্ঞপ্তি।':
    'Office orders, technical guidelines, professional development notices, and AGM bulletins of the PGCB Diploma Engineers Association.',
  'সকল সার্কুলার': 'All Circulars',
  'অফিস আদেশ': 'Office Order',
  'সাধারণ সার্কুলার': 'General Circular',
  'প্রশাসনিক বিজ্ঞপ্তি': 'Administrative Notice',
  'কল্যাণমূলক কার্যক্রম': 'Welfare Program',
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
  'সকল সার্কুলার ও অফিস আদেশ': 'All Circulars & Office Orders',
  'অফিসিয়াল নথি ডাউনলোড করুন (PDF)': 'Download Official Document (PDF)',
  'আলাদা পিডিএফ সংযুক্তি নেই': 'No separate PDF attachment',
  'প্রাতিষ্ঠানিক ডকুমেন্টস ও ফরম সংগ্রহশালা': 'Institutional Documents & Forms Repository',
  'পিজিসিবি প্রকৌশলী সমিতির সদস্য ফরম, কল্যাণ নীতিমালা, বার্ষিক নিরীক্ষা রিপোর্ট ও অফিশিয়াল প্রকাশনাসমূহ ডাউনলোড করুন।':
    'Download membership forms, welfare policies, annual audit reports, and official publications of the PGCB Engineers Association.',
  'সকল ডকুমেন্টস': 'All Documents',
  'ফরম (Forms)': 'Forms',
  'নীতিমালা (Policies)': 'Policies',
  'বার্ষিক প্রতিবেদন (Reports)': 'Annual Reports',
  'ম্যানুয়াল ও নির্দেশিকা': 'Manuals & Guidelines',
  'অন্যান্য': 'Other',
  'ডকুমেন্ট তালিকা লোড হচ্ছে...': 'Loading documents...',
  'কোনো দলিল পাওয়া যায়নি': 'No Documents Found',
  'বর্তমানে এই ক্যাটাগরিতে কোনো নথি বা ফরম আপলোড করা হয়নি।': 'No documents or forms have been uploaded in this category yet.',
  'ডকুমেন্টের নাম ও বিবরণ': 'Document Title & Description',
  'ক্যাটাগরি': 'Category',
  'ভার্সন': 'Version',
  'ফাইল সাইজ': 'File Size',
  'ডাউনলোড': 'Download',
  'অ্যাকশন': 'Action',
  'খুঁজুন': 'Search',
  'পাওয়ার গ্রিড প্রকৌশলী সমিতির সাম্প্রতিক সাংগঠনিক সংবাদ, প্রেস বিজ্ঞপ্তি ও ঘোষণা।':
    'Recent organizational news, press releases, and official announcements of the PGCB Engineers Association.',
  'সকল সংবাদ': 'All News',
  'সাংগঠনিক': 'Organizational',
  'প্রেস বিজ্ঞপ্তি': 'Press Release',
  'সদস্য কল্যাণ': 'Member Welfare',
  'গ্রিড কার্যক্রম': 'Grid Operations',
  'সম্মেলন ও ইভেন্ট': 'Conferences & Events',
  'প্রধান সংবাদ (Featured News)': 'Featured News',
  'সংবাদ লোড হচ্ছে...': 'Loading news...',
  'কোনো সংবাদ পাওয়া যায়নি': 'No News Found',
  'অনুগ্রহ করে ভিন্ন ক্যাটাগরি বা কীওয়ার্ড দিয়ে অনুসন্ধান করুন।': 'Please try searching with a different category or keyword.',
  'পড়ুন': 'Read',

  // Events, Journal, Media (/events, /journal, /media)
  'কেন্দ্রীয় সম্মেলন, কাউন্সিল ও কারিগরি কর্মশালা': 'Central Conferences, Councils & Technical Workshops',
  'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর বার্ষিক সাধারণ সভা, আঞ্চলিক প্রতিনিধি সম্মেলন ও কারিগরি প্রশিক্ষণ কর্মসূচির ক্যালেন্ডার।':
    'Official calendar of Annual General Meetings, regional council conferences, and technical training workshops of Diprokous (PGCB).',
  'সকল কর্মসূচি': 'All Events',
  'আসন্ন কর্মসূচি': 'Upcoming Events',
  'কোনো নির্ধারিত ইভেন্ট বা সম্মেলন পাওয়া যায়নি': 'No Scheduled Events or Conferences Found',
  'পরবর্তী কর্মসূচির তারিখ ঘোষিত হলে এখানে প্রদর্শিত হবে।': 'Upcoming programs will be listed here once announced.',
  'বিনামূল্যে নিবন্ধন': 'Free Registration',
  'বিস্তারিত তথ্য': 'Event Details',
  'নিবন্ধন করুন →': 'Register →',
  'কারিগরি জার্নাল, গবেষণা ও স্মরণিকা': 'Technical Journal, Research & Souvenirs',
  'উচ্চ ভোল্টেজ পাওয়ার গ্রিড ট্রান্সমিশন, সাবস্টেশন অটোমেশন, নিউমেরিক রিলে প্রোটেকশন এবং গ্রিড স্থিতিশীলতা বিষয়ে পিজিসিবির ডিপ্লোমা প্রকৌশলীদের গবেষণাপত্র ও বার্ষিক প্রকাশনা।':
    'Research papers and annual publications by PGCB Diploma Engineers on high-voltage grid transmission, substation automation, numeric relay protection, and grid stability.',
  'গ্রিড কারিগরি জার্নাল ও প্রকাশনা': 'Grid Technical Journal & Publications',
  'সকল প্রকাশনা': 'All Publications',
  'কারিগরি গবেষণা প্রবন্ধ': 'Technical Research',
  'বিশেষ প্রতিবেদন ও গাইডলাইন': 'Reports & Guidelines',
  'স্মরণিকা ও বার্ষিক প্রকাশনা': 'Souvenirs & Annuals',
  'প্রবন্ধ বা প্রকাশনা খুঁজুন...': 'Search articles or publications...',
  'পূর্ণ প্রবন্ধ পড়ুন →': 'Read Full Article →',
  'পিডিএফ ডাউনলোড': 'Download PDF',
  'মিডিয়া গ্যালারি ও ফটো আর্কাইভ': 'Media Gallery & Photo Archive',
  'ডিপ্লোমা প্রকৌশলী সমিতি, পিজিসিবি (ডিপ্রকৌস)-এর কেন্দ্রীয় সম্মেলন, কারিগরি কর্মশালা, গ্রিড পরিদর্শন এবং সাংগঠনিক কার্যক্রমের আলোকচিত্র ও ভিডিও সংগ্রহ।':
    'Official photo and video archive of Central Conferences, technical workshops, grid inspections, and organizational activities of Diprokous (PGCB).',
  'সকল মিডিয়া': 'All Media',
  'আলোকচিত্র': 'Photos',
  'ভিডিও': 'Videos',
  'কোনো মিডিয়া আইটেম পাওয়া যায়নি': 'No Media Items Found',
  'নতুন আলোকচিত্র বা ভিডিও শীঘ্রই যুক্ত করা হবে।': 'New photos and videos will be added shortly.',
  'বিস্তারিত প্রিভিউ দেখুন': 'View Full Preview',
  'ফটো আর্কাইভ': 'Photo Archive',
  'ভিডিও আর্কাইভ': 'Video Archive',

  // Contact Page (/contact)
  'যোগাযোগ ও দাপ্তরিক সহায়তা কেন্দ্র': 'Contact & Official Support Center',
  'সদস্যপদ নিবন্ধন, ডিজিটাল আইডি কার্ড যাচাইকরণ, বার্ষিক নবায়ন বা সাংগঠনিক যেকোনো বিষয়ে কেন্দ্রীয় দপ্তরের সাথে যোগাযোগ করুন।':
    'Contact the Central Secretariat regarding membership registration, digital ID card verification, annual renewal, or organizational inquiries.',
  'কেন্দ্রীয় দপ্তর': 'Central Secretariat Office',
  'প্রধান কার্যালয়ের ঠিকানা': 'Head Office Address',
  'পিজিসিবি ভবন, এভিনিউ-৩, জহুরুল ইসলাম সিটি, আফতাবনগর, বাড্ডা, ঢাকা-১২১২':
    'PGCB Bhaban, Avenue-3, Jahurul Islam City, Aftabnagar, Badda, Dhaka-1212',
  'অফিসিয়াল ইমেইল': 'Official Email',
  'টেলিফোন ও হেল্পডেস্ক': 'Telephone & Helpdesk',
  'দাপ্তরিক সময়সূচি': 'Office Hours',
  'রবিবার – বৃহস্পতিবার, সকাল ৯:০০ – বিকাল ৫:০০': 'Sunday – Thursday, 9:00 AM – 5:00 PM',
  'জরুরি সদস্যপদ সহায়তা': 'Urgent Membership Support',
  'বার্তা বা অনুসন্ধান পাঠান': 'Send a Message or Inquiry',
  'আপনার বার্তা সরাসরি কেন্দ্রীয় সচিবালয়ের সাপোর্ট টিকেট সিস্টেমে সংরক্ষিত হবে।':
    'Your message will be logged directly in the Central Secretariat support ticket system.',
  'আপনার পূর্ণ নাম *': 'Your Full Name *',
  'ইমেইল ঠিকানা *': 'Email Address *',
  'মোবাইল নম্বর (ঐচ্ছিক)': 'Mobile Number (Optional)',
  'বিষয় *': 'Subject *',
  'বিস্তারিত বার্তা *': 'Detailed Message *',
  'বার্তা জমা দিন': 'Submit Message',
  'বার্তা পাঠানো হচ্ছে...': 'Sending message...',
  'আপনার বার্তা সফলভাবে গৃহীত হয়েছে!': 'Your message has been received!',

  // Membership Apply & Track (/membership/apply, /membership/track)
  'অনলাইন মেম্বারশিপ পোর্টাল': 'Online Membership Portal',
  'সদস্যপদের জন্য অনলাইন আবেদন': 'Online Membership Application',
  'পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর সম্মানিত প্রকৌশলীদের সমিতির সদস্যভুক্তির আবেদন ফরম।':
    'Official membership enrollment application form for engineers of Power Grid Bangladesh PLC (PGCB).',
  'ব্যক্তিগত তথ্য': 'Personal Info',
  'পেশাগত তথ্য': 'Professional Info',
  'শিক্ষা ও ঠিকানা': 'Education & Address',
  'পর্যালোচনা': 'Review & Submit',
  'ধাপ ১: ব্যক্তিগত ও অ্যাকাউন্ট সংক্রান্ত তথ্য': 'Step 1: Personal & Account Information',
  'ধাপ ২: পিজিসিবি কর্মক্ষেত্র ও পেশাগত তথ্য': 'Step 2: PGCB Workplace & Professional Information',
  'ধাপ ৩: শিক্ষাগত যোগ্যতা ও যোগাযোগের ঠিকানা': 'Step 3: Educational Qualification & Contact Address',
  'ধাপ ৪: আবেদনের চূড়ান্ত তথ্য যাচাই': 'Step 4: Final Review of Application Details',
  'জাতীয় পরিচয়পত্র নম্বর (NID)': 'National ID Number (NID)',
  'জন্ম তারিখ': 'Date of Birth',
  'পিজিসিবি এমপ্লয়ি আইডি (Employee ID)': 'PGCB Employee ID',
  'সদস্যপদের ধরন': 'Membership Category',
  'পাসের সন (Graduation Year)': 'Graduation Year',
  'বর্তমান কর্মস্থল / পোস্টিং সাব-স্টেশনের ঠিকানা': 'Current Workplace / Posting Substation Address',
  'স্থায়ী ঠিকানা': 'Permanent Address',
  'পূর্ববর্তী': 'Previous',
  'পরবর্তী ধাপ': 'Next Step',
  'আবেদনপত্র জমা দিন': 'Submit Application',
  'আবেদন জমা হচ্ছে...': 'Submitting application...',
  'অনলাইন ট্র্যাকিং সিস্টেম': 'Online Tracking System',
  'সদস্যপদ আবেদনের অগ্রগতি ট্র্যাকিং': 'Track Membership Application Status',
  'আপনার আবেদনের ট্র্যাকিং নম্বর (যেমন: APP-2026-XXXX) দিয়ে বর্তমান অবস্থা ও অনুমোদনের ধাপসমূহ দেখুন।':
    'Enter your application tracking number (e.g. APP-2026-XXXX) to check current status and approval progress.',
  'স্ট্যাটাস দেখুন': 'Check Status',
  'অনুসন্ধান হচ্ছে...': 'Searching...',
  'অনুমোদনের পর্যায়ক্রমিক অগ্রগতি': 'Approval Progress Timeline',

  // Verification Page (/verify)
  'অফিসিয়াল সদস্য কার্ড ও ডিজিটাল সনদ যাচাই': 'Official Member ID Card & Digital Certificate Verification',
  'পাওয়ার গ্রিড ডিপ্লোমা প্রকৌশলী সমিতির অফিসিয়াল পরিচয়পত্র নম্বর অথবা ডিজিটাল কার্ডের কিউআর কোড টোকেন যাচাই করুন।':
    'Verify an official membership ID number or scan a digital ID card QR cryptographic token.',
  'আইডি যাচাই করুন': 'Verify ID',
  'যাচাই হচ্ছে...': 'Verifying...',
  'ক্রিপ্টোগ্রাফিক HMAC-SHA256 দ্বারা সুরক্ষিত': 'Secured by Cryptographic HMAC-SHA256 Signature',
  'নমুনা আইডি:': 'Sample ID:',
  'যাচাইকরণ ব্যর্থ হয়েছে': 'Verification Failed',

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

  // Auth & Portal
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
  ['তালিকাভুক্ত প্রকৌশলী সদস্যবৃন্দ', 'Registered Member Engineers'],
  ['সদস্য আইডি:', 'Membership ID:'],
  ['কর্মকর্তা আইডি:', 'Employee ID:'],
  ['গ্রিড সার্কেল:', 'Grid Circle:'],
  ['আবেদনকারীর নাম:', 'Applicant Name:'],
  ['আবেদনের তারিখ:', 'Application Date:'],
  ['সদস্য নম্বর:', 'Membership No:'],
  ['ট্র্যাকিং নম্বর:', 'Tracking No:'],
  ['পদবি:', 'Designation:'],
  ['স্মারক:', 'Ref:'],
  ['রেফারেন্স:', 'Reference:'],
  ['ক্যাটাগরি:', 'Category:'],
  ['প্রকাশের তারিখ:', 'Published Date:'],
  ['মেয়াদ:', 'Term:'],
  ['স্থান:', 'Venue:'],
  ['বিভাগ:', 'Category:'],
  ['আইডি:', 'ID:'],
  ['উপ-সহকারী প্রকৌশলী', 'Sub-Assistant Engineer'],
  ['সহকারী প্রকৌশলী', 'Assistant Engineer'],
  ['উপ-বিভাগীয় প্রকৌশলী', 'Sub-Divisional Engineer'],
  ['নির্বাহী প্রকৌশলী', 'Executive Engineer'],
  ['তত্ত্বাবধায়ক প্রকৌশলী', 'Superintending Engineer'],
  ['প্রধান প্রকৌশলী', 'Chief Engineer'],
  ['সভাপতি', 'President'],
  ['সহ-সভাপতি', 'Vice President'],
  ['সাধারণ সম্পাদক', 'General Secretary'],
  ['যুগ্ম সাধারণ সম্পাদক', 'Joint Secretary'],
  ['সাংগঠনিক সম্পাদক', 'Organizing Secretary'],
  ['অর্থ সম্পাদক', 'Finance Secretary'],
  ['দপ্তর সম্পাদক', 'Office Secretary'],
  ['প্রচার ও প্রকাশনা সম্পাদক', 'Publicity & Publication Secretary'],
  ['কার্যনির্বাহী সদস্য', 'Executive Member'],
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
  ['বার', 'times'],
  ['জন প্রকৌশলী', 'Engineers'],
  ['জন সদস্য', 'Members'],
];

const PLACEHOLDER_BN_TO_EN: Record<string, string> = {
  'নাম, পদবি বা সদস্য আইডি খুঁজুন...': 'Search by name, designation, or member ID...',
  'নোটিশ খুঁজুন...': 'Search notices...',
  'বিষয়, শিরোনাম বা রেফারেন্স নম্বর দিয়ে সার্কুলার অনুসন্ধান করুন...':
    'Search circulars by subject, title, or reference number...',
  'ডকুমেন্ট খুঁজুন...': 'Search documents...',
  'সংবাদ অনুসন্ধান করুন...': 'Search news...',
  'সার্কেল বা শাখা কমিটির নাম দিয়ে খুঁজুন (যেমন: ঢাকা, খুলনা, বগুড়া, এনএলডিসি)...':
    'Search by circle or branch committee name (e.g. Dhaka, Khulna, Bogura, NLDC)...',
  'প্রবন্ধ বা প্রকাশনা খুঁজুন...': 'Search articles or publications...',
  'সদস্য আইডি (যেমন: PGD-2026-1001) বা QR টোকেন লিখুন':
    'Enter Member ID (e.g. PGD-2026-1001) or QR Token',
  'আবেদন ট্র্যাকিং নম্বর দিন (যেমন: APP-2026-A1B2C3)...':
    'Enter Application Tracking Number (e.g. APP-2026-A1B2C3)...',
  'যেমন: প্রকৌ. মোঃ সাইফুল ইসলাম': 'e.g. Engr. Md. Saiful Islam',
  'সদস্যপদ / ডিজিটাল আইডি / সাধারণ জিজ্ঞাসা': 'Membership / Digital ID / General Inquiry',
  'আপনার জিজ্ঞাসা বা মতামত বিস্তারিত লিখুন (কমপক্ষে ১০ অক্ষর)...':
    'Write your inquiry or feedback in detail (minimum 10 characters)...',
};

function translateTextContent(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) return raw;

  // 1. Exact dictionary match
  if (BN_TO_EN_EXACT[trimmed]) {
    return raw.replace(trimmed, BN_TO_EN_EXACT[trimmed]);
  }

  let result = raw;

  // 2. Replace numeric counters followed by জন or টি safely (only after digits!)
  result = result.replace(/([০-৯0-9,]+)\s*জন\s*সদস্য/g, '$1 Members');
  result = result.replace(/([০-৯0-9,]+)\s*জন/g, '$1');
  result = result.replace(/([০-৯0-9,]+)\s*টি/g, '$1');

  // 3. Phrase replacements
  for (const [bn, en] of BN_TO_EN_PHRASES) {
    if (result.includes(bn)) {
      result = result.split(bn).join(en);
    }
  }

  // 4. Convert Bengali numerals if any remain
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
            if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') {
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

        // Translate input & textarea placeholders
        const inputs = document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(
          'input[placeholder], textarea[placeholder]'
        );
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
    const rafId = window.requestAnimationFrame(applyDomTranslation);
    const timerId = window.setTimeout(applyDomTranslation, 180);

    const observer = new MutationObserver(() => {
      if (language === 'en') {
        applyDomTranslation();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => {
      window.cancelAnimationFrame(rafId);
      window.clearTimeout(timerId);
      observer.disconnect();
    };
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
