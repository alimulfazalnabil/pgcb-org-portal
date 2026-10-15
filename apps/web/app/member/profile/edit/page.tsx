'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  User,
  ShieldCheck,
  CreditCard,
  FileText,
  FileCheck,
  Award,
  Bell,
  Settings,
  LogOut,
  Menu,
  X,
  Languages,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  ChevronRight,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  HeartPulse,
  Lock,
  Edit3,
  FileEdit,
  Sparkles,
  Camera,
  Upload,
  Check,
  ArrowLeft,
  Eye,
  EyeOff,
  Layers,
} from 'lucide-react';
import { api } from '@/lib/api';
import { MemberProfile } from '@/lib/api/types';

export default function MemberProfileEditPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [photoSuccess, setPhotoSuccess] = useState<string | null>(null);
  const [lang, setLang] = useState<'bn' | 'en'>('en');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Editable Form State
  const [formData, setFormData] = useState({
    // Personal (editable)
    father_name: '',
    mother_name: '',
    gender: 'Male',
    blood_group: 'B+',
    // Contact (editable)
    email: '',
    phone: '',
    alternate_phone: '',
    current_address: '',
    permanent_address: '',
    district: '',
    // Professional (editable)
    organization: 'Power Grid Company of Bangladesh PLC (PGCB)',
    department: '',
    profession: 'Sub-Assistant Engineer',
    academic_qualification: 'Diploma in Electrical Engineering',
    professional_qualification: '',
    years_of_experience: 8,
    // Emergency Contact
    emergency_contact_name: '',
    emergency_contact_relationship: '',
    emergency_contact_phone: '',
    emergency_contact_address: '',
    // Privacy
    show_phone_in_directory: true,
    directory_visibility: true,
  });

  const isEn = lang === 'en';

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const data: MemberProfile = await api.getProfile();
        setProfile(data);
        if (data.preferred_language === 'bn') {
          setLang('bn');
        }

        const pInfo = data.personal_information || {};
        const profInfo = data.professional_information || {};
        const cInfo = data.contact_information || {};
        const eContact = data.emergency_contact || {};

        setFormData({
          father_name: pInfo.father_name || data.father_name || '',
          mother_name: pInfo.mother_name || data.mother_name || '',
          gender: pInfo.gender || data.gender || 'Male',
          blood_group: pInfo.blood_group || data.blood_group || 'B+',
          email: cInfo.email || data.email || '',
          phone: cInfo.phone || data.phone || '',
          alternate_phone: cInfo.alternate_phone || data.alternate_phone || '',
          current_address: cInfo.current_address || data.current_address || '',
          permanent_address: cInfo.permanent_address || data.permanent_address || '',
          district: cInfo.district || data.district || '',
          organization: profInfo.organization || data.organization || 'Power Grid Company of Bangladesh PLC (PGCB)',
          department: profInfo.department || data.department || '',
          profession: profInfo.profession || data.profession || 'Sub-Assistant Engineer',
          academic_qualification: profInfo.academic_qualification || data.academic_qualification || 'Diploma in Electrical Engineering',
          professional_qualification: profInfo.professional_qualification || data.professional_qualification || '',
          years_of_experience: profInfo.years_of_experience ?? data.years_of_experience ?? 8,
          emergency_contact_name: eContact.name || data.emergency_contact_name || '',
          emergency_contact_relationship: eContact.relationship || data.emergency_contact_relationship || '',
          emergency_contact_phone: eContact.phone || data.emergency_contact_phone || '',
          emergency_contact_address: eContact.address || data.emergency_contact_address || '',
          show_phone_in_directory: data.contact_visibility ?? true,
          directory_visibility: data.directory_visibility ?? true,
        });
      } catch (err: any) {
        if (err?.status === 401) {
          router.push('/login?redirect=/member/profile/edit');
          return;
        }
        setError(err?.message || 'Failed to load member profile');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData((prev) => ({ ...prev, [name]: value === '' ? '' : Number(value) }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handlePhotoSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setPhotoError(null);
    setPhotoSuccess(null);

    // Client-side validations
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setPhotoError(
        isEn
          ? 'Invalid format. Only JPEG, PNG, and WebP images are allowed.'
          : 'ভুল ফরম্যাট। শুধুমাত্র JPEG, PNG, এবং WebP ছবি আপলোড করা যাবে।'
      );
      return;
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setPhotoError(
        isEn
          ? 'File size exceeds 5MB limit. Please choose a smaller image.'
          : 'ছবির আকার ৫ মেগাবাইট অতিক্রম করেছে। ছোট আকারের ছবি নির্বাচন করুন।'
      );
      return;
    }

    try {
      setUploadingPhoto(true);
      const res = await api.uploadProfilePhoto(file);
      if (res?.ok && res?.photo_url) {
        setProfile((prev) => (prev ? { ...prev, photo_url: res.photo_url } : null));
        setPhotoSuccess(isEn ? 'Profile photo updated successfully!' : 'প্রোফাইল ছবি সফলভাবে আপডেট করা হয়েছে!');
      } else {
        throw new Error(res?.detail || 'Failed to update photo');
      }
    } catch (err: any) {
      setPhotoError(err?.message || (isEn ? 'Failed to upload photo.' : 'ছবি আপলোড করতে ব্যর্থ হয়েছে।'));
    } finally {
      setUploadingPhoto(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setSaving(true);

    try {
      const updated = await api.updateProfile(formData);
      setProfile(updated);
      setSuccessMsg(
        isEn
          ? 'Profile updated successfully!'
          : 'প্রোফাইল সফলভাবে সংরক্ষণ করা হয়েছে!'
      );
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err: any) {
      setError(err?.message || (isEn ? 'Failed to update profile.' : 'প্রোফাইল আপডেট করতে সমস্যা হয়েছে।'));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setSaving(false);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="w-12 h-12 border-4 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-slate-400 font-medium text-sm">
            {isEn ? 'Loading edit profile form...' : 'ফরম লোড হচ্ছে...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <Link href="/member/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center font-black text-white text-base shadow-lg shadow-emerald-600/30">
              P
            </div>
            <div className="hidden sm:block">
              <span className="font-extrabold tracking-tight text-white text-sm">PGCB</span>
              <span className="text-emerald-400 font-bold text-xs ml-1.5 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/50">
                MEMBER PORTAL
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center gap-2.5 sm:gap-3">
          <button
            onClick={() => setLang((prev) => (prev === 'en' ? 'bn' : 'en'))}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 hover:border-slate-600 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
          >
            <Languages size={15} />
            <span className="uppercase">{lang}</span>
          </button>

          <Link
            href="/member/profile"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-bold transition-colors"
          >
            <ArrowLeft size={14} />
            <span>{isEn ? 'View Profile' : 'প্রোফাইলে ফিরুন'}</span>
          </Link>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Sidebar */}
        <aside
          className={`lg:w-64 bg-slate-900/60 lg:bg-slate-900/30 border-r border-slate-800/80 p-4 lg:p-6 shrink-0 transition-all duration-300 ${
            mobileMenuOpen ? 'block' : 'hidden lg:block'
          }`}
        >
          <div className="space-y-1">
            <Link
              href="/member/dashboard"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <Layers size={18} />
              <span>{isEn ? 'Dashboard' : 'ড্যাশবোর্ড'}</span>
            </Link>

            <Link
              href="/member/profile"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
            >
              <User size={18} />
              <span>{isEn ? 'My Profile' : 'আমার প্রোফাইল'}</span>
            </Link>

            <Link
              href="/member/profile/edit"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-bold text-sm bg-emerald-600/15 border border-emerald-500/30 text-emerald-300 transition-colors pl-8 text-xs"
            >
              <Edit3 size={15} className="text-emerald-400" />
              <span>{isEn ? 'Edit Profile' : 'তথ্য পরিবর্তন'}</span>
            </Link>

            <Link
              href="/member/profile/change-requests"
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors pl-8 text-xs"
            >
              <FileEdit size={15} />
              <span>{isEn ? 'Change Requests' : 'ভেরিফিকেশন আবেদন'}</span>
            </Link>

            <div className="pt-4 mt-4 border-t border-slate-800/80 space-y-1">
              <Link
                href="/portal?tab=settings"
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <Settings size={18} />
                <span>{isEn ? 'Settings' : 'সেটিংস'}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl font-semibold text-sm text-rose-400 hover:bg-rose-500/10 transition-colors text-left"
              >
                <LogOut size={18} />
                <span>{isEn ? 'Sign Out' : 'লগ আউট'}</span>
              </button>
            </div>
          </div>
        </aside>

        {/* Form Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto w-full space-y-6">
          {/* Breadcrumb & Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-xs text-slate-400 font-medium mb-1">
                <Link href="/member/dashboard" className="hover:text-slate-200">
                  {isEn ? 'Portal' : 'পোর্টাল'}
                </Link>
                <ChevronRight size={13} />
                <Link href="/member/profile" className="hover:text-slate-200">
                  {isEn ? 'Profile' : 'প্রোফাইল'}
                </Link>
                <ChevronRight size={13} />
                <span className="text-emerald-400 font-bold">{isEn ? 'Edit' : 'সম্পাদনা'}</span>
              </div>
              <h1 className="text-2xl font-black text-white tracking-tight">
                {isEn ? 'Edit Member Profile' : 'সদস্য প্রোফাইল সম্পাদনা'}
              </h1>
            </div>

            <Link
              href="/member/profile"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs transition-colors self-start sm:self-auto"
            >
              <ArrowLeft size={14} />
              <span>{isEn ? 'Back to Profile' : 'প্রোফাইলে ফিরুন'}</span>
            </Link>
          </div>

          {/* Feedback alerts */}
          {successMsg && (
            <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 flex items-center gap-3 text-sm">
              <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}
          {error && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-center gap-3 text-sm">
              <AlertCircle size={18} className="text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Banner: Protected Information Notice */}
          <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-slate-900 border border-amber-800/50 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <Lock size={20} className="text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-amber-200">
                  {isEn ? 'Protected Information Policy' : 'সুরক্ষিত তথ্যের নীতিমালা'}
                </h3>
                <p className="text-xs text-amber-300/80 leading-relaxed max-w-2xl">
                  {isEn
                    ? 'Full Name, Date of Birth, NID/Passport, Membership ID, and Grid Circle cannot be edited directly here to prevent unauthorized identity alteration. To modify protected fields, submit an official Profile Change Request.'
                    : 'আইডি কার্ড ও প্রাতিষ্ঠানিক তথ্যের নিরাপত্তার খাতিরে নাম, জন্ম তারিখ, এনআইডি এবং গ্রিড সার্কেল এখান থেকে সরাসরি পরিবর্তনযোগ্য নয়। এ সকল তথ্য পরিবর্তনের জন্য পরিবর্তন আবেদন জমা দিন।'}
                </p>
              </div>
            </div>
            <Link
              href="/member/profile/change-requests"
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shrink-0 transition-colors shadow-md shadow-amber-500/20"
            >
              {isEn ? 'Change Requests' : 'পরিবর্তন আবেদন'}
            </Link>
          </div>

          {/* Section: Profile Photograph Upload */}
          <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2">
                <Camera size={18} className="text-emerald-400" />
                <span>{isEn ? 'Profile Photograph' : 'প্রোফাইল ছবি'}</span>
              </h2>
              <span className="text-[11px] text-slate-400">
                {isEn ? 'Max 5MB (JPG, PNG, WebP)' : 'সর্বোচ্চ ৫ মেগাবাইট (JPG, PNG, WebP)'}
              </span>
            </div>

            {photoSuccess && (
              <div className="p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 size={15} />
                <span>{photoSuccess}</span>
              </div>
            )}
            {photoError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle size={15} />
                <span>{photoError}</span>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center gap-6">
              <div className="w-24 h-24 rounded-2xl bg-slate-800 border-2 border-emerald-500/40 overflow-hidden flex items-center justify-center shrink-0 shadow-lg">
                {profile?.photo_url ? (
                  <img src={profile.photo_url} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <User size={38} className="text-slate-500" />
                )}
              </div>

              <div className="flex-1 space-y-2 text-center sm:text-left">
                <p className="text-xs text-slate-300 font-medium">
                  {isEn
                    ? 'Upload a formal, passport-style photograph for your Digital ID and Member Directory.'
                    : 'ডিজিটাল আইডি কার্ড ও মেম্বার ডিরেক্টরির জন্য আপনার একটি স্পষ্ট পাসপোর্ট সাইজের ছবি আপলোড করুন।'}
                </p>
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-3 pt-1">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handlePhotoSelect}
                    className="hidden"
                    id="profile-photo-upload"
                  />
                  <button
                    type="button"
                    disabled={uploadingPhoto}
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs transition-colors shadow-md shadow-emerald-600/20"
                  >
                    {uploadingPhoto ? (
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <Upload size={14} />
                    )}
                    <span>
                      {uploadingPhoto
                        ? isEn
                          ? 'Validating & Uploading...'
                          : 'আপলোড হচ্ছে...'
                        : isEn
                        ? 'Upload New Photo'
                        : 'নতুন ছবি নির্বাচন করুন'}
                    </span>
                  </button>
                  <span className="text-[11px] text-slate-500">
                    {isEn ? 'Automatic magic bytes & virus scan' : 'স্বয়ংক্রিয় ভাইরাস ও ফরম্যাট স্ক্যান'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 1. Contact Information */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <Phone size={18} className="text-emerald-400" />
                <span>{isEn ? 'Contact Details' : 'যোগাযোগের তথ্য'}</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Official Email Address *' : 'অফিসিয়াল ইমেইল *'}
                  </label>
                  <input
                    type="email"
                    name="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Mobile Phone Number *' : 'মোবাইল নম্বর *'}
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    required
                    value={formData.phone}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Alternate Phone Number' : 'বিকল্প ফোন নম্বর'}
                  </label>
                  <input
                    type="tel"
                    name="alternate_phone"
                    value={formData.alternate_phone}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Home District' : 'নিজ জেলা'}
                  </label>
                  <input
                    type="text"
                    name="district"
                    value={formData.district}
                    onChange={handleChange}
                    placeholder="e.g. Dhaka, Cumilla, Chattogram"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Present / Mailing Address' : 'বর্তমান / যোগাযোগের ঠিকানা'}
                  </label>
                  <textarea
                    name="current_address"
                    rows={2}
                    value={formData.current_address}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Permanent Address' : 'স্থায়ী ঠিকানা'}
                  </label>
                  <textarea
                    name="permanent_address"
                    rows={2}
                    value={formData.permanent_address}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* 2. Professional Details */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <Briefcase size={18} className="text-emerald-400" />
                <span>{isEn ? 'Professional Credentials' : 'পেশাগত তথ্য'}</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Organization' : 'প্রতিষ্ঠান'}
                  </label>
                  <input
                    type="text"
                    name="organization"
                    value={formData.organization}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Department / Unit' : 'দপ্তর / শাখা'}
                  </label>
                  <input
                    type="text"
                    name="department"
                    value={formData.department}
                    onChange={handleChange}
                    placeholder="e.g. Grid Maintenance Division"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Profession / Cadre' : 'পেশা / ক্যাডার'}
                  </label>
                  <input
                    type="text"
                    name="profession"
                    value={formData.profession}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Academic Qualification' : 'শিক্ষাগত যোগ্যতা'}
                  </label>
                  <input
                    type="text"
                    name="academic_qualification"
                    value={formData.academic_qualification}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Professional Qualification / Special Training' : 'পেশাগত প্রশিক্ষণ / সনদ'}
                  </label>
                  <input
                    type="text"
                    name="professional_qualification"
                    value={formData.professional_qualification}
                    onChange={handleChange}
                    placeholder="e.g. High Voltage Protection, SCADA"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Years of Experience' : 'কাজের অভিজ্ঞতা (বছর)'}
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="60"
                    name="years_of_experience"
                    value={formData.years_of_experience}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* 3. Personal Secondary Info */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <User size={18} className="text-emerald-400" />
                <span>{isEn ? 'Personal Details (Non-Protected)' : 'ব্যক্তিগত তথ্য (অননুমোদিত ক্ষেত্রসমূহ)'}</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? "Father's Name" : 'পিতার নাম'}
                  </label>
                  <input
                    type="text"
                    name="father_name"
                    value={formData.father_name}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? "Mother's Name" : 'মাতার নাম'}
                  </label>
                  <input
                    type="text"
                    name="mother_name"
                    value={formData.mother_name}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Gender' : 'লিঙ্গ'}
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  >
                    <option value="Male">{isEn ? 'Male' : 'পুরুষ'}</option>
                    <option value="Female">{isEn ? 'Female' : 'মহিলা'}</option>
                    <option value="Other">{isEn ? 'Other' : 'অন্যান্য'}</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Blood Group' : 'রক্তের গ্রুপ'}
                  </label>
                  <select
                    name="blood_group"
                    value={formData.blood_group}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  >
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>
            </div>

            {/* 4. Emergency Contact */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <HeartPulse size={18} className="text-rose-400" />
                <span>{isEn ? 'Emergency Contact Information' : 'জরুরি যোগাযোগের তথ্য'}</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Contact Person Name' : 'যোগাযোগকারীর নাম'}
                  </label>
                  <input
                    type="text"
                    name="emergency_contact_name"
                    value={formData.emergency_contact_name}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Relationship' : 'সম্পর্ক'}
                  </label>
                  <input
                    type="text"
                    name="emergency_contact_relationship"
                    value={formData.emergency_contact_relationship}
                    onChange={handleChange}
                    placeholder="e.g. Spouse, Brother, Father, Friend"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Emergency Phone Number' : 'জরুরি ফোন নম্বর'}
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact_phone"
                    value={formData.emergency_contact_phone}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-bold mb-1.5">
                    {isEn ? 'Address' : 'ঠিকানা'}
                  </label>
                  <input
                    type="text"
                    name="emergency_contact_address"
                    value={formData.emergency_contact_address}
                    onChange={handleChange}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* 5. Directory & Privacy Preferences */}
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 space-y-4">
              <h2 className="font-extrabold text-base text-white flex items-center gap-2 pb-3 border-b border-slate-800">
                <ShieldCheck size={18} className="text-emerald-400" />
                <span>{isEn ? 'Directory & Privacy Preferences' : 'ডিরেক্টরি ও গোপনীয়তা সেটিংস'}</span>
              </h2>

              <div className="space-y-3 text-xs">
                <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 cursor-pointer hover:bg-slate-800 transition-colors">
                  <input
                    type="checkbox"
                    name="directory_visibility"
                    checked={formData.directory_visibility}
                    onChange={handleChange}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold text-white block">
                      {isEn ? 'Show profile in Member Directory' : 'সদস্য ডিরেক্টরিতে প্রোফাইল প্রদর্শন করুন'}
                    </span>
                    <span className="text-[11px] text-slate-400 block">
                      {isEn
                        ? 'Allow fellow verified PGCB members to discover your designation and grid circle'
                        : 'অন্যান্য যাচাইকৃত পিজিসিবি সদস্যদের আপনার সার্কেল ও পদবি দেখার সুযোগ দিন'}
                    </span>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 cursor-pointer hover:bg-slate-800 transition-colors">
                  <input
                    type="checkbox"
                    name="show_phone_in_directory"
                    checked={formData.show_phone_in_directory}
                    onChange={handleChange}
                    className="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <div>
                    <span className="font-bold text-white block">
                      {isEn ? 'Show mobile phone number to other verified members' : 'সদস্য ডিরেক্টরিতে ফোন নম্বর প্রদর্শন করুন'}
                    </span>
                    <span className="text-[11px] text-slate-400 block">
                      {isEn
                        ? 'If unchecked, your phone number remains strictly private to PGCB administration'
                        : 'চিহ্নিত না থাকলে আপনার ফোন নম্বর কেবল পিজিসিবি প্রশাসনের কাছে সংরক্ষিত থাকবে'}
                    </span>
                  </div>
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-4">
              <Link
                href="/member/profile"
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs text-center transition-colors"
              >
                {isEn ? 'Cancel' : 'বাতিল'}
              </Link>
              <button
                type="submit"
                disabled={saving}
                className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs transition-all shadow-lg shadow-emerald-600/30"
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Check size={16} />
                )}
                <span>
                  {saving
                    ? isEn
                      ? 'Saving Changes...'
                      : 'সংরক্ষণ হচ্ছে...'
                    : isEn
                    ? 'Save Profile Changes'
                    : 'তথ্য সংরক্ষণ করুন'}
                </span>
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}
