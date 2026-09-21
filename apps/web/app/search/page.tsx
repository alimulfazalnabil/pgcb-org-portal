'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';

type Result = { type: string; id: number; title_bn: string; summary_bn?: string | null; date?: string | null; href: string };

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Result[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function runSearch(e?: FormEvent, overrideQuery?: string) {
    e?.preventDefault();
    const q = (overrideQuery ?? query).trim();
    if (q.length < 2) { setMessage('কমপক্ষে ২টি অক্ষর দিয়ে খুঁজুন।'); return; }
    setBusy(true); setMessage('');
    try {
      const response = await fetch(`/backend/api/v1/public/search?q=${encodeURIComponent(q)}`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || 'অনুসন্ধান ব্যর্থ হয়েছে।');
      setResults(body.results || []);
      if (!body.results?.length) setMessage('কোনো প্রকাশিত ফলাফল পাওয়া যায়নি।');
    } catch (error: any) {
      setMessage(error.message || 'অনুসন্ধান ব্যর্থ হয়েছে।');
      setResults([]);
    } finally { setBusy(false); }
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const initial = params.get('q') || '';
    if (initial) { setQuery(initial); void runSearch(undefined, initial); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <section className="section">
    <div className="container narrow-wide">
      <div className="section-head left">
        <span className="eyebrow">PUBLIC SEARCH</span>
        <h1>সাইটে অনুসন্ধান</h1>
        <p>প্রকাশিত সার্কুলার, জার্নাল, ইভেন্ট ও মিডিয়া কনটেন্ট এক জায়গা থেকে খুঁজুন।</p>
      </div>
      <form className="search-form" onSubmit={runSearch}>
        <input aria-label="Search" placeholder="কীওয়ার্ড লিখুন..." value={query} onChange={e => setQuery(e.target.value)} />
        <button className="btn btn-primary" disabled={busy}>{busy ? 'খোঁজা হচ্ছে...' : 'অনুসন্ধান'}</button>
      </form>
      {message && <div className="notice-error" style={{marginTop: 18}}>{message}</div>}
      <div className="content-list" style={{marginTop: 22}}>
        {results.map(item => <article className="card card-body search-result" key={`${item.type}-${item.id}`}>
          <div className="meta-row"><span className={`tag ${item.type === 'EVENT' ? 'orange' : item.type === 'JOURNAL' ? 'green' : 'blue'}`}>{item.type}</span><span className="muted">{item.date ? new Date(item.date).toLocaleDateString('bn-BD') : ''}</span></div>
          <h2>{item.title_bn}</h2>
          {item.summary_bn && <p className="muted">{item.summary_bn}</p>}
          <Link className="btn btn-light" href={item.href}>বিস্তারিত দেখুন →</Link>
        </article>)}
      </div>
    </div>
  </section>;
}
