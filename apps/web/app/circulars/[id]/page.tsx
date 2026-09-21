'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';

export default function CircularDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [item, setItem] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/backend/api/v1/public/circulars/${id}`)
      .then(async r => {
        const b = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(b.detail || 'Circular not found');
        setItem(b);
      })
      .catch(e => setError(e.message));
  }, [id]);

  if (error) return <section className="section"><div className="container narrow"><div className="card card-body"><h1>সার্কুলার পাওয়া যায়নি</h1><p className="muted">{error}</p><Link className="btn btn-primary" href="/circulars">সার্কুলারে ফিরুন</Link></div></div></section>;
  if (!item) return <section className="section"><div className="container">লোড হচ্ছে...</div></section>;

  return <section className="section"><div className="container narrow-wide">
    <Link className="back-link" href="/circulars">← সকল সার্কুলার</Link>
    <article className="card card-body">
      <div className="meta-row"><span className="tag blue">{item.category}</span><span className="muted">{item.published_at ? new Date(item.published_at).toLocaleDateString('bn-BD') : ''}</span></div>
      <h1>{item.title_bn}</h1>
      {item.title_en && <p className="muted">{item.title_en}</p>}
      {item.reference_no && <p className="small muted">রেফারেন্স: {item.reference_no}</p>}
      <p style={{lineHeight:2,fontSize:17}}>{item.summary_bn || 'এই সার্কুলারের জন্য বিস্তারিত বিবরণ প্রকাশিত হয়নি।'}</p>
      {item.document_url && item.document_url !== '#' ? <a className="btn btn-green" href={item.document_url} target="_blank" rel="noreferrer">⇩ অফিসিয়াল নথি</a> : <span className="status-pill">নথি সংযুক্ত নেই</span>}
    </article>
  </div></section>;
}
