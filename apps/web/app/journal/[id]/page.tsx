'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';

export default function JournalDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [item, setItem] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/backend/api/v1/public/journals/${id}`)
      .then(async r => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.detail || 'Journal not found');
        setItem(b);
      })
      .catch(e => setError(e.message));
  }, [id]);

  if (error) return <section className="section"><div className="container narrow"><div className="card card-body"><h1>প্রকাশনা পাওয়া যায়নি</h1><p className="muted">{error}</p><Link className="btn btn-primary" href="/journal">জার্নালে ফিরুন</Link></div></div></section>;
  if (!item) return <section className="section"><div className="container">লোড হচ্ছে...</div></section>;

  return <section className="section"><div className="container narrow-wide">
    <Link className="back-link" href="/journal">← সকল প্রকাশনা</Link>
    <article className="card card-body">
      <span className="tag blue">{item.category}</span>
      <h1>{item.title_bn}</h1>
      {item.title_en && <p className="muted">{item.title_en}</p>}
      <div className="detail-grid"><div><small>লেখক</small><strong>{item.author || '—'}</strong></div><div><small>সংস্করণ</small><strong>{item.edition || '—'}</strong></div><div><small>প্রকাশের তারিখ</small><strong>{item.publication_date ? new Date(item.publication_date).toLocaleDateString('bn-BD') : '—'}</strong></div><div><small>বিভাগ</small><strong>{item.category}</strong></div></div>
      <h3>সারাংশ</h3>
      <p style={{lineHeight:2}}>{item.abstract_bn || 'এই প্রকাশনার জন্য সারাংশ দেওয়া হয়নি।'}</p>
      {item.document_url && item.document_url !== '#' ? <a className="btn btn-green" href={item.document_url} target="_blank" rel="noreferrer">⇩ প্রকাশনা / PDF</a> : <span className="status-pill">ডকুমেন্ট সংযুক্ত নেই</span>}
    </article>
  </div></section>;
}
