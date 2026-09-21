'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';

export default function VerifyEmail(){
 const [status,setStatus]=useState('যাচাই করা হচ্ছে...'); const [ok,setOk]=useState(false);
 useEffect(()=>{const token=new URLSearchParams(window.location.search).get('token'); if(!token){setStatus('Verification token পাওয়া যায়নি।'); return;} fetch('/backend/api/v1/auth/verify-email',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token})}).then(async r=>{const d=await r.json().catch(()=>({})); if(!r.ok)throw new Error(d.detail||'ইমেইল যাচাই ব্যর্থ হয়েছে'); setOk(true); setStatus(d.message||'ইমেইল সফলভাবে যাচাই হয়েছে।');}).catch(e=>setStatus(e.message||'ইমেইল যাচাই ব্যর্থ হয়েছে'));},[]);
 return <section className="section"><div className="container narrow"><div className="card card-body"><span className="eyebrow">ACCOUNT SECURITY</span><h1>{ok?'ইমেইল যাচাই সম্পন্ন':'ইমেইল যাচাই'}</h1><p className="muted">{status}</p><Link className="btn btn-primary" href="/login">লগইন করুন</Link></div></div></section>
}
