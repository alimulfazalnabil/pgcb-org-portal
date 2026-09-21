'use client';
import { useEffect } from 'react';
export default function ErrorPage({reset}:{error:Error & {digest?:string};reset:()=>void}){useEffect(()=>{console.error(error)},[error]);return <section className="section"><div className="container narrow"><div className="card card-body empty-state"><h1>সাময়িক ত্রুটি</h1><p>এই পৃষ্ঠাটি লোড করা যায়নি।</p><button className="btn btn-primary" onClick={()=>reset()}>আবার চেষ্টা করুন</button></div></div></section>}
