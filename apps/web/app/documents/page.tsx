'use client';

import { useEffect, useState } from 'react';
import { api, DocumentItem } from '../../lib/api';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { Search, Download, FileText, Filter, CheckCircle2 } from 'lucide-react';

const CATEGORIES = [
  { label: 'সকল ডকুমেন্টস', value: '' },
  { label: 'ফরম (Forms)', value: 'FORM' },
  { label: 'নীতিমালা (Policies)', value: 'POLICY' },
  { label: 'বার্ষিক প্রতিবেদন (Reports)', value: 'REPORT' },
  { label: 'ম্যানুয়াল ও নির্দেশিকা', value: 'MANUAL' },
  { label: 'সার্কুলার', value: 'CIRCULAR' },
  { label: 'অন্যান্য', value: 'OTHER' },
];

function formatBytes(bytes?: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('');
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    setLoading(true);
    api.getDocuments({
      category: category || undefined,
      page,
      limit: 15,
    })
      .then((data) => {
        setDocuments(data);
      })
      .catch((err) => {
        console.error('Failed to load documents', err);
        setDocuments([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [category, page]);

  const filteredDocs = documents.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title_bn.toLowerCase().includes(q) ||
      (d.title_en && d.title_en.toLowerCase().includes(q)) ||
      (d.description_bn && d.description_bn.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-10 min-h-screen">
      <div className="border-b border-slate-200 pb-6 mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">প্রাতিষ্ঠানিক ডকুমেন্টস ও ফরম সংগ্রহশালা</h1>
        <p className="text-slate-600 text-sm md:text-base">
          পিজিসিবি প্রকৌশলী সমিতির সদস্য ফরম, কল্যাণ নীতিমালা, বার্ষিক নিরীক্ষা রিপোর্ট ও অফিশিয়াল প্রকাশনাসমূহ ডাউনলোড করুন।
        </p>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-center mb-8">
        <div className="flex flex-wrap gap-2 w-full md:w-auto">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              onClick={() => {
                setCategory(c.value);
                setPage(1);
              }}
              className={`px-3.5 py-1.5 rounded-lg text-xs md:text-sm font-medium transition-all ${
                category === c.value
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-72">
          <Search size={16} className="absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="ডকুমেন্ট খুঁজুন..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>
      </div>

      {/* List */}
      {loading ? (
        <LoadingState message="ডকুমেন্ট তালিকা লোড হচ্ছে..." />
      ) : filteredDocs.length === 0 ? (
        <EmptyState
          icon="📂"
          title="কোনো দলিল পাওয়া যায়নি"
          description="বর্তমানে এই ক্যাটাগরিতে কোনো নথি বা ফরম আপলোড করা হয়নি।"
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-xs">
                  <th className="py-3 px-4">ডকুমেন্টের নাম ও বিবরণ</th>
                  <th className="py-3 px-4">ক্যাটাগরি</th>
                  <th className="py-3 px-4">ভার্সন</th>
                  <th className="py-3 px-4">ফাইল সাইজ</th>
                  <th className="py-3 px-4">ডাউনলোড</th>
                  <th className="py-3 px-4 text-right">অ্যাকশন</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-4">
                      <div className="font-semibold text-slate-900">{doc.title_bn}</div>
                      {doc.title_en && <div className="text-xs text-slate-500 italic">{doc.title_en}</div>}
                      {doc.description_bn && (
                        <div className="text-xs text-slate-600 mt-1 line-clamp-1">{doc.description_bn}</div>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      <span className="bg-emerald-50 text-emerald-700 text-xs font-medium px-2 py-0.5 rounded">
                        {doc.category}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs font-mono text-slate-500">v{doc.version}</td>
                    <td className="py-4 px-4 text-xs text-slate-500">{formatBytes(doc.file_size)}</td>
                    <td className="py-4 px-4 text-xs text-slate-500">
                      {doc.download_count.toLocaleString('bn-BD')} বার
                    </td>
                    <td className="py-4 px-4 text-right">
                      <a
                        href={api.getDocumentDownloadUrl(doc.id)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-md text-xs font-medium transition-colors shadow-sm"
                      >
                        <Download size={13} /> ডাউনলোড
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Pagination */}
      <Pagination
        currentPage={page}
        totalPages={Math.max(1, Math.ceil(filteredDocs.length / 15))}
        onPageChange={(newPage) => setPage(newPage)}
      />
    </div>
  );
}
