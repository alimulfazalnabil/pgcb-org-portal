'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { Shield, KeyRound, Smartphone, LogOut, ArrowLeft, CheckCircle2, AlertCircle } from 'lucide-react';

export default function SecurityPage() {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionBusy, setSessionBusy] = useState(false);

  // Password state
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState('');
  const [pwdError, setPwdError] = useState('');

  async function loadSessions() {
    try {
      const data = await api.getSessions();
      setSessions(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.error('Failed to load sessions', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSessions();
  }, []);

  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setPwdSuccess('');
    setPwdError('');

    if (newPassword.length < 8) {
      setPwdError('নতুন পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে।');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwdError('নতুন পাসওয়ার্ড ও নিশ্চিতকরণ পাসওয়ার্ড মেলেনি।');
      return;
    }

    setPwdLoading(true);
    try {
      const res = await api.changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      setPwdSuccess(res.message || 'পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে।');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPwdError(err.message || 'পাসওয়ার্ড পরিবর্তনে ব্যর্থ হয়েছে। বর্তমান পাসওয়ার্ড সঠিক কিনা পরীক্ষা করুন।');
    } finally {
      setPwdLoading(false);
    }
  }

  async function revoke(id: number) {
    setSessionBusy(true);
    try {
      await api.revokeSession(id);
      await loadSessions();
    } catch (err: any) {
      alert(err.message || 'সেশন বাতিল করা যায়নি।');
    } finally {
      setSessionBusy(false);
    }
  }

  async function handleLogoutAll() {
    if (!confirm('আপনি কি নিশ্চিত যে সমস্ত সক্রিয় ডিভাইস ও সেশন থেকে লগআউট করতে চান?')) return;
    setSessionBusy(true);
    try {
      await api.logoutAll();
      window.location.href = '/login';
    } catch (err: any) {
      alert(err.message || 'সব সেশন বন্ধ করা যায়নি।');
      setSessionBusy(false);
    }
  }

  return (
    <section className="section py-10 bg-background min-h-screen">
      <div className="container max-w-4xl mx-auto px-4">
        {/* Breadcrumb & Navigation */}
        <div className="mb-6">
          <Link
            href="/portal"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-secondary hover:text-primary transition-colors"
          >
            <ArrowLeft size={16} /> সদস্য পোর্টাল-এ ফিরে যান
          </Link>
        </div>

        {/* Section Head */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary mb-2">
            <Shield size={14} /> ACCOUNT SECURITY & SESSIONS
          </div>
          <h1 className="text-3xl font-extrabold text-foreground">অ্যাকাউন্ট নিরাপত্তা ও সেশন নিয়ন্ত্রণ</h1>
          <p className="text-secondary mt-1">
            আপনার পাসওয়ার্ড হালনাগাদ করুন এবং সক্রিয় ডিভাইস ও লগইন সেশন পরিচালনা করুন।
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Password Change Form */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4 pb-3 border-b border-border">
                <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                  <KeyRound size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-foreground">পাসওয়ার্ড পরিবর্তন</h2>
                  <p className="text-xs text-secondary">নিয়মিত পাসওয়ার্ড পরিবর্তন অ্যাকাউন্ট সুরক্ষিত রাখে</p>
                </div>
              </div>

              {pwdSuccess && (
                <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-sm flex items-start gap-2">
                  <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
                  <span>{pwdSuccess}</span>
                </div>
              )}

              {pwdError && (
                <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-sm flex items-start gap-2">
                  <AlertCircle size={18} className="shrink-0 mt-0.5" />
                  <span>{pwdError}</span>
                </div>
              )}

              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">
                    বর্তমান পাসওয়ার্ড <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    value={oldPassword}
                    onChange={(e) => setOldPassword(e.target.value)}
                    placeholder="বর্তমান পাসওয়ার্ড লিখুন"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">
                    নতুন পাসওয়ার্ড (কমপক্ষে ৮ অক্ষর) <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="নতুন শক্তিশালী পাসওয়ার্ড দিন"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-foreground mb-1">
                    নতুন পাসওয়ার্ড নিশ্চিত করুন <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="নতুন পাসওয়ার্ডটি পুনরায় লিখুন"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  />
                </div>

                <button
                  type="submit"
                  disabled={pwdLoading}
                  className="w-full mt-2 py-2.5 px-4 rounded-xl bg-primary text-white font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all shadow-sm"
                >
                  {pwdLoading ? 'সংরক্ষণ হচ্ছে...' : 'পাসওয়ার্ড হালনাগাদ করুন'}
                </button>
              </form>
            </div>

            <p className="text-xs text-secondary mt-6 pt-4 border-t border-border">
              পাসওয়ার্ড পরিবর্তনের পর আপনার নিবন্ধিত ইমেইলে একটি নিশ্চিতকরণ ও সুরক্ষা সতর্কবার্তা পাঠানো হবে।
            </p>
          </div>

          {/* Sessions Control */}
          <div className="bg-card border border-border rounded-2xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
                    <Smartphone size={20} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-foreground">সক্রিয় সেশন তালিকা</h2>
                    <p className="text-xs text-secondary">আপনার লগইন ডিভাইসসমূহ</p>
                  </div>
                </div>

                {sessions.some((s) => !s.revoked) && (
                  <button
                    onClick={handleLogoutAll}
                    disabled={sessionBusy}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-500/10 text-rose-600 hover:bg-rose-500/20 transition-colors"
                  >
                    <LogOut size={13} /> সব লগআউট
                  </button>
                )}
              </div>

              {loading ? (
                <div className="py-8 text-center text-sm text-secondary">সেশন লোড হচ্ছে...</div>
              ) : sessions.length === 0 ? (
                <div className="py-8 text-center text-sm text-secondary">কোনো সক্রিয় সেশন পাওয়া যায়নি।</div>
              ) : (
                <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
                  {sessions.map((s) => (
                    <div
                      key={s.id}
                      className={`p-3.5 rounded-xl border text-xs transition-all ${
                        s.revoked
                          ? 'border-border/50 bg-surface/30 opacity-60'
                          : 'border-border bg-surface'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <strong className="text-foreground font-semibold flex items-center gap-2">
                          Session #{s.id}
                          {s.revoked ? (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-600">
                              Revoked
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600">
                              Active
                            </span>
                          )}
                        </strong>

                        {!s.revoked && (
                          <button
                            onClick={() => revoke(s.id)}
                            disabled={sessionBusy}
                            className="px-2.5 py-1 rounded-md text-[11px] font-medium border border-border bg-background hover:bg-rose-500/10 hover:text-rose-600 transition-colors"
                          >
                            বাতিল করুন
                          </button>
                        )}
                      </div>

                      <div className="text-secondary space-y-0.5 font-mono text-[11px]">
                        <div>শুরু: {new Date(s.created_at).toLocaleString('en-GB')}</div>
                        {s.last_seen_at && (
                          <div>শেষ সক্রিয়: {new Date(s.last_seen_at).toLocaleString('en-GB')}</div>
                        )}
                        <div>মেয়াদ: {new Date(s.expires_at).toLocaleString('en-GB')}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs text-secondary">
              <span>অচেনা ডিভাইস সন্দেহ হলে দ্রুত সব সেশন লগআউট করুন।</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
