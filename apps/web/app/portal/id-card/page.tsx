'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, DigitalCardDetails } from '@/lib/api';
import {
  IdCard,
  Download,
  QrCode,
  ShieldCheck,
  WifiOff,
  CheckCircle2,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

const OFFLINE_STORAGE_KEY = 'pgcb_offline_digital_card_v2';

export default function DigitalIdCardPage() {
  const [card, setCard] = useState<DigitalCardDetails | null>(null);
  const [side, setSide] = useState<'front' | 'back'>('front');
  const [loading, setLoading] = useState(true);
  const [isOfflineCopy, setIsOfflineCopy] = useState(false);
  const [savedOffline, setSavedOffline] = useState(false);

  async function fetchCard() {
    setLoading(true);
    try {
      const data = await api.getDigitalCardDetails();
      setCard(data);
      setIsOfflineCopy(false);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(data));
      }
    } catch {
      if (typeof window !== 'undefined') {
        const cached = window.localStorage.getItem(OFFLINE_STORAGE_KEY);
        if (cached) {
          try {
            setCard(JSON.parse(cached));
            setIsOfflineCopy(true);
          } catch {}
        }
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCard();
  }, []);

  async function saveForOffline() {
    if (!card || typeof window === 'undefined') return;
    window.localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(card));
    if ('caches' in window) {
      try {
        const cache = await caches.open('pgcb-portal-pwa-v2');
        await Promise.allSettled([
          cache.add(card.card_png_url),
          cache.add(card.card_back_png_url),
        ]);
      } catch {}
    }
    setSavedOffline(true);
    window.setTimeout(() => setSavedOffline(false), 3000);
  }

  if (loading) {
    return (
      <section className="section py-20 min-h-screen bg-background">
        <div className="container max-w-md mx-auto px-4 text-center">
          <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent mb-4" />
          <p className="text-secondary text-sm font-medium">ডিজিটাল পরিচয়পত্র লোড হচ্ছে...</p>
        </div>
      </section>
    );
  }

  if (!card) {
    return (
      <section className="section py-16 min-h-screen bg-background">
        <div className="container max-w-md mx-auto px-4">
          <div className="bg-card border border-border rounded-2xl p-8 text-center shadow-sm">
            <IdCard className="mx-auto text-primary mb-3" size={44} />
            <h1 className="text-xl font-bold text-foreground mb-2">ডিজিটাল সদস্য পরিচয়পত্র</h1>
            <p className="text-xs text-secondary mb-6 leading-relaxed">
              আপনার ডিজিটাল পরিচয়পত্র দেখতে অনুগ্রহ করে লগইন করুন অথবা আপনার সদস্যপদ অনুমোদিত হওয়া পর্যন্ত অপেক্ষা করুন।
            </p>
            <div className="flex flex-col gap-2">
              <Link
                href="/portal"
                className="w-full py-2.5 px-4 rounded-xl bg-primary text-white text-sm font-semibold hover:opacity-90 transition-all"
              >
                মেম্বার ড্যাশবোর্ডে ফিরে যান
              </Link>
              <Link
                href="/login"
                className="w-full py-2.5 px-4 rounded-xl border border-border bg-surface text-foreground text-sm font-semibold"
              >
                লগইন করুন
              </Link>
            </div>
          </div>
        </div>
      </section>
    );
  }

  const statusColor =
    card.status === 'ACTIVE'
      ? 'bg-emerald-500 text-white'
      : card.status === 'EXPIRED'
      ? 'bg-amber-500 text-white'
      : 'bg-rose-600 text-white';

  return (
    <section className="section py-8 min-h-screen bg-background">
      <div className="container max-w-lg mx-auto px-4 space-y-6">
        {/* Top bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/portal"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition-colors"
          >
            <ArrowLeft size={15} /> ড্যাশবোর্ডে ফিরুন
          </Link>
          <button
            onClick={fetchCard}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary"
          >
            <RefreshCw size={13} /> রিফ্রেশ
          </button>
        </div>

        {isOfflineCopy && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-700 text-xs flex items-center gap-2">
            <WifiOff size={15} />
            <span>অফলাইন ক্যাশ থেকে ডিজিটাল পরিচয়পত্র প্রদর্শিত হচ্ছে।</span>
          </div>
        )}

        {savedOffline && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 text-xs flex items-center gap-2">
            <CheckCircle2 size={15} />
            <span>পরিচয়পত্রটি অফলাইন ব্যবহারের জন্য ডিভাইসে সংরক্ষিত হয়েছে।</span>
          </div>
        )}

        {/* Mobile Digital ID Card 2.0 */}
        <div className="rounded-3xl overflow-hidden bg-slate-900 text-white shadow-xl border-2 border-amber-500/50">
          {/* Card Header */}
          <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 px-6 py-5 border-b border-amber-500/30 flex items-center justify-between">
            <div>
              <p className="text-[11px] uppercase tracking-widest text-amber-400 font-bold">
                Power Grid Bangladesh ({card.organization || 'PGCB'})
              </p>
              <h1 className="text-lg font-extrabold text-white mt-0.5">Member Digital ID</h1>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-extrabold tracking-wide ${statusColor}`}>
              {card.status}
            </span>
          </div>

          {/* Card Body */}
          <div className="p-6 space-y-5">
            <div className="space-y-1">
              <div className="text-xl font-bold text-white">{card.name_en || card.name_bn}</div>
              {card.name_bn && card.name_en && (
                <div className="text-sm text-slate-300">{card.name_bn}</div>
              )}
              <div className="text-xs font-medium text-amber-300">
                {card.designation_en || card.designation_bn || 'Engineer'}
              </div>
              <div className="text-xs text-slate-300">
                {card.circle_name_en || card.circle_name_bn || 'Central Grid Circle'}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Membership ID</span>
                <span className="font-mono font-bold text-amber-400 text-sm">{card.membership_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Valid Until</span>
                <span className="font-semibold text-white">
                  {card.expires_at
                    ? new Date(card.expires_at).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })
                    : 'Lifetime'}
                </span>
              </div>
              {card.employee_id && (
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Employee ID</span>
                  <span className="font-mono text-slate-200">{card.employee_id}</span>
                </div>
              )}
              {card.blood_group && (
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Blood Group</span>
                  <span className="font-bold text-rose-400">{card.blood_group}</span>
                </div>
              )}
            </div>

            {/* Rendered Card Image (Front / Back) */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-semibold uppercase">
                  Official High-Res Card ({side === 'front' ? 'Front Side' : 'Back Side'})
                </span>
                <div className="inline-flex rounded-lg bg-slate-800 p-0.5 text-xs">
                  <button
                    type="button"
                    onClick={() => setSide('front')}
                    className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
                      side === 'front' ? 'bg-amber-500 text-slate-950' : 'text-slate-300'
                    }`}
                  >
                    সামনের অংশ
                  </button>
                  <button
                    type="button"
                    onClick={() => setSide('back')}
                    className={`px-2.5 py-1 rounded-md font-semibold transition-colors ${
                      side === 'back' ? 'bg-amber-500 text-slate-950' : 'text-slate-300'
                    }`}
                  >
                    পেছনের অংশ
                  </button>
                </div>
              </div>

              <div className="rounded-2xl overflow-hidden border border-slate-700 bg-slate-950">
                <img
                  src={side === 'front' ? api.getDigitalCardUrl() : api.getDigitalCardBackUrl()}
                  alt={`Digital ID Card ${side}`}
                  className="w-full h-auto block"
                />
              </div>
            </div>

            {/* QR Verification Footer */}
            <div className="pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <QrCode size={18} className="text-amber-400 shrink-0" />
                <div>
                  <div className="font-semibold text-white">QR Verification Ready</div>
                  <div className="text-[11px] text-slate-400 truncate max-w-[210px]">
                    {card.qr_verify_url || card.verify_url}
                  </div>
                </div>
              </div>
              <Link
                href={`/verify?member_id=${encodeURIComponent(card.membership_id)}`}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 text-xs font-bold hover:bg-emerald-500/30 transition-colors shrink-0"
              >
                <ShieldCheck size={14} /> যাচাই <ExternalLink size={11} />
              </Link>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <a
            href={api.getDigitalCardUrl()}
            target="_blank"
            download
            className="inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-primary text-white text-xs font-bold hover:opacity-90 transition-all shadow-sm"
          >
            <Download size={15} /> Download PNG
          </a>
          <a
            href={api.getDigitalCardPdfUrl()}
            target="_blank"
            download
            className="inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl border border-border bg-card text-foreground text-xs font-bold hover:bg-surface transition-all shadow-sm"
          >
            <Download size={15} /> 2-Page PDF
          </a>
          <button
            type="button"
            onClick={saveForOffline}
            className="inline-flex items-center justify-center gap-2 py-3 px-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs font-bold hover:bg-emerald-500/20 transition-all"
          >
            <WifiOff size={15} /> অফলাইনে সংরক্ষণ
          </button>
        </div>
      </div>
    </section>
  );
}
