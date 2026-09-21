'use client';
import Link from 'next/link';
import { useEffect,useState } from 'react';
import { SectionHead } from '@/components/SectionHead';
export default function Circles(){const [circles,setCircles]=useState<any[]>([]);useEffect(()=>{fetch('/backend/api/v1/public/circles').then(r=>r.json()).then(setCircles)},[]);return <section className="section"><div className="container"><SectionHead eyebrow="9 PGCB GRID CIRCLES" title="গ্রিড সার্কেল কমিটি" subtitle="প্রতিটি সার্কেলের কমিটি, সদস্য ও যোগাযোগের তথ্য।"/><div className="grid-3">{circles.map(c=><Link key={c.id} href={`/circles/${encodeURIComponent(c.name_bn)}`} className="card card-body"><div className="kicker blue">PGCB GRID CIRCLE</div><h2>{c.name_bn}</h2><p className="muted">কমিটি দেখুন →</p></Link>)}</div></div></section>}
