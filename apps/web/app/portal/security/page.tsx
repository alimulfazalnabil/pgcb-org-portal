'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
export default function Security(){
 const [sessions,setSessions]=useState<any[]>([]); const [loading,setLoading]=useState(true);
 async function load(){const r=await fetch('/backend/api/v1/auth/sessions'); if(r.ok)setSessions(await r.json()); setLoading(false);}
 useEffect(()=>{load()},[]);
 async function revoke(id:number){const r=await fetch(`/backend/api/v1/auth/sessions/${id}/revoke`,{method:'POST'}); if(r.ok)load(); else alert('Session revoke failed');}
 async function all(){const r=await fetch('/backend/api/v1/auth/logout-all',{method:'POST'}); if(r.ok)window.location.href='/login';}
 return <section className="section"><div className="container narrow-wide"><div className="section-head left"><span className="eyebrow">ACCOUNT SECURITY</span><h1>সেশন ও নিরাপত্তা</h1><p>আপনার সক্রিয় ও পূর্ববর্তী লগইন সেশন পর্যালোচনা করুন।</p></div><div className="card card-body"><div className="split-head"><h2>সেশন তালিকা</h2><button className="btn btn-orange" onClick={all}>সব সেশন লগআউট</button></div>{loading?<p>লোড হচ্ছে...</p>:sessions.map(s=><div className="timeline-item" key={s.id}><strong>Session #{s.id} {s.revoked?'· Revoked':''}</strong><p>Created: {new Date(s.created_at).toLocaleString('en-GB')} · Last seen: {s.last_seen_at?new Date(s.last_seen_at).toLocaleString('en-GB'):'—'} · Expires: {new Date(s.expires_at).toLocaleString('en-GB')}</p>{!s.revoked&&<button className="btn btn-light" onClick={()=>revoke(s.id)}>Revoke</button>}</div>)}<Link className="small" href="/portal">← Portal-এ ফিরে যান</Link></div></div></section>
}
