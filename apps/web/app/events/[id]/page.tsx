'use client';
import Link from 'next/link';
import { use, useEffect, useState } from 'react';

export default function EventDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [event, setEvent] = useState<any>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    fetch(`/backend/api/v1/event/${id}`).then(async r => { const b = await r.json().catch(() => ({})); if (!r.ok) throw new Error(b.detail || 'Event not found'); setEvent(b); }).catch(e => setError(e.message));
  }, [id]);
  if (error) return <section className="section"><div className="container narrow"><div className="card card-body"><h1>ইভেন্ট পাওয়া যায়নি</h1><p className="muted">{error}</p><Link className="btn btn-primary" href="/events">ইভেন্ট তালিকায় ফিরুন</Link></div></div></section>;
  if (!event) return <section className="section"><div className="container">লোড হচ্ছে...</div></section>;
  return <section className="section"><div className="container narrow-wide"><Link className="back-link" href="/events">← সকল ইভেন্ট</Link><article className="card card-body"><span className="tag orange">EVENT</span><h1>{event.title_bn}</h1>{event.title_en && <p className="muted">{event.title_en}</p>}<div className="meta">{event.event_date ? new Date(event.event_date).toLocaleString('bn-BD') : 'তারিখ নির্ধারিত নয়'} · {event.location_bn || 'স্থান নির্ধারিত নয়'}</div><p style={{lineHeight:1.9}}>{event.description_bn || 'এই ইভেন্টের জন্য এখনো বিস্তারিত বিবরণ প্রকাশিত হয়নি।'}</p><div className="detail-grid"><div><small>Capacity</small><strong>{event.capacity || 'Unlimited'}</strong></div><div><small>Registration deadline</small><strong>{event.registration_deadline ? new Date(event.registration_deadline).toLocaleString('bn-BD') : 'Not specified'}</strong></div><div><small>Participation fee</small><strong>{event.fee_amount ? `${event.fee_amount.toLocaleString('bn-BD')} ${event.fee_currency}` : 'Free'}</strong></div><div><small>Registration</small><strong>{event.registration_enabled ? 'Open' : 'Closed'}</strong></div></div>{event.registration_enabled ? <Link className="btn btn-green" href={`/events/${event.id}/register`}>ইভেন্ট নিবন্ধন করুন</Link> : <span className="status-pill">নিবন্ধন বন্ধ</span>}</article></div></section>;
}
