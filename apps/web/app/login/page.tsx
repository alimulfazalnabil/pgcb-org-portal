'use client';
import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '../../lib/api';

export default function LoginPage(){
  const [email,setEmail]=useState(''); const [password,setPassword]=useState(''); const [code,setCode]=useState('');
  const [mfa,setMfa]=useState(false); const [busy,setBusy]=useState(false); const [error,setError]=useState('');
  async function submit(e:FormEvent){
    e.preventDefault(); setBusy(true); setError('');
    try{
      const body = await api.login({
        email,
        password,
        mfa_code: mfa ? code : undefined,
      });
      if(body.mfa_required){setMfa(true); return;}
      window.location.href = body.role === 'MEMBER' ? '/portal' : '/admin';
    }catch(err:any){
      if (err.status === 404) {
        setError('ব্যাকএন্ড সার্ভার রেসপন্স করছে না (Backend API 404). Render-এ ব্যাকএন্ড সার্ভিস চালু আছে কিনা নিশ্চিত করুন।');
      } else {
        setError(err.message || 'লগইন ব্যর্থ হয়েছে');
      }
    }
    finally{setBusy(false)}
  }
  return <section className="section"><div className="container narrow"><div className="auth-card card card-body">
    <span className="eyebrow">ENGINEER PORTAL</span><h1>{mfa?'MFA যাচাই করুন':'সদস্য/অ্যাডমিন লগইন'}</h1>
    <p className="muted">{mfa?'Authenticator app-এর 6-digit code দিন।':'আপনার নিবন্ধিত অ্যাকাউন্ট দিয়ে প্রবেশ করুন।'}</p>
    {error && <div className="notice-error">{error}{error.includes('Email verification')&&<><br/><a className="small" href="/resend-verification">ইমেইল যাচাই লিংক পুনরায় পাঠান</a></>}</div>}
    <form className="form-stack" onSubmit={submit}>
      {!mfa && <><input type="email" required placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}/><input type="password" required placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)}/></>}
      {mfa && <input inputMode="numeric" pattern="\\d{6}" maxLength={6} required placeholder="123456" value={code} onChange={e=>setCode(e.target.value.replace(/\\D/g,''))}/>} 
      <button className="btn btn-primary" disabled={busy}>{busy?'যাচাই হচ্ছে...':mfa?'Verify MFA':'Login'}</button>
    </form>
    {!mfa && <div className="split-head" style={{marginTop:15}}><Link className="small green-text" href="/forgot-password">পাসওয়ার্ড ভুলে গেছেন?</Link><Link className="small" href="/register">নতুন সদস্য নিবন্ধন</Link></div>}
  </div></div></section>
}
