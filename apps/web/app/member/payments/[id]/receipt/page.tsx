'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import {
  Printer,
  Download,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  RefreshCw,
  AlertCircle,
  ExternalLink,
  QrCode,
  Building2,
} from 'lucide-react';
import { MemberLayout } from '@/components/member/MemberLayout';
import { membersApi } from '@/lib/api/members';
import { PaymentReceiptData } from '@/lib/api/types';

export default function MemberPaymentReceiptPage() {
  const params = useParams();
  const router = useRouter();
  const paymentId = Number(params?.id);

  const [lang, setLang] = useState<'en' | 'bn'>('en');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [receipt, setReceipt] = useState<PaymentReceiptData | null>(null);

  const isEn = lang === 'en';

  const loadReceipt = async () => {
    if (!paymentId || isNaN(paymentId)) {
      setError(isEn ? 'Invalid payment ID' : 'অকার্যকর পেমেন্ট আইডি');
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await membersApi.getPaymentReceipt(paymentId);
      setReceipt(data);
    } catch (err: any) {
      setError(
        err?.message ||
          (isEn
            ? 'Official digital receipt not found or not yet generated for this transaction'
            : 'অফিসিয়াল ডিজিটাল রসিদ পাওয়া যায়নি অথবা এখনো ইস্যু করা হয়নি')
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReceipt();
  }, [paymentId]);

  const handlePrint = () => {
    if (typeof window !== 'undefined') {
      window.print();
    }
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return 'N/A';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(isEn ? 'en-US' : 'bn-BD', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <MemberLayout
      title={isEn ? 'Official Payment Receipt' : 'অফিসিয়াল পেমেন্ট রসিদ'}
      lang={lang}
      onLangChange={setLang}
      activeTab="payments"
    >
      <div className="space-y-6 max-w-3xl mx-auto pb-12">
        {/* Top Control Bar (Hidden during print) */}
        <div className="flex items-center justify-between print:hidden">
          <Link
            href={`/member/payments/${paymentId}`}
            className="inline-flex items-center gap-2 text-xs font-semibold text-slate-600 hover:text-primary-600 transition"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>{isEn ? 'Back to Payment Details' : 'পেমেন্ট বিবরণে ফিরুন'}</span>
          </Link>
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrint}
              disabled={loading || !receipt}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-xl shadow-sm transition"
            >
              <Printer className="w-4 h-4 text-slate-600" />
              <span>{isEn ? 'Print Receipt' : 'প্রিন্ট করুন'}</span>
            </button>
            <a
              href={`/api/v1/member/payments/${paymentId}/receipt.pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-xl shadow-sm transition ${
                loading || !receipt ? 'pointer-events-none opacity-50' : ''
              }`}
            >
              <Download className="w-4 h-4" />
              <span>{isEn ? 'Download PDF' : 'পিডিএফ ডাউনলোড'}</span>
            </a>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-16 text-center shadow-sm print:hidden">
            <RefreshCw className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-500">
              {isEn ? 'Generating authentic digital receipt...' : 'ডিজিটাল রসিদ প্রস্তুত হচ্ছে...'}
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 p-6 rounded-2xl flex items-start gap-4 print:hidden">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm">{isEn ? 'Receipt Unavailable' : 'রসিদ পাওয়া যায়নি'}</h3>
              <p className="text-xs mt-1 text-rose-600">{error}</p>
              <Link
                href={`/member/payments/${paymentId}`}
                className="inline-flex items-center gap-1.5 mt-3 text-xs font-semibold text-rose-800 underline"
              >
                <span>{isEn ? 'Return to payment details' : 'পেমেন্ট বিবরণে ফিরুন'}</span>
              </Link>
            </div>
          </div>
        )}

        {/* Official Printable Receipt Document */}
        {receipt && !loading && (
          <div className="bg-white rounded-2xl border border-slate-300 shadow-lg p-8 md:p-12 print:border-none print:shadow-none print:p-0 text-slate-800 print:text-black">
            {/* Institutional Header */}
            <div className="border-b-2 border-slate-800 pb-6 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-primary-700 text-white rounded-xl flex items-center justify-center font-bold text-xl tracking-wider shadow-sm">
                    PGCB
                  </div>
                  <div>
                    <h1 className="text-lg md:text-xl font-bold tracking-tight text-slate-900 uppercase">
                      Power Grid Company of Bangladesh PLC
                    </h1>
                    <h2 className="text-xs font-semibold text-slate-600">
                      পাওয়ার গ্রিড কোম্পানি অব বাংলাদেশ পিএলসি (সদস্য পোর্টাল)
                    </h2>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      IEB Bhaban, Ramna, Dhaka-1000, Bangladesh • www.pgcb.org.bd
                    </p>
                  </div>
                </div>

                <div className="text-right sm:text-right">
                  <span className="inline-block px-3 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-300">
                    ✓ {isEn ? 'Official Receipt' : 'অফিসিয়াল রসিদ'}
                  </span>
                  <div className="font-mono text-xs font-bold text-slate-900 mt-2">
                    {receipt.receipt_no}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {formatDate(receipt.payment_date)}
                  </div>
                </div>
              </div>
            </div>

            {/* Two Column Member & Payment Details */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pb-6 border-b border-slate-200 text-xs">
              {/* Member Details */}
              <div className="space-y-2">
                <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] text-primary-800">
                  {isEn ? 'Billed To (Member Details)' : 'সদস্যের তথ্য'}
                </h3>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-medium">
                    {isEn ? 'Member Name' : 'সদস্যের নাম'}
                  </span>
                  <span className="font-bold text-slate-900 text-sm block">
                    {isEn ? receipt.member_name : receipt.member_name_bn || receipt.member_name}
                  </span>
                </div>
                {receipt.membership_id && (
                  <div>
                    <span className="text-slate-500 block text-[10px] uppercase font-medium">
                      {isEn ? 'Membership ID' : 'সদস্য আইডি'}
                    </span>
                    <span className="font-mono font-semibold text-slate-800 block">
                      {receipt.membership_id}
                    </span>
                  </div>
                )}
              </div>

              {/* Payment Transaction Details */}
              <div className="space-y-2 sm:text-right">
                <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] text-primary-800">
                  {isEn ? 'Payment Information' : 'পেমেন্ট বিবরণ'}
                </h3>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-medium">
                    {isEn ? 'Transaction Reference' : 'লেনদেন রেফারেন্স'}
                  </span>
                  <span className="font-mono font-semibold text-slate-900 block">
                    {receipt.transaction_ref}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase font-medium">
                    {isEn ? 'Payment Gateway / Channel' : 'পেমেন্ট গেটওয়ে'}
                  </span>
                  <span className="font-semibold text-slate-800 block">
                    {receipt.provider} {receipt.provider_tran_id ? `(${receipt.provider_tran_id})` : ''}
                  </span>
                </div>
              </div>
            </div>

            {/* Payment Items Table */}
            <div className="py-6">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b-2 border-slate-800 bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-700">
                    <th className="py-2.5 px-3">{isEn ? 'Description' : 'বিবরণ'}</th>
                    <th className="py-2.5 px-3 text-center">{isEn ? 'Currency' : 'মুদ্রা'}</th>
                    <th className="py-2.5 px-3 text-right">{isEn ? 'Amount' : 'পরিমাণ'}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <tr>
                    <td className="py-4 px-3">
                      <div className="font-bold text-slate-900 text-sm">
                        {isEn ? receipt.purpose_title_en : receipt.purpose_title_bn}
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">
                        {isEn
                          ? 'Official fees credited toward active membership standing.'
                          : 'সদস্যপদ সক্রিয়করণের জন্য জমা করা সরকারি ফি।'}
                      </div>
                    </td>
                    <td className="py-4 px-3 text-center text-slate-600 font-mono">
                      {receipt.currency}
                    </td>
                    <td className="py-4 px-3 text-right font-bold text-slate-900 text-sm">
                      {receipt.amount_formatted}
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-slate-800 text-slate-900 font-bold">
                    <td colSpan={2} className="py-3 px-3 text-right text-xs uppercase tracking-wider">
                      {isEn ? 'Total Amount Paid:' : 'সর্বমোট পরিশোধিত:'}
                    </td>
                    <td className="py-3 px-3 text-right text-base text-primary-800 font-extrabold font-mono">
                      {receipt.amount_formatted}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Bottom Verification Seal & Live QR Code */}
            <div className="mt-6 pt-6 border-t-2 border-dashed border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-6">
              {/* Security Seal text */}
              <div className="space-y-1.5 text-xs max-w-sm">
                <div className="flex items-center gap-1.5 font-bold text-emerald-800 text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span>{isEn ? 'Digitally Verified & Authorized' : 'ডিজিটালি যাচাইকৃত ও অনুমোদিত'}</span>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  {isEn
                    ? 'This is a computer-generated official receipt verified by the PGCB Core Financial Engine. No physical signature is required. Scan the QR code to verify live status.'
                    : 'এটি পিজিসিবি কোর ফাইন্যান্সিয়াল ইঞ্জিন দ্বারা অনুমোদিত একটি কম্পিউটার-জেনারেটেড রসিদ। কোনো স্বাক্ষরের প্রয়োজন নেই। সরাসরি যাচাইয়ের জন্য কিউআর কোড স্ক্যান করুন।'}
                </p>
              </div>

              {/* QR Verification Link Box */}
              <div className="flex items-center gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200 flex-shrink-0">
                <div className="w-16 h-16 bg-white border border-slate-300 rounded-lg flex items-center justify-center text-slate-700 shadow-sm p-1">
                  <QrCode className="w-12 h-12 text-slate-800" />
                </div>
                <div className="text-[10px] space-y-0.5">
                  <span className="font-bold text-slate-800 block uppercase">
                    {isEn ? 'Verify Authenticity' : 'সত্যতা যাচাই করুন'}
                  </span>
                  <Link
                    href={`/verify/payment/${encodeURIComponent(receipt.receipt_no || receipt.transaction_ref)}`}
                    target="_blank"
                    className="text-primary-700 font-mono underline hover:text-primary-800 block truncate max-w-[140px]"
                  >
                    verify/payment/{receipt.receipt_no}
                  </Link>
                  <span className="text-slate-400 block">{isEn ? 'Instant Verification' : 'তাৎক্ষণিক যাচাই'}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MemberLayout>
  );
}
