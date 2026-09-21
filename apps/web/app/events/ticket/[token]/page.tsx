'use client';
import Link from 'next/link';
import { use, useEffect, useState } from 'react';

export default function TicketPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const [ticket,setTicket]=useState<any>(null);const [error,setError]=useState('');
  useEffect(()=>{fetch(`/backend/api/v1/events/registrations/${encodeURIComponent(token)}`).then(async r=>{const b=await r.json().catch(()=>({}));if(!r.ok)throw new Error(b.detail||'Invalid ticket');setTicket(b)}).catch(e=>setError(e.message));},[token]);
  if(error)return <section className="section"><div className="container narrow"><div className="card card-body"><h1>টিকিট যাচাই ব্যর্থ</h1><p className="muted">{error}</p><Link className="btn btn-primary" href="/events">ইভেন্ট তালিকায় ফিরুন</Link></div></div></section>;
  if(!ticket)return <section className="section"><div className="container">লোড হচ্ছে...</div></section>;
  const qr=`/backend/api/v1/events/registrations/${encodeURIComponent(token)}/qr`;
  return <section className="section"><div className="container narrow"><div className="card card-body" style={{textAlign:'center'}}><span className="tag green">VALID TICKET</span><h1>{ticket.event?.title_bn}</h1><p className="muted">{ticket.event?.event_date?new Date(ticket.event.event_date).toLocaleString('bn-BD'):''} · {ticket.event?.location_bn||''}</p><img className="mfa-qr" style={{margin:'18px auto'}} src={qr} alt="Ticket QR"/><h2>{ticket.name}</h2><p className="muted">Ticket: {ticket.ticket_code}</p><div className="detail-grid" style={{textAlign:'left'}}><div><small>Registration</small><strong>{ticket.registration_status}</strong></div><div><small>Attendance</small><strong>{ticket.attendance_status}</strong></div><div><small>Payment</small><strong>{ticket.payment_status}</strong></div><div><small>Organization</small><strong>{ticket.organization||'—'}</strong></div></div></div></div></section>;
}
