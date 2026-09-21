'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import Link from 'next/link';

// 1. Define the Zod Validation Schema
const registrationSchema = z.object({
  fullNameEn: z.string().min(3, 'Full name in English is required'),
  fullNameBn: z.string().min(3, 'Full name in Bangla is required'),
  employeeId: z.string().min(4, 'Valid PGCB Employee ID is required'),
  designation: z.string().min(2, 'Designation is required'),
  email: z.string().email('Valid email address is required'),
  phone: z.string().regex(/^(?:\+88|88)?(01[3-9]\d{8})$/, 'Valid Bangladeshi phone number required'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type RegistrationFormValues = z.infer<typeof registrationSchema>;

export default function RegisterPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegistrationFormValues>({
    resolver: zodResolver(registrationSchema),
  });

  const onSubmit = async (data: RegistrationFormValues) => {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || '/backend/api/v1';
      const response = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setSubmitSuccess(true);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setErrorMessage(errorData.detail || 'নিবন্ধন ব্যর্থ হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।');
        console.error('Registration failed:', errorData);
      }
    } catch (error) {
      setErrorMessage('নেটওয়ার্ক ত্রুটি। অনুগ্রহ করে সার্ভার সংযোগ পরীক্ষা করুন।');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface p-6">
        <div className="max-w-md w-full bg-white dark:bg-primary-dark p-8 rounded-xl shadow-lg text-center border border-border">
          <div className="w-16 h-16 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-4 text-2xl font-bold">✓</div>
          <h2 className="text-2xl font-bold text-primary dark:text-white mb-2">আবেদন সফল হয়েছে</h2>
          <p className="text-secondary mb-6">আপনার আবেদনটি পর্যালোচনার জন্য পাঠানো হয়েছে। অনুগ্রহ করে আপনার ইমেইল যাচাই করুন।</p>
          <Link href="/" className="px-6 py-2 bg-primary text-white rounded-md hover:bg-primary-dark transition-colors inline-block font-medium">
            হোমপেজে ফিরে যান
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-surface py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8 bg-white dark:bg-primary p-8 md:p-10 rounded-2xl shadow-xl border border-border">
        
        <div className="text-center border-b border-border pb-6">
          <h2 className="text-3xl font-extrabold text-primary dark:text-white">সদস্যপদ আবেদন ফরম</h2>
          <p className="mt-2 text-sm text-secondary">Power Grid Engineers Association (PGEA)</p>
        </div>

        {errorMessage && (
          <div className="p-4 rounded-md bg-danger/10 border border-danger text-danger text-sm font-medium">
            {errorMessage}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* English Name */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">Full Name (English) *</label>
              <input
                {...register('fullNameEn')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="e.g. Engr. Md. Rahim"
              />
              {errors.fullNameEn && <p className="text-danger text-xs mt-1">{errors.fullNameEn.message}</p>}
            </div>

            {/* Bangla Name */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">পূর্ণ নাম (বাংলা) *</label>
              <input
                {...register('fullNameBn')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="যেমন: প্রকোং. মোঃ রহিম"
              />
              {errors.fullNameBn && <p className="text-danger text-xs mt-1">{errors.fullNameBn.message}</p>}
            </div>

            {/* Employee ID */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">PGCB Employee ID *</label>
              <input
                {...register('employeeId')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="PGCB-EMP-0000"
              />
              {errors.employeeId && <p className="text-danger text-xs mt-1">{errors.employeeId.message}</p>}
            </div>

            {/* Designation */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">পদবী (Designation) *</label>
              <select
                {...register('designation')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
              >
                <option value="">নির্বাচন করুন...</option>
                <option value="Sub-Assistant Engineer">Sub-Assistant Engineer (SAE)</option>
                <option value="Assistant Engineer">Assistant Engineer (AE)</option>
                <option value="Executive Engineer">Executive Engineer (XEN)</option>
              </select>
              {errors.designation && <p className="text-danger text-xs mt-1">{errors.designation.message}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">অফিসিয়াল ইমেইল *</label>
              <input
                type="email"
                {...register('email')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="name@pgcb.gov.bd"
              />
              {errors.email && <p className="text-danger text-xs mt-1">{errors.email.message}</p>}
            </div>

            {/* Phone */}
            <div>
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">মোবাইল নম্বর *</label>
              <input
                {...register('phone')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="01700000000"
              />
              {errors.phone && <p className="text-danger text-xs mt-1">{errors.phone.message}</p>}
            </div>

            {/* Password */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-primary dark:text-white mb-1">পাসওয়ার্ড সেট করুন *</label>
              <input
                type="password"
                {...register('password')}
                className="w-full px-4 py-2.5 rounded-md border border-border bg-background focus:ring-2 focus:ring-accent outline-none transition-all"
                placeholder="••••••••"
              />
              {errors.password && <p className="text-danger text-xs mt-1">{errors.password.message}</p>}
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-bold text-white bg-success hover:bg-emerald-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-success disabled:opacity-70 transition-colors cursor-pointer"
          >
            {isSubmitting ? 'প্রসেস হচ্ছে...' : 'আবেদন জমা দিন (Submit)'}
          </button>
        </form>
      </div>
    </div>
  );
}
