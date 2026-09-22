'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, CircleItem } from '../../../lib/api';
import { LoadingState } from '../../../components/ui/LoadingState';
import { CheckCircle2, AlertCircle, ArrowRight, ArrowLeft, ShieldCheck, User, Briefcase, GraduationCap, FileCheck } from 'lucide-react';

export default function MembershipApplyPage() {
  const [step, setStep] = useState(1);
  const [circles, setCircles] = useState<CircleItem[]>([]);
  const [loadingCircles, setLoadingCircles] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<{ application_no: string; message: string } | null>(null);

  const [formData, setFormData] = useState({
    // Step 1: Personal & Account
    name_bn: '',
    name_en: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    nid_number: '',
    date_of_birth: '',

    // Step 2: Professional & PGCB
    designation_bn: 'উপ-সহকারী প্রকৌশলী',
    employee_id: '',
    circle_id: '',
    membership_type: 'GENERAL',

    // Step 3: Education & Address
    diploma_institution: '',
    graduation_year: '',
    current_address: '',
    permanent_address: '',
  });

  useEffect(() => {
    api.getCircles()
      .then((data) => {
        setCircles(data);
        if (data.length > 0) {
          setFormData((prev) => ({ ...prev, circle_id: data[0].id.toString() }));
        }
      })
      .catch(() => {})
      .finally(() => setLoadingCircles(false));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
  };

  const validateStep = (currentStep: number): boolean => {
    if (currentStep === 1) {
      if (!formData.name_bn.trim()) {
        setError('বাংলায় নাম আবশ্যক');
        return false;
      }
      if (!formData.email.trim() || !formData.email.includes('@')) {
        setError('সঠিক ইমেইল ঠিকানা প্রদান করুন');
        return false;
      }
      if (!formData.phone.trim() || formData.phone.length < 11) {
        setError('সঠিক ১১ ডিজিটের মোবাইল নম্বর দিন');
        return false;
      }
      if (!formData.password || formData.password.length < 8) {
        setError('পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে');
        return false;
      }
      if (formData.password !== formData.confirm_password) {
        setError('পাসওয়ার্ড এবং কনফার্ম পাসওয়ার্ড মিলছে না');
        return false;
      }
    } else if (currentStep === 2) {
      if (!formData.designation_bn.trim()) {
        setError('পদবি নির্বাচন করুন');
        return false;
      }
      if (!formData.circle_id) {
        setError('গ্রিড সার্কেল নির্বাচন করুন');
        return false;
      }
    } else if (currentStep === 3) {
      if (!formData.diploma_institution.trim()) {
        setError('পলিটেকনিক ইনস্টিটিউটের নাম লিখুন');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    setError(null);
    setStep((prev) => prev - 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateStep(3)) return;

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        name_bn: formData.name_bn,
        name_en: formData.name_en || undefined,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        employee_id: formData.employee_id || undefined,
        designation_bn: formData.designation_bn,
        circle_id: formData.circle_id ? Number(formData.circle_id) : undefined,
        diploma_institution: formData.diploma_institution || undefined,
        graduation_year: formData.graduation_year ? Number(formData.graduation_year) : undefined,
        nid_number: formData.nid_number || undefined,
        current_address: formData.current_address || undefined,
        permanent_address: formData.permanent_address || undefined,
        membership_type: formData.membership_type,
      };

      const res = await api.submitApplication(payload);
      setSuccessResult(res);
    } catch (err: any) {
      setError(err.message || 'আবেদন জমা দিতে সমস্যা হয়েছে। আবার চেষ্টা করুন।');
    } finally {
      setSubmitting(false);
    }
  };

  if (successResult) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-16 text-center">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 md:p-12 shadow-md">
          <div className="w-20 h-20 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={48} />
          </div>

          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 mb-3">
            আবেদন সফলভাবে গৃহীত হয়েছে!
          </h2>
          <p className="text-slate-600 text-sm md:text-base mb-8">
            আপনার সদস্যপদ আবেদনটি পিজিসিবি প্রকৌশলী সমিতির সিস্টেমে পর্যালোচনা প্রক্রিয়ার অন্তর্ভুক্ত করা হয়েছে।
          </p>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 mb-8 text-left">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              আপনার অ্যাপ্লিকেশন ট্র্যাকিং নম্বর
            </div>
            <div className="text-2xl md:text-3xl font-mono font-bold text-emerald-800 tracking-wide select-all">
              {successResult.application_no}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              ভবিষ্যতে আবেদনের অগ্রগতি জানতে বা হেল্পডেস্কে যোগাযোগের জন্য এই নম্বরটি সংরক্ষণ করুন।
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href={`/membership/track?app_no=${encodeURIComponent(successResult.application_no)}`}
              className="px-6 py-3 bg-emerald-700 text-white rounded-lg font-semibold hover:bg-emerald-800 transition-colors shadow-sm"
            >
              আবেদনের স্ট্যাটাস দেখুন
            </Link>
            <Link
              href="/portal"
              className="px-6 py-3 bg-white border border-slate-300 text-slate-800 rounded-lg font-semibold hover:bg-slate-50 transition-colors"
            >
              মেম্বার পোর্টাল লগইন
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 min-h-screen">
      <div className="text-center mb-10">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 mb-3">
          অনলাইন মেম্বারশিপ পোর্টাল
        </span>
        <h1 className="text-3xl font-bold text-slate-900 mb-2">সদস্যপদের জন্য অনলাইন আবেদন</h1>
        <p className="text-slate-600 text-sm md:text-base">
          পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ (পিজিসিবি)-এর সম্মানিত প্রকৌশলীদের সমিতির সদস্যভুক্তির আবেদন ফরম।
        </p>
      </div>

      {/* Progress Steps Header */}
      <div className="grid grid-cols-4 gap-2 mb-10 text-xs md:text-sm font-semibold">
        {[
          { num: 1, title: 'ব্যক্তিগত তথ্য', icon: User },
          { num: 2, title: 'পেশাগত তথ্য', icon: Briefcase },
          { num: 3, title: 'শিক্ষা ও ঠিকানা', icon: GraduationCap },
          { num: 4, title: 'পর্যালোচনা', icon: FileCheck },
        ].map((s) => (
          <div
            key={s.num}
            className={`p-3 rounded-lg border text-center transition-all flex flex-col sm:flex-row items-center justify-center gap-2 ${
              step === s.num
                ? 'bg-emerald-800 text-white border-emerald-800 shadow-sm'
                : step > s.num
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-white text-slate-400 border-slate-200'
            }`}
          >
            <s.icon size={16} />
            <span>{s.title}</span>
          </div>
        ))}
      </div>

      {/* Form Container */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 md:p-10 shadow-sm">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-center gap-2">
            <AlertCircle size={18} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Step 1: Personal & Account */}
          {step === 1 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-3">
                ধাপ ১: ব্যক্তিগত ও অ্যাকাউন্ট সংক্রান্ত তথ্য
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পূর্ণ নাম (বাংলায়) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name_bn"
                    value={formData.name_bn}
                    onChange={handleChange}
                    placeholder="যেমন: মোঃ কামরুল হাসান"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Full Name (in English)
                  </label>
                  <input
                    type="text"
                    name="name_en"
                    value={formData.name_en}
                    onChange={handleChange}
                    placeholder="e.g. Md. Kamrul Hasan"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    ইমেইল ঠিকানা (লগইনের জন্য ব্যবহৃত হবে) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="example@pgcb.gov.bd"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    মোবাইল নম্বর <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="০১৭xxxxxxxx"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পাসওয়ার্ড সেট করুন (কমপক্ষে ৮ অক্ষর) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পাসওয়ার্ড নিশ্চিত করুন <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    name="confirm_password"
                    value={formData.confirm_password}
                    onChange={handleChange}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    জাতীয় পরিচয়পত্র নম্বর (NID)
                  </label>
                  <input
                    type="text"
                    name="nid_number"
                    value={formData.nid_number}
                    onChange={handleChange}
                    placeholder="১০ বা ১৭ ডিজিটের এনআইডি"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    জন্ম তারিখ
                  </label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={formData.date_of_birth}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Professional & PGCB */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-3">
                ধাপ ২: পিজিসিবি কর্মক্ষেত্র ও পেশাগত তথ্য
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    বর্তমান পদবি <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="designation_bn"
                    value={formData.designation_bn}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
                  >
                    <option value="উপ-সহকারী প্রকৌশলী">উপ-সহকারী প্রকৌশলী (Sub-Assistant Engineer)</option>
                    <option value="সহকারী প্রকৌশলী">সহকারী প্রকৌশলী (Assistant Engineer)</option>
                    <option value="উপ-বিভাগীয় প্রকৌশলী">উপ-বিভাগীয় প্রকৌশলী (Sub-Divisional Engineer)</option>
                    <option value="নির্বাহী প্রকৌশলী">নির্বাহী প্রকৌশলী (Executive Engineer)</option>
                    <option value="অন্যান্য কারিগরি পদ">অন্যান্য কারিগরি কর্মকর্তা</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পিজিসিবি এমপ্লয়ি আইডি (Employee ID)
                  </label>
                  <input
                    type="text"
                    name="employee_id"
                    value={formData.employee_id}
                    onChange={handleChange}
                    placeholder="যেমন: PGCB-0421"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    গ্রিড সার্কেল ইউনিট <span className="text-red-500">*</span>
                  </label>
                  <select
                    name="circle_id"
                    value={formData.circle_id}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
                  >
                    {circles.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name_bn} ({c.name_en})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    সদস্যপদের ধরন
                  </label>
                  <select
                    name="membership_type"
                    value={formData.membership_type}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 bg-white"
                  >
                    <option value="GENERAL">সাধারণ সদস্য (General Member)</option>
                    <option value="LIFE">আজীবন সদস্য (Life Member)</option>
                    <option value="ASSOCIATE">সহযোগী সদস্য (Associate Member)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Education & Address */}
          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-3">
                ধাপ ৩: শিক্ষাগত যোগ্যতা ও যোগাযোগের ঠিকানা
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পলিটেকনিক ইনস্টিটিউটের নাম <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="diploma_institution"
                    value={formData.diploma_institution}
                    onChange={handleChange}
                    placeholder="যেমন: ঢাকা পলিটেকনিক ইনস্টিটিউট"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    পাসের সন (Graduation Year)
                  </label>
                  <input
                    type="number"
                    name="graduation_year"
                    value={formData.graduation_year}
                    onChange={handleChange}
                    placeholder="যেমন: 2018"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    বর্তমান কর্মস্থল / পোস্টিং সাব-স্টেশনের ঠিকানা
                  </label>
                  <textarea
                    name="current_address"
                    value={formData.current_address}
                    onChange={handleChange}
                    rows={2}
                    placeholder="সাব-স্টেশনের নাম, স্থান ও সার্কেল"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    স্থায়ী ঠিকানা
                  </label>
                  <textarea
                    name="permanent_address"
                    value={formData.permanent_address}
                    onChange={handleChange}
                    rows={2}
                    placeholder="গ্রাম/রোড, ডাকঘর, উপজেলা, জেলা"
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4: Review & Submit */}
          {step === 4 && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-slate-900 border-b border-slate-100 pb-3">
                ধাপ ৪: আবেদনের চূড়ান্ত তথ্য যাচাই
              </h2>

              <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-slate-500 block">নাম (বাংলা):</span>
                    <strong className="text-slate-900">{formData.name_bn}</strong>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">ইমেইল:</span>
                    <strong className="text-slate-900">{formData.email}</strong>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">মোবাইল নম্বর:</span>
                    <strong className="text-slate-900">{formData.phone}</strong>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">পদবি:</span>
                    <strong className="text-slate-900">{formData.designation_bn}</strong>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">গ্রিড সার্কেল:</span>
                    <strong className="text-slate-900">
                      {circles.find((c) => c.id.toString() === formData.circle_id)?.name_bn || 'নির্বাচিত সার্কেল'}
                    </strong>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 block">ইনস্টিটিউট:</span>
                    <strong className="text-slate-900">{formData.diploma_institution}</strong>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-200 text-xs text-slate-500">
                  ঘোষণা: আমি এই মর্মে প্রত্যয়ন করছি যে উপরে প্রদত্ত সমস্ত তথ্যাদি সঠিক ও নির্ভুল। সমিতির গঠনতন্ত্র ও শৃঙ্খলা মেনে চলতে আমি অঙ্গীকারবদ্ধ।
                </div>
              </div>
            </div>
          )}

          {/* Wizard Controls */}
          <div className="mt-8 pt-6 border-t border-slate-100 flex items-center justify-between">
            {step > 1 ? (
              <button
                type="button"
                onClick={handlePrev}
                className="px-5 py-2.5 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition-colors flex items-center gap-1.5 text-sm"
              >
                <ArrowLeft size={16} /> পূর্ববর্তী
              </button>
            ) : (
              <div></div>
            )}

            {step < 4 ? (
              <button
                type="button"
                onClick={handleNext}
                className="px-6 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-semibold transition-colors flex items-center gap-1.5 text-sm shadow-sm"
              >
                পরবর্তী ধাপ <ArrowRight size={16} />
              </button>
            ) : (
              <button
                type="submit"
                disabled={submitting}
                className="px-8 py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg font-bold transition-all flex items-center gap-2 text-sm shadow-md"
              >
                {submitting ? 'আবেদন জমা হচ্ছে...' : 'আবেদনপত্র জমা দিন'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
